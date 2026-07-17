from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from core.models import (
    ConversationMessage,
    ConversationThread,
    Creator,
    CreatorChannel,
    Operator,
    OperatorAssignment,
    ThreadFollowUpStatus,
)


DEMO_MARKER = "buddy-demo-scenarios-v1"
DEMO_CREATOR_NAME = "[DEMO] Luna Vale"
DEMO_CHANNEL_HANDLE = "buddy-demo-luna"


class Command(BaseCommand):
    help = (
        "Create or remove three fictitious Buddy demo scenarios. "
        "No live source data or credentials are used."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--username",
            help=(
                "Username of the existing operator who may access the demo creator. "
                "Optional when exactly one Operator exists."
            ),
        )
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Remove Buddy demo scenarios v1 and exit.",
        )

    def handle(self, *args, **options):
        if options["reset"]:
            self._remove_existing_demo()
            self.stdout.write(
                self.style.SUCCESS("Buddy demo scenarios v1 removed.")
            )
            return

        operator = self._resolve_operator(options.get("username"))

        with transaction.atomic():
            self._remove_existing_demo(write_output=False)
            creator, threads = self._create_demo(operator)

        self.stdout.write(
            self.style.SUCCESS(
                f"Buddy demo scenarios v1 created for operator "
                f"{operator.user.username}: {len(threads)} threads."
            )
        )
        for thread in threads:
            self.stdout.write(
                f"- {thread.source_thread_id} "
                f"({thread.get_source_system_display()})"
            )

    def _resolve_operator(self, username):
        if username:
            user = get_user_model().objects.filter(username=username).first()
            if not user:
                raise CommandError(
                    f"User '{username}' does not exist."
                )

            operator = Operator.objects.filter(user=user).first()
            if not operator:
                raise CommandError(
                    f"User '{username}' has no Operator profile."
                )
            return operator

        operators = list(
            Operator.objects.select_related("user").order_by("id")
        )

        if len(operators) == 1:
            return operators[0]

        if not operators:
            raise CommandError(
                "No Operator profiles exist. Supply an existing operator first."
            )

        usernames = ", ".join(
            operator.user.username for operator in operators
        )
        raise CommandError(
            "Multiple operators exist. Run again with --username. "
            f"Available operators: {usernames}"
        )

    def _remove_existing_demo(self, *, write_output=True):
        demo_creators = Creator.objects.filter(
            display_name=DEMO_CREATOR_NAME,
            notes=DEMO_MARKER,
        )
        creator_count = demo_creators.count()
        demo_creators.delete()

        if write_output:
            self.stdout.write(
                f"Removed {creator_count} matching demo creator(s)."
            )

    def _create_demo(self, operator):
        now = timezone.now()

        creator = Creator.objects.create(
            display_name=DEMO_CREATOR_NAME,
            legal_name="",
            status=Creator.Status.ACTIVE,
            consent_status=Creator.ConsentStatus.ACTIVE,
            customer_stage=Creator.CustomerStage.INSIDE_PAYWALL,
            primary_operator=operator,
            notes=DEMO_MARKER,
            primary_link="",
        )

        channel = CreatorChannel.objects.create(
            creator=creator,
            platform=CreatorChannel.Platform.OTHER,
            handle=DEMO_CHANNEL_HANDLE,
            profile_url="https://example.com/demo/buddy-luna",
            status=CreatorChannel.Status.ACTIVE,
            access_mode=CreatorChannel.AccessMode.DRAFT_ONLY,
            recovery_owner=CreatorChannel.RecoveryOwner.AGENCY,
            credential_status=CreatorChannel.CredentialStatus.KNOWN,
            access_notes=(
                "Fictief demo-account. Geen echte login of bronkoppeling."
            ),
            access_profile_notes=(
                "Demo-only accountcontext; geen credentials opgeslagen."
            ),
            two_factor_enabled=True,
        )

        OperatorAssignment.objects.create(
            operator=operator,
            creator=creator,
            scope=OperatorAssignment.Scope.FULL_MANAGEMENT,
            starts_at=now - timedelta(days=1),
            active=True,
        )

        warm_thread = ConversationThread.objects.create(
            creator=creator,
            channel=channel,
            source_system=ConversationThread.SourceSystem.CHATTIES,
            source_thread_id="DEMO-01-WARME-FOLLOW-UP",
            source_site_id="demo-legacy-a",
            source_site_label="Fictieve legacychat A",
            source_participant_a_id="demo-profile-luna",
            source_participant_b_id="demo-customer-kai",
            status=ConversationThread.Status.WAITING_ON_OPERATOR,
            last_message_at=now - timedelta(minutes=5),
            last_operator_handoff_at=now - timedelta(hours=2),
            thread_summary=(
                "Kai reageert goed op lichte humor en persoonlijke details. "
                "De conversatie loopt al meerdere dagen en voelt wederzijds."
            ),
            open_loop=(
                "Reageer op zijn vraag over vanavond en pak de eerdere "
                "grap over zijn late koffiemoment terug."
            ),
            guardrails=(
                "Geen beschikbaarheid beloven die niet bevestigd is. "
                "Niet direct verkopen; eerst de persoonlijke lijn voortzetten."
            ),
            risk_flags="",
            last_handoff_note=(
                "Warme lijn. Hij kwam zelf terug op de eerdere grap. "
                "Niet opnieuw voorstellen en de conversatie niet resetten."
            ),
            last_approved_reply_style=(
                "Warm, speels en persoonlijk; korte natuurlijke zinnen "
                "zonder overdreven enthousiasme."
            ),
        )

        ThreadFollowUpStatus.objects.create(
            thread=warm_thread,
            status=ThreadFollowUpStatus.Status.WARM,
            note="Warme persoonlijke lijn gecontroleerd voortzetten.",
            created_by=operator.user,
            updated_by=operator.user,
        )

        self._create_messages(
            warm_thread,
            [
                (
                    ConversationMessage.Direction.OUTBOUND,
                    "Luna",
                    "Jij en die koffie om middernacht blijven een vreemde combinatie.",
                    now - timedelta(hours=20),
                ),
                (
                    ConversationMessage.Direction.INBOUND,
                    "Kai",
                    "Maar je moest er wel om lachen, geef maar toe.",
                    now - timedelta(hours=19, minutes=52),
                ),
                (
                    ConversationMessage.Direction.OUTBOUND,
                    "Luna",
                    "Een klein beetje. Dat betekent nog niet dat het een goed idee was.",
                    now - timedelta(hours=19, minutes=48),
                ),
                (
                    ConversationMessage.Direction.INBOUND,
                    "Kai",
                    "Ik moest vandaag weer aan je denken. Ben je vanavond nog even online?",
                    now - timedelta(minutes=5),
                ),
            ],
        )

        review_thread = ConversationThread.objects.create(
            creator=creator,
            channel=channel,
            source_system=ConversationThread.SourceSystem.MARA_CHAT,
            source_thread_id="DEMO-02-REVIEW-NODIG",
            source_site_id="demo-source-b",
            source_site_label="Fictieve chatsource B",
            source_participant_a_id="demo-profile-luna",
            source_participant_b_id="demo-customer-milo",
            status=ConversationThread.Status.HANDOFF_REQUIRED,
            last_message_at=now - timedelta(minutes=20),
            last_operator_handoff_at=now - timedelta(hours=1),
            thread_summary=(
                "Milo vraagt om een concrete toezegging, maar de broncontext "
                "en eerdere afspraak spreken elkaar tegen."
            ),
            open_loop=(
                "Controleer eerst de eerdere afspraak en bevestig wat werkelijk "
                "kan worden toegezegd."
            ),
            guardrails=(
                "Geen datum, prijs of beschikbaarheid bevestigen zonder "
                "handmatige broncontrole."
            ),
            risk_flags=(
                "Tegenstrijdige broncontext: eerdere afspraak is niet bevestigd."
            ),
            last_handoff_note=(
                "Niet antwoorden voordat een operator de eerdere afspraak "
                "in de bronomgeving heeft gecontroleerd."
            ),
            last_approved_reply_style=(
                "Rustig, duidelijk en niet-defensief; geen ongeverifieerde beloftes."
            ),
        )

        ThreadFollowUpStatus.objects.create(
            thread=review_thread,
            status=ThreadFollowUpStatus.Status.REVIEW_NODIG,
            note="Eerdere afspraak en broncontext eerst controleren.",
            created_by=operator.user,
            updated_by=operator.user,
        )

        self._create_messages(
            review_thread,
            [
                (
                    ConversationMessage.Direction.INBOUND,
                    "Milo",
                    "Je zei toch dat dit morgen geregeld zou zijn?",
                    now - timedelta(minutes=28),
                ),
                (
                    ConversationMessage.Direction.INTERNAL_NOTE,
                    "Demo-import",
                    "De genoemde afspraak is niet teruggevonden in de gecontroleerde context.",
                    now - timedelta(minutes=24),
                ),
                (
                    ConversationMessage.Direction.INBOUND,
                    "Milo",
                    "Kun je het nu gewoon bevestigen?",
                    now - timedelta(minutes=20),
                ),
            ],
        )

        incomplete_thread = ConversationThread.objects.create(
            creator=creator,
            channel=None,
            source_system=ConversationThread.SourceSystem.CHATTIES,
            source_thread_id="DEMO-03-CONTEXT-ONTBREEKT",
            source_site_id="demo-unmapped-source",
            source_site_label="Onvolledige fictieve import",
            source_participant_a_id="",
            source_participant_b_id="demo-customer-noah",
            status=ConversationThread.Status.WAITING_ON_OPERATOR,
            last_message_at=now - timedelta(minutes=40),
            thread_summary="",
            open_loop="",
            guardrails="",
            risk_flags="",
            last_handoff_note="",
            last_approved_reply_style="",
        )

        self._create_messages(
            incomplete_thread,
            [
                (
                    ConversationMessage.Direction.INBOUND,
                    "Noah",
                    "Hoi, ken je me nog?",
                    now - timedelta(minutes=40),
                ),
            ],
        )

        return creator, [
            warm_thread,
            review_thread,
            incomplete_thread,
        ]

    def _create_messages(self, thread, messages):
        ConversationMessage.objects.bulk_create(
            [
                ConversationMessage(
                    thread=thread,
                    direction=direction,
                    sender_label=sender_label,
                    source_system=thread.source_system,
                    source_site_id=thread.source_site_id,
                    source_thread_id=thread.source_thread_id,
                    body=body,
                    occurred_at=occurred_at,
                )
                for direction, sender_label, body, occurred_at in messages
            ]
        )
