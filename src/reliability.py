"""
Reliability layer for VibeFinder 2.0 (final project AI feature).

Project 3 (VibeFinder 1.0) always returned 5 songs, even when:
  - the request was broken (energy 1.7, energy "loud", nothing filled in),
  - the genre or mood was not in the catalog (k-pop gave no warning),
  - the preferences conflicted (sad + energy 0.9 put a 0.30-energy song at #1).

Every request now goes through this pipeline:
  1. Input guardrails   validate_prefs / validate_k: reject or clean bad input
  2. Scoring            recommend_songs from src/recommender.py (unchanged)
  3. Conflict check     detect_conflict: is the #1 song far from the target energy?
  4. Confidence score   compute_confidence: 0-1, how much to trust this list
  5. Decision           OK, LOW_CONFIDENCE (show + warn), or ABSTAINED (show nothing)
  6. Logging            every step goes to logs/recommender.log
"""

import logging
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    from src.recommender import max_score, recommend_songs
except ModuleNotFoundError:  # running as `python src/main.py`
    from recommender import max_score, recommend_songs  # type: ignore

LOG_PATH = Path(__file__).resolve().parent.parent / "logs" / "recommender.log"

CONFIDENT_THRESHOLD = 0.70   # at or above: OK
ABSTAIN_THRESHOLD = 0.45     # below: refuse to recommend
CONFLICT_ENERGY_GAP = 0.40   # #1 song this far from target energy = conflicting prefs
MAX_K = 10


class GuardrailError(ValueError):
    """Raised when a request is malformed and must be rejected."""


