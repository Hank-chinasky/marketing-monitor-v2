from django.contrib import messages
from django.http import FileResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from django.views import View

from core.forms import CreatorMaterialUploadForm
from core.models import CreatorMaterial
from core.services.scope import get_creator_queryset_for_user, is_admin_user
from core.views import CreatorDetailView as BaseCreatorDetailView


class CreatorDetailView(BaseCreatorDetailView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        creator = self.object
        context["materials"] = creator.materials.filter(active=True).select_related("uploaded_by")
        context["material_form"] = kwargs.get("material_form") or CreatorMaterialUploadForm()
        context["can_upload_materials"] = is_admin_user(self.request.user)
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        if request.POST.get("form_name") != "creator-material-upload":
            return HttpResponseForbidden("Unsupported creator detail action.")

        if not is_admin_user(request.user):
            return HttpResponseForbidden("You do not have permission to upload materials.")

        material_form = CreatorMaterialUploadForm(request.POST, request.FILES)
        if material_form.is_valid():
            material = material_form.save(commit=False)
            material.creator = self.object
            material.uploaded_by = request.user
            material.save()
            messages.success(request, "Materiaal geüpload.")
            return redirect("creator-detail", pk=self.object.pk)

        return self.render_to_response(self.get_context_data(material_form=material_form))


class CreatorMaterialDownloadView(View):
    http_method_names = ["get"]

    def get(self, request, creator_pk, material_pk, *args, **kwargs):
        creator = get_object_or_404(
            get_creator_queryset_for_user(request.user),
            pk=creator_pk,
        )
        material = get_object_or_404(
            creator.materials.filter(active=True).select_related("creator", "uploaded_by"),
            pk=material_pk,
        )
        return FileResponse(material.file.open("rb"), as_attachment=False, filename=material.filename)
