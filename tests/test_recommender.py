from src.recommender import (
    Song,
    UserProfile,
    Recommender,
    EXPERIMENT_WEIGHTS,
    load_songs,
    score_song,
    recommend_songs,
)

def make_small_recommender() -> Recommender:
    songs = [
        Song(
            id=1,
            title="Test Pop Track",
            artist="Test Artist",
            genre="pop",
            mood="happy",
            energy=0.8,
            tempo_bpm=120,
            valence=0.9,
            danceability=0.8,
            acousticness=0.2,
        ),
        Song(
            id=2,
            title="Chill Lofi Loop",
            artist="Test Artist",
            genre="lofi",
            mood="chill",
            energy=0.4,
            tempo_bpm=80,
            valence=0.6,
            danceability=0.5,
            acousticness=0.9,
        ),
    ]
    return Recommender(songs)


def test_recommend_returns_songs_sorted_by_score():
    user = UserProfile(
        favorite_genre="pop",
        favorite_mood="happy",
        target_energy=0.8,
        likes_acoustic=False,
    )
    rec = make_small_recommender()
    results = rec.recommend(user, k=2)

    assert len(results) == 2
    # Starter expectation: the pop, happy, high energy song should score higher
    assert results[0].genre == "pop"
    assert results[0].mood == "happy"


def test_explain_recommendation_returns_non_empty_string():
    user = UserProfile(
        favorite_genre="pop",
        favorite_mood="happy",
        target_energy=0.8,
        likes_acoustic=False,
    )
    rec = make_small_recommender()
    song = rec.songs[0]

    explanation = rec.explain_recommendation(user, song)
    assert isinstance(explanation, str)
    assert explanation.strip() != ""


# ---------------------------------------------------------------------------
# Functional API tests (load_songs / score_song / recommend_songs)
# ---------------------------------------------------------------------------

def _song(**overrides):
    base = {
        "id": 99, "title": "X", "artist": "Y", "genre": "pop", "mood": "happy",
        "energy": 0.5, "tempo_bpm": 100.0, "valence": 0.5,
        "danceability": 0.5, "acousticness": 0.5,
    }
    base.update(overrides)
    return base


def test_load_songs_converts_numeric_fields():
    songs = load_songs("data/songs.csv")
    assert len(songs) >= 10
    first = songs[0]
    assert isinstance(first["id"], int)
    for field in ("energy", "tempo_bpm", "valence", "danceability", "acousticness"):
        assert isinstance(first[field], float)


def test_score_song_returns_score_and_reasons():
    score, reasons = score_song({"genre": "pop", "mood": "happy", "energy": 0.5}, _song())
    assert score == 4.5  # 2.0 genre + 1.0 mood + 1.5 perfect energy
    assert any("genre match" in r for r in reasons)
    assert any("mood match" in r for r in reasons)


def test_energy_rewards_closeness_not_loudness():
    prefs = {"energy": 0.4}
    close, _ = score_song(prefs, _song(energy=0.45))
    loud, _ = score_song(prefs, _song(energy=0.95))
    assert close > loud


def test_genre_match_is_case_insensitive():
    score, _ = score_song({"genre": "Pop"}, _song(genre="pop"))
    assert score == 2.0


def test_recommend_songs_sorted_and_limited_to_k():
    songs = load_songs("data/songs.csv")
    results = recommend_songs({"genre": "lofi", "mood": "chill", "energy": 0.35}, songs, k=3)
    assert len(results) == 3
    scores = [score for _, score, _ in results]
    assert scores == sorted(scores, reverse=True)
    assert results[0][0]["genre"] == "lofi"


def test_experiment_weights_shift_ranking_toward_energy():
    songs = load_songs("data/songs.csv")
    prefs = {"genre": "pop", "mood": "happy", "energy": 0.8}
    base = [s["title"] for s, _, _ in recommend_songs(prefs, songs, k=3)]
    exp = [s["title"] for s, _, _ in recommend_songs(prefs, songs, k=3, weights=EXPERIMENT_WEIGHTS)]
    assert base.index("Gym Hero") < base.index("Rooftop Lights")
    assert exp.index("Rooftop Lights") < exp.index("Gym Hero")
