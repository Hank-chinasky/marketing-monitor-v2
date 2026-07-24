import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from core.models import ConversationMessage, ConversationThread, Creator, CreatorChannel
from core.services.eurotikken_identity import (
    build_eurotikken_message_source_id,
    build_eurotikken_thread_source_id,
)

SCHEMA_V1 = "eurotikken-thread-export-v1"
SCHEMA_V2 = "eurotikken-thread-export-v2"
SUPPORTED_SCHEMAS = {SCHEMA_V1, SCHEMA_V2}
SOURCE = ConversationThread.SourceSystem.EUROTIKKEN
SOURCE_TZ = "Europe/Amsterdam"
MAX_MESSAGES = 50


def _num(value, name):
    value = "" if value is None else str(value).strip()
    if not value.isdigit():
        raise CommandError(f"{name} must be numeric.")
    return str(int(value))


def _label(value, name):
    if not isinstance(value, str) or not value.strip():
        raise CommandError(f"{name} must be a non-empty string.")
    normalized = value.strip()
    if len(normalized) > 160:
        raise CommandError(f"{name} may not exceed 160 characters.")
    return normalized


def _source_time(value, name):
    if not isinstance(value, str) or not value.strip():
        raise CommandError(f"{name} must be a non-empty ISO timestamp.")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise CommandError(f"{name} is not a valid ISO timestamp.") from exc
    if timezone.is_aware(parsed):
        raise CommandError(f"{name} must be naive Amsterdam source time.")
    return timezone.make_aware(parsed, ZoneInfo(SOURCE_TZ))


