import csv
from dataclasses import dataclass, asdict
from typing import List, Dict, Tuple, Optional

# ---------------------------------------------------------------------------
# Algorithm Recipe (see README "How The System Works")
#   +2.0  genre match            (exact, case-insensitive)
#   +1.0  mood match             (exact, case-insensitive)
#   +1.5  x energy closeness     (1 - |song energy - target energy|)
#   +0.5  x texture fit          (acousticness if the user likes acoustic,
#                                 1 - acousticness if they do not)
# Max possible score with every preference set = 5.0
# ---------------------------------------------------------------------------
DEFAULT_WEIGHTS: Dict[str, float] = {
    "genre": 2.0,
    "mood": 1.0,
    "energy": 1.5,
    "acoustic": 0.5,
}

# Phase 4 experiment: double energy, halve genre.
EXPERIMENT_WEIGHTS: Dict[str, float] = {
    "genre": 1.0,
    "mood": 1.0,
    "energy": 3.0,
    "acoustic": 0.5,
}

NUMERIC_FIELDS = {
    "id": int,
    "energy": float,
    "tempo_bpm": float,
    "valence": float,
    "danceability": float,
    "acousticness": float,
}


@dataclass
class Song:
    """
    Represents a song and its attributes.
    Required by tests/test_recommender.py
    """
    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float


@dataclass
class UserProfile:
    """
    Represents a user's taste preferences.
    Required by tests/test_recommender.py
    """
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool

    def to_prefs(self) -> Dict:
        """Convert the profile into the dict format used by score_song."""
        return {
            "genre": self.favorite_genre,
            "mood": self.favorite_mood,
            "energy": self.target_energy,
            "likes_acoustic": self.likes_acoustic,
        }


class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py
    """
    def __init__(self, songs: List[Song], weights: Optional[Dict[str, float]] = None):
        """Store the catalog and the weights used to judge each song."""
        self.songs = songs
        self.weights = weights or DEFAULT_WEIGHTS

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        """Return the top k Song objects for a user, highest score first."""
        prefs = user.to_prefs()
        ranked = sorted(
            self.songs,
            key=lambda s: (-score_song(prefs, asdict(s), self.weights)[0], s.title),
        )
        return ranked[:k]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        """Return a readable sentence listing why a song earned its score."""
        score, reasons = score_song(user.to_prefs(), asdict(song), self.weights)
        if not reasons:
            return f"Score {score:.2f}: no preferences matched."
        return f"Score {score:.2f}: " + "; ".join(reasons)


def load_songs(csv_path: str) -> List[Dict]:
    """Read the songs CSV into a list of dicts with numeric fields converted."""
    songs: List[Dict] = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            song = {key: value.strip() for key, value in row.items()}
            for field, cast in NUMERIC_FIELDS.items():
                if field in song and song[field] != "":
                    song[field] = cast(song[field])
            songs.append(song)
    return songs


def max_score(user_prefs: Dict, weights: Optional[Dict[str, float]] = None) -> float:
    """Return the best score any song could get for these preferences."""
    w = weights or DEFAULT_WEIGHTS
    total = 0.0
    if user_prefs.get("genre"):
        total += w["genre"]
    if user_prefs.get("mood"):
        total += w["mood"]
    if user_prefs.get("energy") is not None:
        total += w["energy"]
    if user_prefs.get("likes_acoustic") is not None:
        total += w["acoustic"]
    return total


def score_song(
    user_prefs: Dict, song: Dict, weights: Optional[Dict[str, float]] = None
) -> Tuple[float, List[str]]:
    """Score one song against user preferences and return (score, reasons)."""
    w = weights or DEFAULT_WEIGHTS
    score = 0.0
    reasons: List[str] = []

    genre = user_prefs.get("genre")
    if genre and song["genre"].lower() == genre.lower():
        score += w["genre"]
        reasons.append(f"genre match: {song['genre']} (+{w['genre']:.2f})")

    mood = user_prefs.get("mood")
    if mood and song["mood"].lower() == mood.lower():
        score += w["mood"]
        reasons.append(f"mood match: {song['mood']} (+{w['mood']:.2f})")

    target_energy = user_prefs.get("energy")
    if target_energy is not None:
        gap = abs(float(song["energy"]) - float(target_energy))
        points = w["energy"] * max(0.0, 1.0 - gap)
        score += points
        reasons.append(
            f"energy {song['energy']:.2f} vs target {target_energy:.2f} (+{points:.2f})"
        )

    likes_acoustic = user_prefs.get("likes_acoustic")
    if likes_acoustic is not None:
        acousticness = float(song["acousticness"])
        fit = acousticness if likes_acoustic else 1.0 - acousticness
        points = w["acoustic"] * fit
        score += points
        label = "acoustic" if likes_acoustic else "produced/electronic"
        reasons.append(f"{label} sound fit (+{points:.2f})")

    return round(score, 4), reasons


def recommend_songs(
    user_prefs: Dict,
    songs: List[Dict],
    k: int = 5,
    weights: Optional[Dict[str, float]] = None,
) -> List[Tuple[Dict, float, str]]:
    """Score every song, sort highest first (title breaks ties), return top k."""
    scored = [(song, *score_song(user_prefs, song, weights)) for song in songs]
    ranked = sorted(scored, key=lambda item: (-item[1], item[0]["title"]))
    return [(song, score, "; ".join(reasons)) for song, score, reasons in ranked[:k]]
