from dataclasses import dataclass

from core.models import ProfileOpportunity


@dataclass(frozen=True)
class OpportunityScoreResult:
    total_score: int
    priority_band: str
    action_bucket: str
    score_reason_short: str


def _validate_score(name: str, value: int, allowed_values: set[int]) -> None:
    if value not in allowed_values:
        raise ValueError(f"Invalid {name}: {value}")


def calculate_total_score(
    *,
    source_quality_score: int,
    profile_signal_score: int,
    intent_guess_score: int,
    target_fit_score: int,
    risk_penalty_score: int,
) -> int:
    return (
        source_quality_score
        + profile_signal_score
        + intent_guess_score
        + target_fit_score
        + risk_penalty_score
    )


def build_score_reason_short(
    *,
    source_quality_score: int,
    profile_signal_score: int,
    intent_guess_score: int,
    target_fit_score: int,
    risk_penalty_score: int,
) -> str:
    source_map = {
        0: "Zwakke bron",
        1: "Redelijke bron",
        2: "Sterke bron",
    }
    source_text = source_map[source_quality_score]

    if target_fit_score == 2 and intent_guess_score == 2:
        fit_intent_text = "sterke fit, duidelijke intentie"
    elif target_fit_score >= 1 and intent_guess_score == 2:
        fit_intent_text = "goede fit, duidelijke intentie"
    elif target_fit_score >= 1 and intent_guess_score == 1:
        fit_intent_text = "redelijke fit, intentie nog onzeker"
    elif target_fit_score == 0:
        if profile_signal_score >= 1:
            fit_intent_text = "matige fit, profiel nog wel bruikbaar"
        else:
            fit_intent_text = "matige fit en beperkt signaal"
    elif profile_signal_score == 0 and intent_guess_score == 0:
        fit_intent_text = "beperkt signaal"
    elif profile_signal_score >= 1:
        fit_intent_text = "profiel oké, intentie nog onzeker"
    else:
        fit_intent_text = "beperkt signaal"

    parts = [source_text, fit_intent_text]

    if risk_penalty_score == -2:
        parts.append("risico te hoog")
    elif risk_penalty_score == -1:
        parts.append("beperkt risico")

    return ", ".join(parts)


def evaluate_opportunity(
    *,
    source_quality_score: int,
    profile_signal_score: int,
    intent_guess_score: int,
    target_fit_score: int,
    risk_penalty_score: int,
) -> OpportunityScoreResult:
    _validate_score("source_quality_score", source_quality_score, {0, 1, 2})
    _validate_score("profile_signal_score", profile_signal_score, {0, 1, 2})
    _validate_score("intent_guess_score", intent_guess_score, {0, 1, 2})
    _validate_score("target_fit_score", target_fit_score, {0, 1, 2})
    _validate_score("risk_penalty_score", risk_penalty_score, {0, -1, -2})

    total_score = calculate_total_score(
        source_quality_score=source_quality_score,
        profile_signal_score=profile_signal_score,
        intent_guess_score=intent_guess_score,
        target_fit_score=target_fit_score,
        risk_penalty_score=risk_penalty_score,
    )

    score_reason_short = build_score_reason_short(
        source_quality_score=source_quality_score,
        profile_signal_score=profile_signal_score,
        intent_guess_score=intent_guess_score,
        target_fit_score=target_fit_score,
        risk_penalty_score=risk_penalty_score,
    )

    if risk_penalty_score == -2:
        return OpportunityScoreResult(
            total_score=total_score,
            priority_band=ProfileOpportunity.PriorityBand.LOW,
            action_bucket=ProfileOpportunity.ActionBucket.NOT_WORTH,
            score_reason_short=score_reason_short,
        )

    if target_fit_score == 0 and intent_guess_score == 0:
        return OpportunityScoreResult(
            total_score=total_score,
            priority_band=ProfileOpportunity.PriorityBand.LOW,
            action_bucket=ProfileOpportunity.ActionBucket.NOT_WORTH,
            score_reason_short=score_reason_short,
        )

    if total_score >= 7:
        priority_band = ProfileOpportunity.PriorityBand.HIGH
        action_bucket = ProfileOpportunity.ActionBucket.NOW
    elif total_score >= 4:
        priority_band = ProfileOpportunity.PriorityBand.MEDIUM
        action_bucket = ProfileOpportunity.ActionBucket.LATER
    else:
        priority_band = ProfileOpportunity.PriorityBand.LOW
        action_bucket = ProfileOpportunity.ActionBucket.NOT_WORTH

    if (
        total_score == 6
        and intent_guess_score == 2
        and target_fit_score >= 1
        and risk_penalty_score >= -1
    ):
        priority_band = ProfileOpportunity.PriorityBand.HIGH
        action_bucket = ProfileOpportunity.ActionBucket.NOW

    if target_fit_score == 0 and priority_band == ProfileOpportunity.PriorityBand.HIGH:
        priority_band = ProfileOpportunity.PriorityBand.MEDIUM
        action_bucket = ProfileOpportunity.ActionBucket.LATER

    if (
        source_quality_score == 2
        and profile_signal_score == 0
        and intent_guess_score == 0
        and action_bucket == ProfileOpportunity.ActionBucket.NOW
    ):
        priority_band = ProfileOpportunity.PriorityBand.MEDIUM
        action_bucket = ProfileOpportunity.ActionBucket.LATER

    return OpportunityScoreResult(
        total_score=total_score,
        priority_band=priority_band,
        action_bucket=action_bucket,
        score_reason_short=score_reason_short,
    )