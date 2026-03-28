from pathlib import Path

from django.contrib import messages
from django.http import FileResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from django.views import View

from core.forms import CreatorMaterialUploadForm
from core.models import CreatorMaterial
from core.services.scope import (
    get_creator_queryset_for_user,
    get_instagram_workspace_channel_queryset_for_user,
    is_admin_user,
)
from core.views import CreatorDetailView as BaseCreatorDetailView


class CreatorDetailView(BaseCreatorDetailView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        creator = self.object
        context["materials"] = creator.materials.filter(active=True).select_related("uploaded_by")
        context["material_form"] = kwargs.get("material_form") or CreatorMaterialUploadForm()
        context["can_upload_materials"] = is_admin_user(self.request.user)
        context["workspace_channel_ids"] = set(
            get_instagram_workspace_channel_queryset_for_user(self.request.user)
            .filter(creator=creator)
            .values_list("pk", flat=True)
        )
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        if request.POST.get("form_name") != "creator-material-upload":
            return HttpResponseForbidden("Unsupported creator detail action.")

        if not is_admin_user(request.user):
            return HttpResponseForbidden("You do not have permission to upload materials.")

        material_form = CreatorMaterialUploadForm(request.POST, request.FILES)
        if material_form.is_valid():
            uploaded_files = material_form.cleaned_data["file"]
            label = (material_form.cleaned_data.get("label") or "").strip()
            notes = (material_form.cleaned_data.get("notes") or "").strip()

            for uploaded_file in uploaded_files:
                material_label = label
                if label and len(uploaded_files) > 1:
                    material_label = f"{label} — {uploaded_file.name}"

                CreatorMaterial.objects.create(
                    creator=self.object,
                    file=uploaded_file,
                    label=material_label,
                    notes=notes,
                    uploaded_by=request.user,
                )

            upload_count = len(uploaded_files)
            if upload_count == 1:
                messages.success(request, "1 bestand geüpload.")
            else:
                messages.success(request, f"{upload_count} bestanden geüpload.")
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

        if not material.file:
            messages.error(request, "No file is attached to this material.")
            return redirect("creator-detail", pk=creator.pk)

        try:
            file_path = Path(material.file.path)
        except Exception:
            messages.error(request, "The material file path could not be resolved.")
            return redirect("creator-detail", pk=creator.pk)

        if not file_path.exists():
            messages.error(request, "The material file is missing on disk.")
            return redirect("creator-detail", pk=creator.pk)

        return FileResponse(
            file_path.open("rb"),
            as_attachment=False,
            filename=material.filename,
        )