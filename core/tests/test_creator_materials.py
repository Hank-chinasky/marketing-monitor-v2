from datetime import timedelta
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from core.forms import CreatorMaterialUploadForm
from core.models import Creator, CreatorMaterial, Operator, OperatorAssignment


class CreatorMaterialTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.admin = User.objects.create_user(
            username="admin-materials",
            password="x",
            is_active=True,
            is_staff=True,
        )
        self.operator_user = User.objects.create_user(
            username="operator-materials",
            password="x",
            is_active=True,
        )
        self.operator = Operator.objects.create(user=self.operator_user)
        self.creator = Creator.objects.create(
            display_name="Creator Materials",
            legal_name="Creator Materials BV",
            status="active",
            consent_status="active",
        )
        OperatorAssignment.objects.create(
            operator=self.operator,
            creator=self.creator,
            scope="full_management",
            starts_at=timezone.now() - timedelta(days=1),
            ends_at=None,
            active=True,
        )

    def test_material_media_kind_helpers_detect_image_video_and_other(self):
        image = CreatorMaterial.objects.create(
            creator=self.creator,
            uploaded_by=self.admin,
            file=SimpleUploadedFile("preview.jpg", b"image-bytes", content_type="image/jpeg"),
        )
        video = CreatorMaterial.objects.create(
            creator=self.creator,
            uploaded_by=self.admin,
            file=SimpleUploadedFile("clip.mp4", b"video-bytes", content_type="video/mp4"),
        )
        other = CreatorMaterial.objects.create(
            creator=self.creator,
            uploaded_by=self.admin,
            file=SimpleUploadedFile("briefing.pdf", b"pdf-bytes", content_type="application/pdf"),
        )

        self.assertTrue(image.is_image)
        self.assertFalse(image.is_video)
        self.assertTrue(image.is_previewable)
        self.assertEqual(image.media_kind, "image")

        self.assertTrue(video.is_video)
        self.assertFalse(video.is_image)
        self.assertTrue(video.is_previewable)
        self.assertEqual(video.media_kind, "video")

        self.assertFalse(other.is_previewable)
        self.assertEqual(other.media_kind, "other")
        self.assertEqual(other.extension, "pdf")

    def test_scoped_operator_sees_preview_links_without_open_file_action(self):
        image = CreatorMaterial.objects.create(
            creator=self.creator,
            uploaded_by=self.admin,
            label="Image one",
            file=SimpleUploadedFile("preview.jpg", b"image-bytes", content_type="image/jpeg"),
        )
        video = CreatorMaterial.objects.create(
            creator=self.creator,
            uploaded_by=self.admin,
            label="Video one",
            file=SimpleUploadedFile("clip.mp4", b"video-bytes", content_type="video/mp4"),
        )

        self.client.force_login(self.operator_user)
        response = self.client.get(reverse("creator-detail", kwargs={"pk": self.creator.pk}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            reverse("creator-material-preview", kwargs={"creator_pk": self.creator.pk, "material_pk": image.pk}),
        )
        self.assertContains(
            response,
            reverse("creator-material-preview", kwargs={"creator_pk": self.creator.pk, "material_pk": video.pk}),
        )
        self.assertNotContains(response, "creator-material-modal")
        self.assertNotContains(response, "creator-material-preview-trigger")
        self.assertNotContains(response, "Open bestand")
        self.assertNotContains(
            response,
            reverse("creator-material-delete", kwargs={"creator_pk": self.creator.pk, "material_pk": image.pk}),
        )

    def test_allowed_user_can_open_material_preview_page(self):
        image = CreatorMaterial.objects.create(
            creator=self.creator,
            uploaded_by=self.admin,
            label="Image one",
            file=SimpleUploadedFile("preview.jpg", b"image-bytes", content_type="image/jpeg"),
        )

        self.client.force_login(self.operator_user)
        response = self.client.get(
            reverse("creator-material-preview", kwargs={"creator_pk": self.creator.pk, "material_pk": image.pk})
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "creators/material_preview.html")
        self.assertContains(response, "Terug naar materialen")
        self.assertContains(
            response,
            reverse("creator-material-download", kwargs={"creator_pk": self.creator.pk, "material_pk": image.pk}),
        )

    def test_admin_sees_delete_action_on_creator_detail(self):
        material = CreatorMaterial.objects.create(
            creator=self.creator,
            uploaded_by=self.admin,
            label="Image one",
            file=SimpleUploadedFile("preview.jpg", b"image-bytes", content_type="image/jpeg"),
        )

        self.client.force_login(self.admin)
        response = self.client.get(reverse("creator-detail", kwargs={"pk": self.creator.pk}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            reverse("creator-material-delete", kwargs={"creator_pk": self.creator.pk, "material_pk": material.pk}),
        )
        self.assertContains(response, "Verwijder")
        self.assertContains(response, "Bekijk groter")
        self.assertNotContains(response, "Open bestand")

    def test_upload_form_accepts_multiple_files(self):
        form = CreatorMaterialUploadForm(
            data={"label": "Shoot", "notes": "Latest set"},
            files={
                "file": [
                    SimpleUploadedFile("one.jpg", b"one", content_type="image/jpeg"),
                    SimpleUploadedFile("two.jpg", b"two", content_type="image/jpeg"),
                ]
            },
        )
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(len(form.cleaned_data["file"]), 2)

    def test_admin_can_upload_multiple_materials_in_one_submit(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("creator-detail", kwargs={"pk": self.creator.pk}),
            {
                "form_name": "creator-material-upload",
                "label": "Shoot",
                "notes": "Latest set",
                "file": [
                    SimpleUploadedFile("one.jpg", b"one", content_type="image/jpeg"),
                    SimpleUploadedFile("two.jpg", b"two", content_type="image/jpeg"),
                ],
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            f"{reverse('creator-detail', kwargs={'pk': self.creator.pk})}#creator-materials",
        )
        self.assertEqual(self.creator.materials.count(), 2)
        labels = set(self.creator.materials.values_list("label", flat=True))
        self.assertEqual(labels, {"Shoot — one.jpg", "Shoot — two.jpg"})
        self.assertEqual(set(self.creator.materials.values_list("notes", flat=True)), {"Latest set"})

    def test_admin_can_delete_material(self):
        material = CreatorMaterial.objects.create(
            creator=self.creator,
            uploaded_by=self.admin,
            label="Delete me",
            file=SimpleUploadedFile("delete-me.jpg", b"image-bytes", content_type="image/jpeg"),
        )
        file_path = Path(material.file.path)
        self.assertTrue(file_path.exists())

        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("creator-material-delete", kwargs={"creator_pk": self.creator.pk, "material_pk": material.pk}),
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            f"{reverse('creator-detail', kwargs={'pk': self.creator.pk})}#creator-materials",
        )

        material.refresh_from_db()
        self.assertFalse(material.active)
        self.assertFalse(file_path.exists())
        self.assertEqual(self.creator.materials.filter(active=True).count(), 0)

    def test_operator_cannot_delete_material(self):
        material = CreatorMaterial.objects.create(
            creator=self.creator,
            uploaded_by=self.admin,
            label="Do not delete",
            file=SimpleUploadedFile("do-not-delete.jpg", b"image-bytes", content_type="image/jpeg"),
        )
        file_path = Path(material.file.path)
        self.assertTrue(file_path.exists())

        self.client.force_login(self.operator_user)
        response = self.client.post(
            reverse("creator-material-delete", kwargs={"creator_pk": self.creator.pk, "material_pk": material.pk}),
        )

        self.assertEqual(response.status_code, 403)

        material.refresh_from_db()
        self.assertTrue(material.active)
        self.assertTrue(file_path.exists())