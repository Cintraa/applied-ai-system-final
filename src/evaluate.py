"""
Evaluation harness: runs VibeFinder 2.0 on predefined profiles and prints a scorecard.

Each case checks two things:
  1. the decision status (ok / low_confidence / abstained / rejected)
  2. an optional behavior check written from the listener's point of view

Run: python -m src.evaluate
"""

try:
    from src.recommender import load_songs
    from src.reliability import reliable_recommend
except ModuleNotFoundError:  # running as `python src/evaluate.py`
    from recommender import load_songs  # type: ignore
    from reliability import reliable_recommend  # type: ignore

SONGS_PATH = "data/songs.csv"


def _titles(result, n=3):
    """First n song titles in a result, for failure messages."""
    return ", ".join(song["title"] for song, _, _ in result.recommendations[:n]) or "none"


# (case name, prefs, k, expected status, behavior check or None, what the check means)
CASES = [
    ("Default Pop/Happy", {"genre": "pop", "mood": "happy", "energy": 0.8},
     5, "ok", lambda r: r.recommendations[0][0]["title"] == "Sunrise City",
     "#1 is Sunrise City"),
    ("Chill Lofi", {"genre": "lofi", "mood": "chill", "energy": 0.35, "likes_acoustic": True},
     5, "ok", lambda r: r.recommendations[0][0]["genre"] == "lofi",
     "#1 is a lofi song"),
    ("Deep Intense Rock", {"genre": "rock", "mood": "intense", "energy": 0.9, "likes_acoustic": False},
     5, "ok", lambda r: r.recommendations[0][0]["title"] == "Storm Runner",
     "#1 is Storm Runner"),
    ("Messy input is cleaned ('  LoFi ', 'CHILL')", {"genre": "  LoFi ", "mood": "CHILL", "energy": "0.35"},
     5, "ok", lambda r: r.recommendations[0][0]["genre"] == "lofi",
     "input cleaned and #1 is a lofi song"),
    ("Sad but Hyped (conflict)", {"genre": "folk", "mood": "sad", "energy": 0.9},
     5, "low_confidence", lambda r: any("conflict" in w for w in r.warnings),
     "conflict warning shown"),
    ("Ghost Genre (k-pop)", {"genre": "k-pop", "mood": "happy", "energy": 0.7},
     5, "low_confidence", lambda r: any("k-pop" in w for w in r.warnings),
     "unknown-genre warning shown"),
    ("Nonsense taste (polka/spooky)", {"genre": "polka", "mood": "spooky", "energy": 0.5},
     5, "abstained", lambda r: r.recommendations == [],
     "no songs returned"),
    ("Energy out of range (1.7)", {"genre": "pop", "mood": "happy", "energy": 1.7},
     5, "rejected", None, ""),
    ("Energy not a number ('loud')", {"genre": "pop", "energy": "loud"},
     5, "rejected", None, ""),
    ("Empty profile", {},
     5, "rejected", None, ""),
    ("Too many songs (k=50)", {"genre": "pop", "mood": "happy", "energy": 0.8},
     50, "rejected", None, ""),
    ("Similar label: indie pop fan wants 'pop'", {"genre": "pop", "mood": "happy", "energy": 0.76},
     5, "ok", lambda r: r.recommendations[1][0]["title"] == "Rooftop Lights",
     "#2 is Rooftop Lights (happy indie pop)"),
]


def run() -> int:
    """Run every case, print one scorecard row each, and return how many passed."""
    songs = load_songs(SONGS_PATH)
    passed = 0
    confidences = []
    failures = []
    print(f"{'#':<4}{'Case':<44}{'Expected':<16}{'Got':<16}{'Conf':<6}Result")
    print("-" * 94)
    for i, (name, prefs, k, expected, check, check_desc) in enumerate(CASES, 1):
        result = reliable_recommend(prefs, songs, k=k)
        status_ok = result.status == expected
        ok = status_ok and (check is None or check(result))
        passed += ok
        if result.status != "rejected":
            confidences.append(result.confidence)
        print(f"{i:<4}{name:<44}{expected:<16}{result.status:<16}"
              f"{result.confidence:<6.2f}{'PASS' if ok else 'FAIL'}")
        if not ok:
            reason = (f"expected status {expected}, got {result.status}" if not status_ok
                      else f"status was right, but behavior check failed: wanted {check_desc}; "
                           f"got top 3 = {_titles(result)}")
            failures.append(f"case {i}: {reason}")
    print("-" * 94)
    avg = sum(confidences) / len(confidences) if confidences else 0.0
    print(f"{passed}/{len(CASES)} cases passed | average confidence (non-rejected): {avg:.2f}")
    for line in failures:
        print(f"  FAIL {line}")
    return passed


if __name__ == "__main__":
    run()
