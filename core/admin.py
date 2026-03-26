from django.contrib import admin

from core.models import Creator, CreatorChannel, CreatorMaterial, Operator, OperatorAssignment


@admin.register(Operator)
class OperatorAdmin(admin.ModelAdmin):
    list_display = ("id", "user")
    search_fields = ("user__username", "user__email", "user__first_name", "user__last_name")


@admin.register(Creator)
class CreatorAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "display_name",
        "status",
        "consent_status",
        "primary_operator",
        "content_source_type",
        "content_ready_status",
    )
    search_fields = (
        "display_name",
        "legal_name",
        "notes",
        "content_source_url",
        "content_source_notes",
    )


@admin.register(CreatorMaterial)
class CreatorMaterialAdmin(admin.ModelAdmin):
    list_display = ("id", "creator", "label", "uploaded_by", "uploaded_at", "active")
    list_filter = ("active", "uploaded_at")
    search_fields = (
        "creator__display_name",
        "label",
        "notes",
        "file",
        "uploaded_by__username",
        "uploaded_by__email",
    )
    autocomplete_fields = ("creator", "uploaded_by")


@admin.register(CreatorChannel)
class CreatorChannelAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "creator",
        "platform",
        "handle",
        "status",
        "access_mode",
        "recovery_owner",
        "credential_status",
        "two_factor_enabled",
        "vpn_required",
        "approved_ip_label",
    )
    search_fields = (
        "handle",
        "creator__display_name",
        "login_identifier",
        "access_notes",
        "approved_egress_ip",
        "approved_ip_label",
        "approved_access_region",
        "access_profile_notes",
        "last_operator_update",
    )


@admin.register(OperatorAssignment)
class OperatorAssignmentAdmin(admin.ModelAdmin):
    list_display = ("id", "operator", "creator", "scope", "starts_at", "ends_at", "active")
    search_fields = ("creator__display_name", "operator__user__username")