@dataclass
class ReliableResult:
    status: str                      # "ok" | "low_confidence" | "abstained" | "rejected"
    confidence: float
    recommendations: List[Tuple[Dict, float, str]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    message: str = ""
    prefs: Dict = field(default_factory=dict)


def get_logger() -> logging.Logger:
    """File logger shared by every request."""
    logger = logging.getLogger("vibefinder")
    if not logger.handlers:
        LOG_PATH.parent.mkdir(exist_ok=True)
        handler = logging.FileHandler(LOG_PATH, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


def _parse_bool(value) -> bool:
    """Accept True/False or yes/no style text; anything else is rejected."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        text = value.strip().lower()
        if text in {"true", "yes", "y", "1"}:
            return True
        if text in {"false", "no", "n", "0"}:
            return False
    raise GuardrailError(f"likes_acoustic must be true or false, got {value!r}")


def validate_prefs(raw: Dict, songs: List[Dict]) -> Tuple[Dict, List[str]]:
    """Input guardrail. Broken input raises GuardrailError; risky input becomes a warning."""
    prefs: Dict = {}
    warnings: List[str] = []

    for key in ("genre", "mood"):
        value = raw.get(key)
        if value is None:
            continue
        if not isinstance(value, str):
            raise GuardrailError(f"{key} must be text, got {value!r}")
        cleaned = " ".join(value.strip().lower().split())
        if cleaned:
            prefs[key] = cleaned

    if raw.get("energy") is not None:
        try:
            energy = float(raw["energy"])
        except (TypeError, ValueError):
            raise GuardrailError(f"energy must be a number from 0 to 1, got {raw['energy']!r}")
        if math.isnan(energy) or not 0.0 <= energy <= 1.0:
            raise GuardrailError(f"energy must be between 0 and 1, got {raw['energy']}")
        prefs["energy"] = energy

    if raw.get("likes_acoustic") is not None:
        prefs["likes_acoustic"] = _parse_bool(raw["likes_acoustic"])

    if not any(k in prefs for k in ("genre", "mood", "energy")):
        raise GuardrailError("give at least one of genre, mood, or energy")

    genres = {s["genre"].lower() for s in songs}
    moods = {s["mood"].lower() for s in songs}
    if "genre" in prefs and prefs["genre"] not in genres:
        warnings.append(f"genre '{prefs['genre']}' is not in the catalog, so no song can earn genre points")
    if "mood" in prefs and prefs["mood"] not in moods:
        warnings.append(f"mood '{prefs['mood']}' is not in the catalog, so no song can earn mood points")
    if "genre" not in prefs and "mood" not in prefs:
        warnings.append("no genre or mood given, so the list is ranked by energy alone")

    return prefs, warnings


def validate_k(k) -> int:
    """Input guardrail for list length: must be a whole number from 1 to MAX_K."""
    try:
        k = int(k)
    except (TypeError, ValueError):
        raise GuardrailError(f"k must be a whole number, got {k!r}")
    if not 1 <= k <= MAX_K:
        raise GuardrailError(f"k must be between 1 and {MAX_K}, got {k}")
    return k


def detect_conflict(prefs: Dict, recs: List[Tuple[Dict, float, str]]) -> Optional[str]:
    """Flag the 'Sad but Hyped' problem: #1 won on labels but is far from the target energy."""
    if not recs or "energy" not in prefs:
        return None
    top = recs[0][0]
    gap = abs(float(top["energy"]) - prefs["energy"])
    if gap >= CONFLICT_ENERGY_GAP:
        return (f"preferences conflict: #1 '{top['title']}' matches your labels but its energy "
                f"{float(top['energy']):.2f} is {gap:.2f} away from your target {prefs['energy']:.2f}")
    return None


def compute_confidence(prefs: Dict, recs: List[Tuple[Dict, float, str]],
                       songs: List[Dict], weights: Optional[Dict[str, float]] = None) -> float:
    """confidence = 0.5 x top fit + 0.2 x list fit + 0.3 x catalog coverage

    top fit:   #1 score / best possible score for these prefs
    list fit:  average of score / best possible across the returned list
    coverage:  share of the requested genre/mood that exist in the catalog
               (0.5 if neither was given: a vague profile is not a strong signal)
    """
    if not recs:
        return 0.0
    best = max_score(prefs, weights)
    top_fit = recs[0][1] / best
    list_fit = sum(score for _, score, _ in recs) / (best * len(recs))

    genres = {s["genre"].lower() for s in songs}
    moods = {s["mood"].lower() for s in songs}
    checks = []
    if "genre" in prefs:
        checks.append(prefs["genre"] in genres)
    if "mood" in prefs:
        checks.append(prefs["mood"] in moods)
    coverage = sum(checks) / len(checks) if checks else 0.5

    return round(0.5 * top_fit + 0.2 * list_fit + 0.3 * coverage, 2)


def reliable_recommend(raw_prefs: Dict, songs: List[Dict], k=5,
                       weights: Optional[Dict[str, float]] = None) -> ReliableResult:
    """Main entry point: guardrails -> scoring -> conflict check -> confidence -> decision."""
    log = get_logger()
    log.info("request prefs=%s k=%s", raw_prefs, k)

    try:
        prefs, warnings = validate_prefs(raw_prefs, songs)
        k = validate_k(k)
    except GuardrailError as err:
        log.warning("REJECTED by input guardrail: %s", err)
        return ReliableResult("rejected", 0.0, message=f"Request rejected: {err}", prefs=raw_prefs)

    for w in warnings:
        log.warning("guardrail warning: %s", w)

    recs = recommend_songs(prefs, songs, k=k, weights=weights)
    confidence = compute_confidence(prefs, recs, songs, weights)

    conflict = detect_conflict(prefs, recs)
    if conflict:
        warnings.append(conflict)
        log.warning("conflict check: %s", conflict)

    if confidence < ABSTAIN_THRESHOLD:
        result = ReliableResult(
            "abstained", confidence, [], warnings,
            "Not confident enough to recommend anything. Try a genre or mood from the catalog.",
            prefs)
    elif confidence < CONFIDENT_THRESHOLD or conflict:
        result = ReliableResult(
            "low_confidence", confidence, recs, warnings,
            "Weak or conflicting match. Treat these as suggestions, not picks.", prefs)
    else:
        result = ReliableResult("ok", confidence, recs, warnings, "Recommendations ready.", prefs)

    log.info("decision=%s confidence=%.2f returned=%d",
             result.status, confidence, len(result.recommendations))
    return result