class Command(BaseCommand):
    help = (
        "Import one reviewed Eurotikken JSON export. "
        "Dry-run is the default; pass --apply to write."
    )

    def add_arguments(self, parser):
        parser.add_argument("--input", required=True)
        parser.add_argument("--creator-id", required=True, type=int)
        parser.add_argument("--channel-id", required=True, type=int)
        parser.add_argument("--site-id", required=True)
        parser.add_argument("--profile-id", required=True)
        parser.add_argument("--customer-id", required=True)
        parser.add_argument("--limit", type=int, default=MAX_MESSAGES)
        parser.add_argument("--apply", action="store_true")

    def handle(self, *args, **options):
        limit = options["limit"]
        if not 1 <= limit <= MAX_MESSAGES:
            raise CommandError("--limit must be between 1 and 50.")

        creator = Creator.objects.filter(pk=options["creator_id"]).first()
        if not creator:
            raise CommandError(f"Creator {options['creator_id']} does not exist.")
        if creator.status != Creator.Status.ACTIVE:
            raise CommandError("Creator must be active.")
        if creator.consent_status != Creator.ConsentStatus.ACTIVE:
            raise CommandError("Creator must have active consent.")

        channel = CreatorChannel.objects.filter(pk=options["channel_id"]).first()
        if not channel:
            raise CommandError(f"CreatorChannel {options['channel_id']} does not exist.")
        if channel.creator_id != creator.id:
            raise CommandError("CreatorChannel does not belong to Creator.")
        if channel.status != CreatorChannel.Status.ACTIVE:
            raise CommandError("CreatorChannel must be active.")

        path = Path(options["input"]).expanduser()
        if not path.is_file():
            raise CommandError(f"Input file does not exist: {path}")
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise CommandError(f"Invalid UTF-8 JSON: {exc}") from exc
        if not isinstance(payload, dict):
            raise CommandError("Top-level JSON value must be an object.")

        site_id = _num(options["site_id"], "site_id")
        profile_id = _num(options["profile_id"], "profile_id")
        customer_id = _num(options["customer_id"], "customer_id")
        thread_id = build_eurotikken_thread_source_id(
            site_id,
            profile_id,
            customer_id,
        )

        schema_version = payload.get("schema_version")
        if schema_version not in SUPPORTED_SCHEMAS:
            raise CommandError(
                "schema_version mismatch: expected one of {!r}, received {!r}.".format(
                    sorted(SUPPORTED_SCHEMAS),
                    schema_version,
                )
            )

        expected = {
            "source_system": SOURCE,
            "source_site_id": site_id,
            "source_profile_id": profile_id,
            "source_customer_id": customer_id,
            "source_timezone": SOURCE_TZ,
            "source_thread_id": thread_id,
        }
        for field, expected_value in expected.items():
            if payload.get(field) != expected_value:
                raise CommandError(
                    f"{field} mismatch: expected {expected_value!r}, "
                    f"received {payload.get(field)!r}."
                )

        site_label = _label(
            payload.get("source_site_label"),
            "source_site_label",
        )

        if schema_version == SCHEMA_V2:
            source_profile_label = _label(
                payload.get("source_profile_label"),
                "source_profile_label",
            )
            source_profile_username = _label(
                payload.get("source_profile_username"),
                "source_profile_username",
            )
            source_customer_label = _label(
                payload.get("source_customer_label"),
                "source_customer_label",
            )
            source_customer_username = _label(
                payload.get("source_customer_username"),
                "source_customer_username",
            )
        else:
            source_profile_label = creator.display_name.strip()
            source_profile_username = ""
            source_customer_label = f"Eurotikken customer {customer_id}"
            source_customer_username = ""

        raw_messages = payload.get("messages")
        if not isinstance(raw_messages, list) or not raw_messages:
            raise CommandError("messages must be a non-empty list.")
        if len(raw_messages) > limit or len(raw_messages) > MAX_MESSAGES:
            raise CommandError(
                f"Payload contains {len(raw_messages)} messages; limit is {limit}."
            )

        normalized = []
        seen = set()
        allowed = {profile_id, customer_id}

        for index, raw in enumerate(raw_messages, start=1):
            if not isinstance(raw, dict):
                raise CommandError(f"messages[{index}] must be an object.")

            raw_message_id = _num(
                raw.get("source_message_id"),
                f"messages[{index}].source_message_id",
            )
            message_id = build_eurotikken_message_source_id(raw_message_id)
            if message_id in seen:
                raise CommandError(f"Duplicate source_message_id: {message_id}")
            seen.add(message_id)

            sender_id = _num(
                raw.get("source_sender_id"),
                f"messages[{index}].source_sender_id",
            )
            recipient_id = _num(
                raw.get("source_recipient_id"),
                f"messages[{index}].source_recipient_id",
            )
            if {sender_id, recipient_id} != allowed:
                raise CommandError(
                    f"messages[{index}] participants do not match the bounded thread."
                )

            body = raw.get("body")
            if not isinstance(body, str):
                raise CommandError(f"messages[{index}].body must be a string.")

            direction = (
                ConversationMessage.Direction.INBOUND
                if sender_id == customer_id
                else ConversationMessage.Direction.OUTBOUND
            )
            normalized.append(
                {
                    "raw_id": int(raw_message_id),
                    "message_id": message_id,
                    "sender_id": sender_id,
                    "recipient_id": recipient_id,
                    "direction": direction,
                    "occurred_at": _source_time(
                        raw.get("occurred_at"),
                        f"messages[{index}].occurred_at",
                    ),
                    "body": body,
                }
            )

        normalized.sort(key=lambda item: (item["occurred_at"], item["raw_id"]))
        latest = normalized[-1]
        target_status = (
            ConversationThread.Status.WAITING_ON_OPERATOR
            if latest["direction"] == ConversationMessage.Direction.INBOUND
            else ConversationThread.Status.WAITING_ON_CUSTOMER
        )
        participant_a, participant_b = sorted(
            [profile_id, customer_id],
            key=int,
        )

        thread = ConversationThread.objects.filter(
            source_system=SOURCE,
            source_thread_id=thread_id,
        ).first()

        if thread and schema_version == SCHEMA_V1:
            source_profile_label = (
                thread.source_profile_label or source_profile_label
            )
            source_profile_username = thread.source_profile_username
            source_customer_label = (
                thread.source_customer_label or source_customer_label
            )
            source_customer_username = thread.source_customer_username

        if thread:
            expected_thread = {
                "creator_id": creator.id,
                "channel_id": channel.id,
                "source_site_id": site_id,
                "source_site_label": site_label,
                "source_participant_a_id": participant_a,
                "source_participant_b_id": participant_b,
            }
            mismatches = [
                field
                for field, value in expected_thread.items()
                if getattr(thread, field) != value
            ]
            if mismatches:
                raise CommandError(
                    "Existing thread identity conflict: " + ", ".join(mismatches)
                )

        message_ids = [item["message_id"] for item in normalized]
        conflicts = ConversationMessage.objects.filter(
            source_system=SOURCE,
            source_message_id__in=message_ids,
        )
        if thread:
            conflicts = conflicts.exclude(thread=thread)
        if conflicts.exists():
            raise CommandError(
                "A source message identity already belongs to another thread."
            )

        existing_ids = set()
        if thread:
            existing_ids = set(
                ConversationMessage.objects.filter(
                    thread=thread,
                    source_system=SOURCE,
                    source_message_id__in=message_ids,
                ).values_list("source_message_id", flat=True)
            )
        pending = [item for item in normalized if item["message_id"] not in existing_ids]

        desired_thread_identity = {
            "source_profile_label": source_profile_label,
            "source_profile_username": source_profile_username,
            "source_customer_label": source_customer_label,
            "source_customer_username": source_customer_username,
        }
        thread_identity_changes = {}
        would_update_message_labels = 0

        if thread:
            thread_identity_changes = {
                field: value
                for field, value in desired_thread_identity.items()
                if getattr(thread, field) != value
            }
            would_update_message_labels += (
                ConversationMessage.objects.filter(
                    thread=thread,
                    source_system=SOURCE,
                    source_sender_id=profile_id,
                )
                .exclude(sender_label=source_profile_label)
                .count()
            )
            would_update_message_labels += (
                ConversationMessage.objects.filter(
                    thread=thread,
                    source_system=SOURCE,
                    source_sender_id=customer_id,
                )
                .exclude(sender_label=source_customer_label)
                .count()
            )

        if not options["apply"]:
            self.stdout.write("DRY RUN — no database changes.")
            self.stdout.write(f"source_thread_id={thread_id}")
            self.stdout.write(f"payload_messages={len(normalized)}")
            self.stdout.write(f"existing_messages={len(existing_ids)}")
            self.stdout.write(f"would_create_messages={len(pending)}")
            self.stdout.write(
                f"would_update_thread_identity={bool(thread_identity_changes)}"
            )
            self.stdout.write(
                f"would_update_message_labels={would_update_message_labels}"
            )
            self.stdout.write(f"target_status={target_status}")
            return

        with transaction.atomic():
            thread, thread_created = ConversationThread.objects.get_or_create(
                source_system=SOURCE,
                source_thread_id=thread_id,
                defaults={
                    "creator": creator,
                    "channel": channel,
                    "source_site_id": site_id,
                    "source_site_label": site_label,
                    "source_participant_a_id": participant_a,
                    "source_participant_b_id": participant_b,
                    "source_profile_label": source_profile_label,
                    "source_profile_username": source_profile_username,
                    "source_customer_label": source_customer_label,
                    "source_customer_username": source_customer_username,
                    "status": target_status,
                    "last_message_at": latest["occurred_at"],
                    "active": True,
                },
            )

            thread_identity_update_fields = []
            if not thread_created:
                for field, value in desired_thread_identity.items():
                    if getattr(thread, field) != value:
                        setattr(thread, field, value)
                        thread_identity_update_fields.append(field)

                if thread_identity_update_fields:
                    thread.save(
                        update_fields=thread_identity_update_fields + ["updated_at"]
                    )

            message_labels_updated = 0
            message_labels_updated += (
                ConversationMessage.objects.filter(
                    thread=thread,
                    source_system=SOURCE,
                    source_sender_id=profile_id,
                )
                .exclude(sender_label=source_profile_label)
                .update(sender_label=source_profile_label)
            )
            message_labels_updated += (
                ConversationMessage.objects.filter(
                    thread=thread,
                    source_system=SOURCE,
                    source_sender_id=customer_id,
                )
                .exclude(sender_label=source_customer_label)
                .update(sender_label=source_customer_label)
            )

            existing_ids = set(
                ConversationMessage.objects.filter(
                    thread=thread,
                    source_system=SOURCE,
                    source_message_id__in=message_ids,
                ).values_list("source_message_id", flat=True)
            )
            to_create = [
                ConversationMessage(
                    thread=thread,
                    direction=item["direction"],
                    sender_label=(
                        source_profile_label
                        if item["sender_id"] == profile_id
                        else source_customer_label
                    ),
                    source_message_id=item["message_id"],
                    source_system=SOURCE,
                    source_site_id=site_id,
                    source_thread_id=thread_id,
                    source_sender_id=item["sender_id"],
                    source_recipient_id=item["recipient_id"],
                    body=item["body"],
                    occurred_at=item["occurred_at"],
                )
                for item in normalized
                if item["message_id"] not in existing_ids
            ]
            ConversationMessage.objects.bulk_create(to_create)

            if thread.last_message_at is None or latest["occurred_at"] >= thread.last_message_at:
                thread.last_message_at = latest["occurred_at"]
                thread.status = target_status
                thread.save(update_fields=["last_message_at", "status", "updated_at"])

        self.stdout.write(
            self.style.SUCCESS(
                "Applied Eurotikken import: "
                f"thread_created={thread_created} "
                f"messages_created={len(to_create)} "
                f"messages_skipped={len(normalized) - len(to_create)} "
                f"thread_identity_updated={bool(thread_identity_update_fields)} "
                f"message_labels_updated={message_labels_updated}"
            )
        )
