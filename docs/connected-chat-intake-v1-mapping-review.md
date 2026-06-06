# Connected Chat Intake v1 — source mapping review

## Status

Docs-only mapping review. No code, no migration, no deploy.

## Source truth

First confirmed source candidate:

- source system: chatties
- source platform: chatties.nl
- runtime/app type: PHP/custom chatengine
- source database: chatengine_big
- source table: messages
- source message id: messages.message_id
- source site id: messages.web_id
- source site label: slave_sites.domain
- source timestamp: messages.time_sending
- source body field: messages.message
- source participants: messages.from and messages.to

The source table has:

- message_id int(11) PRIMARY auto_increment
- from int(11)
- to int(11)
- message varchar(2000)
- time_sending datetime
- mark varchar(11)
- web_id int(11)

## Source thread identity

Candidate internal source thread id:

source_system + web_id + normalized from/to profile pair

Example shape:

chatties:{web_id}:{min_profile_id}:{max_profile_id}

This avoids separate threads for both directions of the same conversation.

## Source message identity

Candidate source message id:

chatties:messages:{message_id}

This should be used for idempotent import and dedupe.

## Direction mapping to confirm

Need read-only confirmation before code:

- inbound to Mara means real/customer profile -> fake/creator profile
- outbound from Mara/source operator means fake/creator profile -> real/customer profile

Likely signal:

- user_profiles.is_fake = 1 means fake/creator/operator-side profile
- user_profiles.is_fake = 0 means real/customer profile

This must be confirmed before code.

## Creator/channel mapping to confirm

Need read-only confirmation before code:

- which chatties profile_id represents Jessica/Mara
- which web_id/domain should map to the Workboard CreatorChannel
- whether one creator profile can exist on multiple slave_sites
- whether source profile_id is stable across sites
- whether source site is required in the creator-channel mapping

Candidate mapping:

- Workboard CreatorChannel.source_system = chatties
- Workboard CreatorChannel.source_site_id = messages.web_id
- Workboard CreatorChannel.source_profile_id = fake/creator profile_id

## Customer mapping to confirm

Need read-only confirmation before code:

- whether real customer identity should use user_profiles.profile_id
- whether customer display label may use profile_name
- whether email/phone/private fields must be excluded from intake
- whether hidden profiles should be skipped

V1 should not import private profile data beyond what is needed for chat context.

## Import window

V1 should not bulk-import full history.

Preferred first import window:

- recent messages only
- small limit
- one mapped creator/channel
- one source site/domain
- inbound-only first

Historical bulk import is outside V1.

## Visibility

For Mara v1, source/platform may be visible in /chats/.

Candidate display:

- source system: chatties
- source site: slave_sites.domain
- source profile/thread ids only for admin/debug, not operator-facing unless needed

## Not in this review

- no source DB writes
- no credentials
- no message bodies
- no production data dump
- no import code
- no migration
- no reply/send
- no connectorboard
- no source masking toggle
- no Fansly/OnlyFans/ManyVids
- no deploy

## Acceptance before code

Code may only start after Architect + Stack Guardian approve:

- source thread id strategy
- source message id strategy
- direction mapping
- creator/channel mapping
- customer mapping
- import window
- no private-data overreach
- migration need or no-migration proof
- read-only source access plan
- tests
