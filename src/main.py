"""
Command line runner for the Music Recommender Simulation (VibeFinder 1.0).

Usage:
    python -m src.main                 # run every test profile, top 5 each
    python -m src.main --k 3           # change how many songs are shown
    python -m src.main --profile "Chill Lofi"
    python -m src.main --experiment    # weight shift: energy x2, genre x0.5
"""

import argparse
from typing import Dict, List

try:
    from src.recommender import (
        DEFAULT_WEIGHTS,
        EXPERIMENT_WEIGHTS,
        load_songs,
        max_score,
        recommend_songs,
    )
except ModuleNotFoundError:  # running as `python src/main.py`
    from recommender import (  # type: ignore
        DEFAULT_WEIGHTS,
        EXPERIMENT_WEIGHTS,
        load_songs,
        max_score,
        recommend_songs,
    )

SONGS_PATH = "data/songs.csv"
LINE = "=" * 64
THIN = "-" * 64

# Normal listeners
PROFILES: Dict[str, Dict] = {
    "Default Pop/Happy": {"genre": "pop", "mood": "happy", "energy": 0.8},
    "High-Energy Pop": {
        "genre": "pop", "mood": "intense", "energy": 0.95, "likes_acoustic": False,
    },
    "Chill Lofi": {
        "genre": "lofi", "mood": "chill", "energy": 0.35, "likes_acoustic": True,
    },
    "Deep Intense Rock": {
        "genre": "rock", "mood": "intense", "energy": 0.9, "likes_acoustic": False,
    },
}

# Edge cases built to try to trick the scoring logic
ADVERSARIAL_PROFILES: Dict[str, Dict] = {
    "Sad but Hyped (conflict)": {"genre": "folk", "mood": "sad", "energy": 0.9},
    "Ghost Genre (k-pop)": {"genre": "k-pop", "mood": "happy", "energy": 0.7},
    "Acoustic Metalhead": {
        "genre": "metal", "mood": "angry", "energy": 0.95, "likes_acoustic": True,
    },
    "Dead Center (energy only)": {"energy": 0.5},
}


def describe_prefs(prefs: Dict) -> str:
    """Turn a prefs dict into a short one-line summary."""
    parts = []
    for key in ("genre", "mood"):
        if prefs.get(key):
            parts.append(f"{key}={prefs[key]}")
    if prefs.get("energy") is not None:
        parts.append(f"energy={prefs['energy']:.2f}")
    if prefs.get("likes_acoustic") is not None:
        parts.append(f"likes_acoustic={prefs['likes_acoustic']}")
    return " | ".join(parts)


def print_recommendations(name: str, prefs: Dict, songs: List[Dict], k: int,
                          weights: Dict[str, float] = DEFAULT_WEIGHTS) -> None:
    """Print one profile's top k songs with scores and reasons."""
    best = max_score(prefs, weights)
    print(LINE)
    print(f"Profile: {name}")
    print(f"Prefs:   {describe_prefs(prefs)}")
    print(THIN)
    for rank, (song, score, explanation) in enumerate(
        recommend_songs(prefs, songs, k=k, weights=weights), start=1
    ):
        header = f"#{rank}  {song['title']} - {song['artist']}"
        print(f"{header:<48}Score: {score:.2f} / {best:.2f}")
        for reason in explanation.split("; "):
            print(f"      - {reason}")
    print()


def print_experiment(name: str, prefs: Dict, songs: List[Dict], k: int) -> None:
    """Show baseline vs. experiment rankings side by side for one profile."""
    base = recommend_songs(prefs, songs, k=k, weights=DEFAULT_WEIGHTS)
    exp = recommend_songs(prefs, songs, k=k, weights=EXPERIMENT_WEIGHTS)
    print(LINE)
    print(f"Profile: {name}  ({describe_prefs(prefs)})")
    print(THIN)
    print(f"{'Rank':<6}{'Baseline (genre 2.0, energy 1.5)':<36}Experiment (genre 1.0, energy 3.0)")
    for rank, ((b_song, b_score, _), (e_song, e_score, _)) in enumerate(zip(base, exp), start=1):
        left = f"{b_song['title']} ({b_score:.2f})"
        right = f"{e_song['title']} ({e_score:.2f})"
        print(f"#{rank:<5}{left:<36}{right}")
    print()


def main() -> None:
    """Load the catalog and print recommendations for each test profile."""
    parser = argparse.ArgumentParser(description="Music Recommender Simulation")
    parser.add_argument("--k", type=int, default=5, help="songs to show per profile")
    parser.add_argument("--profile", help="run a single profile by name")
    parser.add_argument("--experiment", action="store_true",
                        help="compare baseline weights vs. energy x2 / genre x0.5")
    args = parser.parse_args()

    songs = load_songs(SONGS_PATH)
    print(f"Loaded songs: {len(songs)}\n")

    all_profiles = {**PROFILES, **ADVERSARIAL_PROFILES}
    if args.profile:
        if args.profile not in all_profiles:
            print(f"Unknown profile. Pick one of: {', '.join(all_profiles)}")
            return
        all_profiles = {args.profile: all_profiles[args.profile]}

    for name, prefs in all_profiles.items():
        if args.experiment:
            print_experiment(name, prefs, songs, args.k)
        else:
            print_recommendations(name, prefs, songs, args.k)


if __name__ == "__main__":
    main()
