"""
narrative.py — Template-based text generation for insights.

Transforms structured insight data into human-readable sentences and
paragraphs. Uses f-string templates — zero AI dependency.
"""

from typing import Any, Dict, List, Optional


# ── Performance Narratives ──────────────────────────────────────────

def narrate_low_overall_mean(mean: float, pass_mark: int) -> str:
    shortfall = pass_mark - mean
    return (
        f"The overall school mean is {mean:.1f}%, which is {shortfall:.1f} "
        f"percentage points below the pass mark of {pass_mark}%. This indicates "
        f"a systemic performance challenge that requires whole-school intervention."
    )


def narrate_high_overall_mean(mean: float, pass_mark: int) -> str:
    surplus = mean - pass_mark
    return (
        f"The overall school mean is {mean:.1f}%, which is {surplus:.1f} "
        f"percentage points above the pass mark of {pass_mark}%. The school "
        f"is performing well overall."
    )


def narrate_high_fail_rate(fail_rate: float, fail_count: int, total: int) -> str:
    return (
        f"{fail_rate:.1f}% of all scores ({fail_count} out of {total}) "
        f"fall below the pass mark. More than 4 in 10 student-subject scores "
        f"are failing, signalling a need for remedial intervention."
    )


def narrate_weakest_subject(subject: str, mean: float, school_mean: float) -> str:
    gap = school_mean - mean
    return (
        f"{subject} is the weakest subject with a mean of {mean:.1f}%, "
        f"which is {gap:.1f} points below the school average of {school_mean:.1f}%. "
        f"Targeted teacher support and extra revision sessions are recommended."
    )


def narrate_strongest_subject(subject: str, mean: float, school_mean: float) -> str:
    gap = mean - school_mean
    return (
        f"{subject} is the strongest subject with a mean of {mean:.1f}%, "
        f"which is {gap:.1f} points above the school average of {school_mean:.1f}%. "
        f"Consider sharing teaching strategies from this department with others."
    )


def narrate_subject_high_fail_rate(subject: str, fail_rate: float) -> str:
    return (
        f"{subject} has a failure rate of {fail_rate:.1f}%. "
        f"More than half of students are failing this subject, "
        f"indicating a critical need for curriculum review or additional support."
    )


# ── Gap Narratives ──────────────────────────────────────────────────

def narrate_gender_gap(gap: Dict[str, Any]) -> str:
    label = gap.get("label", "Overall")
    male_mean = gap.get("male_mean", 0)
    female_mean = gap.get("female_mean", 0)
    effect = gap.get("effect_size_label", "unknown")
    p_val = gap.get("p_value", 1)
    direction = gap.get("direction", "")

    if direction == "girls_underperforming":
        lagging = "girls"
        leading = "boys"
    else:
        lagging = "boys"
        leading = "girls"

    subject_note = f" in {label}" if label != "Overall" else ""

    return (
        f"A statistically significant gender gap exists{subject_note} "
        f"(p = {p_val:.4f}, {effect} effect size). "
        f"Boys average {male_mean:.1f}% while girls average {female_mean:.1f}%, "
        f"with {lagging} underperforming. "
        f"Consider targeted support strategies for {lagging}."
    )


def narrate_class_gap(gap: Dict[str, Any]) -> str:
    best = gap.get("best_class", "?")
    worst = gap.get("worst_class", "?")
    best_mean = gap.get("best_mean", 0)
    worst_mean = gap.get("worst_mean", 0)
    gap_val = gap.get("gap", 0)
    p_val = gap.get("p_value", 1)

    return (
        f"There is a {gap_val:.1f}-point gap between the best-performing class "
        f"({best}, mean {best_mean:.1f}%) and the lowest-performing class "
        f"({worst}, mean {worst_mean:.1f}%). "
        f"This difference is statistically significant (p = {p_val:.4f}). "
        f"Investigate teaching methods, resources, and class composition differences."
    )


def narrate_term_gap(gap: Dict[str, Any]) -> str:
    best = gap.get("best_term", "?")
    worst = gap.get("worst_term", "?")
    best_mean = gap.get("best_mean", 0)
    worst_mean = gap.get("worst_mean", 0)
    gap_val = gap.get("gap", 0)

    return (
        f"Performance varied across terms: {best} was the strongest "
        f"(mean {best_mean:.1f}%) while {worst} was the weakest "
        f"(mean {worst_mean:.1f}%), a {gap_val:.1f}-point spread. "
        f"Check whether curriculum pacing or external factors contributed."
    )


