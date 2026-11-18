import math

import pytest

from src.recommender import load_songs
from src.reliability import (
    ABSTAIN_THRESHOLD,
    CONFIDENT_THRESHOLD,
    GuardrailError,
    compute_confidence,
    detect_conflict,
    reliable_recommend,
    validate_k,
    validate_prefs,
)
from src.recommender import recommend_songs

SONGS = load_songs("data/songs.csv")


# --- Input guardrails --------------------------------------------------------

@pytest.mark.parametrize("energy", [-0.1, 1.7, "loud", math.nan])
def test_bad_energy_is_rejected(energy):
    with pytest.raises(GuardrailError):
        validate_prefs({"genre": "pop", "energy": energy}, SONGS)


def test_empty_profile_is_rejected():
    with pytest.raises(GuardrailError):
        validate_prefs({}, SONGS)


def test_non_text_genre_is_rejected():
    with pytest.raises(GuardrailError):
        validate_prefs({"genre": 42, "energy": 0.5}, SONGS)


def test_messy_input_is_cleaned():
    prefs, warnings = validate_prefs(
        {"genre": "  LoFi ", "mood": "CHILL", "energy": "0.35", "likes_acoustic": "no"}, SONGS)
    assert prefs == {"genre": "lofi", "mood": "chill", "energy": 0.35, "likes_acoustic": False}
    assert warnings == []


def test_unknown_genre_warns_instead_of_crashing():
    _, warnings = validate_prefs({"genre": "k-pop", "mood": "happy", "energy": 0.7}, SONGS)
    assert any("k-pop" in w for w in warnings)


@pytest.mark.parametrize("k", [0, 11, "five"])
def test_bad_k_is_rejected(k):
    with pytest.raises(GuardrailError):
        validate_k(k)


# --- Conflict check and confidence ------------------------------------------

def test_conflict_detected_for_sad_but_hyped():
    prefs = {"genre": "folk", "mood": "sad", "energy": 0.9}
    assert detect_conflict(prefs, recommend_songs(prefs, SONGS)) is not None


def test_no_conflict_for_clean_profile():
    prefs = {"genre": "lofi", "mood": "chill", "energy": 0.35}
    assert detect_conflict(prefs, recommend_songs(prefs, SONGS)) is None


def test_confidence_is_between_0_and_1():
    for prefs in ({"genre": "pop", "mood": "happy", "energy": 0.8},
                  {"genre": "polka", "mood": "spooky", "energy": 0.5},
                  {"energy": 0.5}):
        conf = compute_confidence(prefs, recommend_songs(prefs, SONGS), SONGS)
        assert 0.0 <= conf <= 1.0


def test_known_genre_beats_ghost_genre_confidence():
    real = {"genre": "pop", "mood": "happy", "energy": 0.7}
    ghost = {"genre": "k-pop", "mood": "happy", "energy": 0.7}
    assert (compute_confidence(real, recommend_songs(real, SONGS), SONGS)
            > compute_confidence(ghost, recommend_songs(ghost, SONGS), SONGS))


# --- End-to-end decisions ----------------------------------------------------

def test_clear_profile_is_ok():
    result = reliable_recommend({"genre": "lofi", "mood": "chill", "energy": 0.35}, SONGS)
    assert result.status == "ok"
    assert result.confidence >= CONFIDENT_THRESHOLD
    assert len(result.recommendations) == 5


def test_ghost_genre_is_low_confidence():
    result = reliable_recommend({"genre": "k-pop", "mood": "happy", "energy": 0.7}, SONGS)
    assert result.status == "low_confidence"
    assert result.recommendations  # still shows songs, but with a warning


def test_conflict_downgrades_status_even_with_high_score():
    result = reliable_recommend({"genre": "folk", "mood": "sad", "energy": 0.9}, SONGS)
    assert result.status == "low_confidence"


def test_nonsense_profile_abstains():
    result = reliable_recommend({"genre": "polka", "mood": "spooky", "energy": 0.5}, SONGS)
    assert result.status == "abstained"
    assert result.confidence < ABSTAIN_THRESHOLD
    assert result.recommendations == []


def test_rejected_request_returns_no_songs():
    result = reliable_recommend({"genre": "pop", "energy": 1.7}, SONGS)
    assert result.status == "rejected"
    assert result.recommendations == []