def narrate_regional_gap(gap: Dict[str, Any]) -> str:
    best = gap.get("best_region", "?")
    worst = gap.get("worst_region", "?")
    gap_val = gap.get("gap", 0)

    return (
        f"A regional performance gap of {gap_val:.1f} points exists between "
        f"{best} (highest) and {worst} (lowest). "
        f"Equity-focused resource allocation may help close this gap."
    )


# ── At-Risk Narratives ─────────────────────────────────────────────

def narrate_risk_summary(
    total: int, high: int, medium: int, high_pct: float
) -> str:
    if high_pct > 25:
        urgency = "This is an alarming proportion requiring immediate school-wide action."
    elif high_pct > 15:
        urgency = "This warrants immediate attention and targeted intervention plans."
    else:
        urgency = "While manageable, these students need close monitoring."

    return (
        f"Out of {total} students, {high} ({high_pct:.1f}%) are at high risk "
        f"and {medium} are at medium risk of academic failure. {urgency}"
    )


def narrate_class_risk_cluster(
    class_name: str, high_count: int, total: int
) -> str:
    return (
        f"Class {class_name} has {high_count} high-risk students out of {total}, "
        f"suggesting a class-level issue that may relate to teaching approach, "
        f"resources, or class dynamics. A class-level intervention is recommended."
    )


# ── Positive Narratives ────────────────────────────────────────────

def narrate_top_performer(name: str, mean: float) -> str:
    return (
        f"{name} is a top performer with an overall average of {mean:.1f}%. "
        f"Recognise this achievement and consider peer mentoring opportunities."
    )


def narrate_most_improved(name: str, slope: float) -> str:
    return (
        f"{name} is showing strong improvement, gaining approximately "
        f"{slope:.1f} points per term. This positive trajectory should be "
        f"acknowledged and encouraged."
    )


def narrate_strong_subject(subject: str, pass_rate: float) -> str:
    return (
        f"{subject} has an excellent pass rate of {pass_rate:.1f}%. "
        f"Teaching methods in this subject could serve as a model for others."
    )


def narrate_improving_trend(
    best_term: str, best_mean: float, worst_term: str, worst_mean: float
) -> str:
    improvement = best_mean - worst_mean
    return (
        f"School performance improved by {improvement:.1f} points from "
        f"{worst_term} ({worst_mean:.1f}%) to {best_term} ({best_mean:.1f}%). "
        f"This positive trend suggests effective interventions are working."
    )


# ── Correlation Narratives ─────────────────────────────────────────

def narrate_strong_correlation(
    subject_a: str, subject_b: str, r: float, p: float
) -> str:
    direction = "positive" if r > 0 else "negative"
    strength = "very strong" if abs(r) > 0.8 else "strong"

    return (
        f"A {strength} {direction} correlation (r = {r:.3f}, p = {p:.4f}) "
        f"exists between {subject_a} and {subject_b}. "
        f"Students who perform well in one tend to perform "
        f"{'well' if r > 0 else 'poorly'} in the other. "
        f"Cross-subject teaching strategies could be beneficial."
    )


# ── Executive Summary ──────────────────────────────────────────────

def generate_executive_summary(insights: List[Dict[str, Any]]) -> str:
    """Combine insights into a multi-paragraph executive summary."""
    if not insights:
        return "No significant insights were generated from the available data."

    critical = [i for i in insights if i.get("severity") == "critical"]
    warnings = [i for i in insights if i.get("severity") == "warning"]
    info = [i for i in insights if i.get("severity") == "info"]

    paragraphs = []

    # Opening line
    total = len(insights)
    paragraphs.append(
        f"The analysis identified {total} key insight(s) across "
        f"{len(set(i['category'] for i in insights))} categories."
    )

    # Critical items
    if critical:
        titles = "; ".join(i["title"] for i in critical[:3])
        paragraphs.append(
            f"⚠️ Critical attention needed: {titles}. "
            f"These issues require immediate administrative action."
        )

    # Warnings
    if warnings:
        titles = "; ".join(i["title"] for i in warnings[:3])
        paragraphs.append(
            f"Areas of concern: {titles}. "
            f"These should be addressed within this term."
        )

    # Positive highlights
    positive = [i for i in insights if i.get("category") == "positive"]
    if positive:
        titles = "; ".join(i["title"] for i in positive[:3])
        paragraphs.append(
            f"Encouraging developments: {titles}."
        )

    # Recommendations summary
    recs = [i.get("recommendation", "") for i in critical + warnings if i.get("recommendation")]
    if recs:
        paragraphs.append(
            f"Priority recommendations: {' '.join(recs[:3])}"
        )

    return "\n\n".join(paragraphs)
