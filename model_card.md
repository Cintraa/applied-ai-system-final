# 🎧 Model Card: VibeFinder 2.0 (Applied AI System)

> **Final project update.** Sections 10-15 cover the reliability layer added for the final project: guardrails, conflict check, confidence scoring, abstention, logging, and evaluation. Sections 1-9 are the original Project 3 (VibeFinder 1.0) card, kept because they document the failures this version was built to catch.

## 1. Model Name

**VibeFinder 2.0**, a content-based music recommender that runs in the terminal.

---

## 2. Intended Use

**Goal / Task:** Given a user's taste profile (favorite genre, favorite mood, target energy, and optionally whether they like acoustic sound), VibeFinder predicts which songs in a small catalog that user will like most. It returns a ranked top-*k* list where every song comes with a score and plain-English reasons.

**Intended use**
- Classroom exploration of how recommenders turn data into predictions.
- Testing how weights, features, and dataset balance change what gets recommended.
- Showing what "explainable" recommendations look like (every point is accounted for).

**Assumptions about the user:** they can describe their taste with one genre, one mood, and one energy level, and that taste stays the same during a session.

**Not intended for**
- Real users or a real product. The catalog is 20 made-up songs.
- Judging what music is "good." A low score only means "doesn't match this profile."
- Users with mixed taste (two genres, or "happy *and* chill"). The profile can't express that.
- Any decision that matters, like ranking artists for payouts or promotion. The bias in Section 6 would directly hurt underrepresented genres.

---

## 3. How the Model Works

Think of it like a judge at a talent show who gives every song a scorecard:

- **Same genre as you?** +2 points. Genre is the biggest signal of who a song is "for."
- **Same mood as you?** +1 point.
- **How close is the song's energy to the energy you want?** Up to +1.5 points. A perfect match gets all 1.5, and the further away it is, the fewer points it gets. This rewards songs that are *close* to your level, not simply the loudest ones. That way the same rule works for a gym playlist and a study playlist.
- **Do you like acoustic music?** Up to +0.5. More acoustic songs get more points if you said yes, and more produced/electronic songs get more if you said no.

The judge scores **every** song in the catalog, sorts the scorecards from highest to lowest, and shows you the top 5. The judge also writes down *why* each song got its points (for example, "genre match: pop (+2.00)"), so you can see the reasoning.

**Changes from the starter logic:** the starter returned the first *k* songs with a placeholder explanation. I added CSV loading with number conversion, the four-part scoring rule, ranking with a tie-breaker (song title) so results are always the same, a `max_score` so the output shows "4.47 / 4.50," configurable weights (for experiments), and a CLI with 8 test profiles and an `--experiment` mode.

---

## 4. Data

- **Size:** 20 songs (10 from the starter, plus 10 I added).
- **Columns:** id, title, artist, genre, mood, energy, tempo_bpm, valence, danceability, acousticness.
- **What I added:** one song each for hip-hop, classical, metal, reggae, country, r&b, edm, folk, latin, and blues, with new moods (confident, peaceful, angry, nostalgic, romantic, energetic, sad, playful, melancholic) so more types of listeners have at least one real match.
- **Coverage now:** 17 genres and 15 moods. Energy ranges from 0.18 to 0.97, with 9 songs at 0.70 or above and 8 below 0.45.
- **Imbalance:** lofi has 3 songs and pop has 2 (3 if you count "indie pop"). Every other genre has exactly 1. Chill is the most common mood (3 songs).
- **What's missing from "taste":** lyrics, language, vocals vs. instrumental, artist familiarity, era/decade, listening context (gym vs. study vs. sleep), and anything about what *other* listeners do. Tempo, valence, and danceability are in the data but not scored yet.

---

## 5. Strengths

- **Clear-cut profiles work very well.** *Chill Lofi* gets three real lofi songs at the top (4.93, 4.75, 3.81) and then ambient and jazz, which is exactly what I'd put on to study. *Deep Intense Rock* puts *Storm Runner* at #1 with 4.93/5.00.
- **Energy closeness separates opposite listeners.** The pop/happy, rock, and lofi lists barely overlap. High-energy and low-energy users never get each other's songs.
- **Every result explains itself.** Because each point comes with a reason, I could explain every surprise in this card just by reading the terminal output.
- **The output is deterministic.** Ties (for example, *Island Time* vs. *Velvet Hours*, both 1.47) are broken by title, so running it twice gives the same list.

---

## 6. Limitations and Bias

**Main weakness I found: once a user's genre runs out, everyone with high energy gets the same "loud pack."** Because 15 of the 17 genres have only one song, the genre bonus usually fires once. After that, the rest of the top 5 is decided almost entirely by energy closeness. That's why *Gym Hero, Storm Runner, Pulse Reactor,* and *Iron Cathedral* show up together for the High-Energy Pop, Deep Intense Rock, Acoustic Metalhead, *and* Sad but Hyped profiles, four listeners who asked for very different things. This is a small filter bubble caused by dataset imbalance plus a scoring rule that always gives some energy points. Lofi fans don't have this problem only because lofi happens to have three songs, so the system ends up serving lofi users better than metal or folk users.

**Other limitations I observed**
- **Genre label beats actual vibe.** Genre (+2.0) is worth twice mood (+1.0), so *Gym Hero* (pop, intense) beats *Rooftop Lights* (indie pop, happy) for a happy-pop listener.
- **Exact string matching.** "indie pop" gets zero genre credit for a "pop" fan, and "melancholic" gets zero mood credit for a "sad" fan.
- **Conflicting preferences break it.** For "sad + energy 0.9," the #1 song has energy 0.30. Genre + mood (3.0 points) beat a huge energy gap, and songs #2–5 are loud but not sad.
- **Silent failure on unknown genres.** Asking for k-pop gives no warning. The best possible score drops from 4.5 to 2.5 and nobody is told.
- **Weak acoustic preference.** At 0.5 points, "likes acoustic" barely matters, and there are no loud acoustic songs for it to find anyway.

---

## 7. Evaluation

### Profiles tested

I tested 4 "normal" listeners and 4 adversarial profiles meant to trick the scoring. For each one I looked at the top 5 and asked: does this *feel* right, and can I explain every rank from the reasons?

#### Default Pop/Happy
```
================================================================
Profile: Default Pop/Happy
Prefs:   genre=pop | mood=happy | energy=0.80
----------------------------------------------------------------
#1  Sunrise City - Neon Echo                    Score: 4.47 / 4.50
      - genre match: pop (+2.00)
      - mood match: happy (+1.00)
      - energy 0.82 vs target 0.80 (+1.47)
#2  Gym Hero - Max Pulse                        Score: 3.31 / 4.50
      - genre match: pop (+2.00)
      - energy 0.93 vs target 0.80 (+1.30)
#3  Rooftop Lights - Indigo Parade              Score: 2.44 / 4.50
      - mood match: happy (+1.00)
      - energy 0.76 vs target 0.80 (+1.44)
#4  Fuego Lento - Los Satelites                 Score: 1.50 / 4.50
      - energy 0.80 vs target 0.80 (+1.50)
#5  Concrete Verses - Blockline                 Score: 1.47 / 4.50
      - energy 0.78 vs target 0.80 (+1.47)
```

#### High-Energy Pop
```
================================================================
Profile: High-Energy Pop
Prefs:   genre=pop | mood=intense | energy=0.95 | likes_acoustic=False
----------------------------------------------------------------
#1  Gym Hero - Max Pulse                        Score: 4.95 / 5.00
      - genre match: pop (+2.00)
      - mood match: intense (+1.00)
      - energy 0.93 vs target 0.95 (+1.47)
      - produced/electronic sound fit (+0.47)
#2  Sunrise City - Neon Echo                    Score: 3.71 / 5.00
      - genre match: pop (+2.00)
      - energy 0.82 vs target 0.95 (+1.30)
      - produced/electronic sound fit (+0.41)
#3  Storm Runner - Voltline                     Score: 2.89 / 5.00
      - mood match: intense (+1.00)
      - energy 0.91 vs target 0.95 (+1.44)
      - produced/electronic sound fit (+0.45)
#4  Pulse Reactor - KYRO                        Score: 1.99 / 5.00
      - energy 0.95 vs target 0.95 (+1.50)
      - produced/electronic sound fit (+0.49)
#5  Iron Cathedral - Grave Signal               Score: 1.96 / 5.00
      - energy 0.97 vs target 0.95 (+1.47)
      - produced/electronic sound fit (+0.48)
```

#### Chill Lofi
```
================================================================
Profile: Chill Lofi
Prefs:   genre=lofi | mood=chill | energy=0.35 | likes_acoustic=True
----------------------------------------------------------------
#1  Library Rain - Paper Lanterns               Score: 4.93 / 5.00
      - genre match: lofi (+2.00)
      - mood match: chill (+1.00)
      - energy 0.35 vs target 0.35 (+1.50)
      - acoustic sound fit (+0.43)
#2  Midnight Coding - LoRoom                    Score: 4.75 / 5.00
      - genre match: lofi (+2.00)
      - mood match: chill (+1.00)
      - energy 0.42 vs target 0.35 (+1.40)
      - acoustic sound fit (+0.35)
#3  Focus Flow - LoRoom                         Score: 3.81 / 5.00
      - genre match: lofi (+2.00)
      - energy 0.40 vs target 0.35 (+1.42)
      - acoustic sound fit (+0.39)
#4  Spacewalk Thoughts - Orbit Bloom            Score: 2.85 / 5.00
      - mood match: chill (+1.00)
      - energy 0.28 vs target 0.35 (+1.40)
      - acoustic sound fit (+0.46)
#5  Coffee Shop Stories - Slow Stereo           Score: 1.92 / 5.00
      - energy 0.37 vs target 0.35 (+1.47)
      - acoustic sound fit (+0.45)
```

#### Deep Intense Rock
```
================================================================
Profile: Deep Intense Rock
Prefs:   genre=rock | mood=intense | energy=0.90 | likes_acoustic=False
----------------------------------------------------------------
#1  Storm Runner - Voltline                     Score: 4.93 / 5.00
      - genre match: rock (+2.00)
      - mood match: intense (+1.00)
      - energy 0.91 vs target 0.90 (+1.48)
      - produced/electronic sound fit (+0.45)
#2  Gym Hero - Max Pulse                        Score: 2.93 / 5.00
      - mood match: intense (+1.00)
      - energy 0.93 vs target 0.90 (+1.46)
      - produced/electronic sound fit (+0.47)
#3  Pulse Reactor - KYRO                        Score: 1.92 / 5.00
      - energy 0.95 vs target 0.90 (+1.43)
      - produced/electronic sound fit (+0.49)
#4  Iron Cathedral - Grave Signal               Score: 1.88 / 5.00
      - energy 0.97 vs target 0.90 (+1.40)
      - produced/electronic sound fit (+0.48)
#5  Sunrise City - Neon Echo                    Score: 1.79 / 5.00
      - energy 0.82 vs target 0.90 (+1.38)
      - produced/electronic sound fit (+0.41)
```

#### Sad but Hyped (adversarial: conflicting mood and energy)
```
================================================================
Profile: Sad but Hyped (conflict)
Prefs:   genre=folk | mood=sad | energy=0.90
----------------------------------------------------------------
#1  Paper Boats - The Quiet Pines               Score: 3.60 / 4.50
      - genre match: folk (+2.00)
      - mood match: sad (+1.00)
      - energy 0.30 vs target 0.90 (+0.60)
#2  Storm Runner - Voltline                     Score: 1.49 / 4.50
      - energy 0.91 vs target 0.90 (+1.48)
#3  Gym Hero - Max Pulse                        Score: 1.46 / 4.50
      - energy 0.93 vs target 0.90 (+1.46)
#4  Pulse Reactor - KYRO                        Score: 1.43 / 4.50
      - energy 0.95 vs target 0.90 (+1.43)
#5  Iron Cathedral - Grave Signal               Score: 1.40 / 4.50
      - energy 0.97 vs target 0.90 (+1.40)
```

#### Ghost Genre (adversarial: genre not in catalog)
```
================================================================
Profile: Ghost Genre (k-pop)
Prefs:   genre=k-pop | mood=happy | energy=0.70
----------------------------------------------------------------
#1  Rooftop Lights - Indigo Parade              Score: 2.41 / 4.50
      - mood match: happy (+1.00)
      - energy 0.76 vs target 0.70 (+1.41)
#2  Sunrise City - Neon Echo                    Score: 2.32 / 4.50
      - mood match: happy (+1.00)
      - energy 0.82 vs target 0.70 (+1.32)
#3  Night Drive Loop - Neon Echo                Score: 1.43 / 4.50
      - energy 0.75 vs target 0.70 (+1.42)
#4  Concrete Verses - Blockline                 Score: 1.38 / 4.50
      - energy 0.78 vs target 0.70 (+1.38)
#5  Fuego Lento - Los Satelites                 Score: 1.35 / 4.50
      - energy 0.80 vs target 0.70 (+1.35)
```

#### Acoustic Metalhead (adversarial: contradictory texture)
```
================================================================
Profile: Acoustic Metalhead
Prefs:   genre=metal | mood=angry | energy=0.95 | likes_acoustic=True
----------------------------------------------------------------
#1  Iron Cathedral - Grave Signal               Score: 4.49 / 5.00
      - genre match: metal (+2.00)
      - mood match: angry (+1.00)
      - energy 0.97 vs target 0.95 (+1.47)
      - acoustic sound fit (+0.01)
#2  Pulse Reactor - KYRO                        Score: 1.51 / 5.00
      - energy 0.95 vs target 0.95 (+1.50)
      - acoustic sound fit (+0.01)
#3  Gym Hero - Max Pulse                        Score: 1.50 / 5.00
      - energy 0.93 vs target 0.95 (+1.47)
      - acoustic sound fit (+0.03)
#4  Storm Runner - Voltline                     Score: 1.49 / 5.00
      - energy 0.91 vs target 0.95 (+1.44)
      - acoustic sound fit (+0.05)
#5  Fuego Lento - Los Satelites                 Score: 1.40 / 5.00
      - energy 0.80 vs target 0.95 (+1.28)
      - acoustic sound fit (+0.12)
```

#### Dead Center (adversarial: energy only, no genre or mood)
```
================================================================
Profile: Dead Center (energy only)
Prefs:   energy=0.50
----------------------------------------------------------------
#1  Island Time - Sol Harbor                    Score: 1.47 / 1.50
      - energy 0.52 vs target 0.50 (+1.47)
#2  Velvet Hours - Amara Lane                   Score: 1.47 / 1.50
      - energy 0.48 vs target 0.50 (+1.47)
#3  Dusty Backroads - Wren Holloway             Score: 1.43 / 1.50
      - energy 0.55 vs target 0.50 (+1.42)
#4  Midnight Coding - LoRoom                    Score: 1.38 / 1.50
      - energy 0.42 vs target 0.50 (+1.38)
#5  Focus Flow - LoRoom                         Score: 1.35 / 1.50
      - energy 0.40 vs target 0.50 (+1.35)
```

### Does it match my intuition?

For **Chill Lofi**, yes, completely. *Library Rain → Midnight Coding → Focus Flow → Spacewalk Thoughts → Coffee Shop Stories* is basically my study playlist. For **Default Pop/Happy**, #1 and #3 feel right, but #2 (*Gym Hero*) does not. I'd want *Rooftop Lights* there.

**Why did *Sunrise City* rank first for Default Pop/Happy?** It's the only song that collects all three bonuses: pop (+2.00), happy (+1.00), and energy 0.82, which is just 0.02 away from my 0.80 target (+1.47). That's 4.47 out of a possible 4.50. No other song gets both the genre and the mood points.

### Why does "Gym Hero" keep showing up for people who just want "Happy Pop"? (plain language)

The system treats "is it pop?" as the most important question, worth 2 points, while "is it happy?" is only worth 1. *Gym Hero* is a pop song, so it gets the big 2 points right away, and it's also fairly high energy, which a pop/happy listener at 0.8 energy also gets points for. *Rooftop Lights* is actually happy, but it's labeled "indie pop" instead of "pop," so the system doesn't count it as pop at all. It only gets the smaller happy point. In the end, the *label* on *Gym Hero* beats the actual *feeling* of *Rooftop Lights*. A person would never make that mistake, but a scorecard that values labels over feelings does.

### Comparing profile pairs

**Normal profiles**
- **Default Pop/Happy vs. High-Energy Pop:** same two pop songs at the top, but swapped. Changing the mood from happy to intense and raising energy from 0.80 to 0.95 lets *Gym Hero* collect genre + mood + energy and jump to #1. *Storm Runner* (rock) also enters at #3 because it shares the intense mood. This makes sense: the second profile is asking for a workout, not a sunny day.
- **Default Pop/Happy vs. Chill Lofi:** no overlap at all. The pop list lives at energy 0.76–0.93 and the lofi list at 0.28–0.42. The energy target alone pulls them into different halves of the catalog, which is what should happen.
- **Default Pop/Happy vs. Deep Intense Rock:** they only share *Gym Hero* and *Sunrise City*. For the rock fan, *Gym Hero* is #2 because of "intense" + energy, not because of genre, and *Sunrise City* sneaks in at #5 on energy alone. That's a sign the rock list runs out of real matches quickly.
- **High-Energy Pop vs. Chill Lofi:** complete opposites with zero shared songs. The acoustic setting flips too: the pop list earns "produced/electronic" points, and the lofi list earns "acoustic" points (+0.35 to +0.46). This shows that both energy and texture are pulling in the expected direction.
- **High-Energy Pop vs. Deep Intense Rock:** this one surprised me the most. **They have the exact same 5 songs**, just in a different order. Genre only decides who is #1 (*Gym Hero* for pop, *Storm Runner* for rock). After that, both are just "the loudest songs in the catalog." It makes sense mathematically, but it shows that a rock fan and a pop fan with the same energy level are basically treated as the same person.
- **Chill Lofi vs. Deep Intense Rock:** no overlap, but a big fairness difference. The lofi fan gets 3 genre matches because lofi has 3 songs, while the rock fan gets 1 and then pop, EDM, and metal as filler. Same algorithm, very different quality, purely because of the dataset.

**Adversarial profiles vs. normal ones**
- **Sad but Hyped vs. Deep Intense Rock:** songs #2–5 are identical to the rock fan's list (*Storm Runner, Gym Hero, Pulse Reactor, Iron Cathedral*), because energy 0.9 is driving both. But #1 is *Paper Boats*, a 0.30-energy sad folk song, because genre + mood (3.0 points) beat losing 0.9 of the energy points. So the system "trusts" words over numbers. That's valid behavior given the weights, but it's probably not what this listener wants.
- **Ghost Genre (k-pop) vs. Default Pop/Happy:** the same happy songs come back, but in the opposite order. *Rooftop Lights* (0.76) beats *Sunrise City* (0.82) because 0.76 is closer to the 0.70 target, and with no genre points available, energy decides it. The highest score is 2.41 out of 4.50, and the system never says "I don't have k-pop."
- **Acoustic Metalhead vs. High-Energy Pop:** almost the same loud songs. Setting likes_acoustic = True adds only +0.01 to +0.12 because every high-energy song in the catalog is heavily produced. The preference is technically counted, but it can't change anything.
- **Dead Center vs. Chill Lofi:** without genre or mood, the system becomes "closest energy wins." It surfaces *Island Time, Velvet Hours,* and *Dusty Backroads* (reggae, r&b, country), which no other profile ever sees. Mid-energy songs in small genres are only discoverable by users with no strong preferences, which is another hidden bias.

### Experiment: weight shift (energy ×2, genre ×0.5)

The full side-by-side output is in the archived Project 3 README ([`docs/project3_README.md`](docs/project3_README.md#experiments-you-tried)), and you can rerun it with `python -m src.main --experiment`. In short:
- **More accurate:** Default Pop/Happy (*Rooftop Lights* passes *Gym Hero*) and High-Energy Pop (*Storm Runner* passes *Sunrise City*). The lists now follow the vibe more than the label.
- **Just different:** Chill Lofi (*Spacewalk Thoughts* and *Focus Flow* swap, separated by 0.01).
- **Riskier:** Sad but Hyped's #1 lead drops from 2.11 to 0.23 points, so the system is close to recommending metal to a sad-folk fan.
- **No change:** Deep Intense Rock, Ghost Genre, Dead Center. Where genre wasn't deciding anything, changing its weight didn't matter.

### Automated tests

`pytest` runs 8 tests: the two starter OOP tests, plus tests for CSV loading/number conversion, score + reasons output, "closer energy beats louder energy," case-insensitive genre, sorted top-*k*, and a test that locks in the experiment result (*Rooftop Lights* passes *Gym Hero* when energy is doubled). All 8 pass.

---

## 8. Future Work

1. **Smarter matching:** a small genre/mood similarity map (pop ↔ indie pop = 0.8, sad ↔ melancholic = 0.8) so related labels get partial credit instead of zero.
2. **Diversity in the top 5:** after picking #1, slightly penalize songs that share its genre, artist, or energy band, so a "loud pack" can't take over every list. Also warn the user when their genre isn't in the catalog.
3. **More features and multi-taste profiles:** score tempo and valence with the same closeness formula, allow lists like `genres: ["pop", "indie pop"]`, and add simple feedback (skip = small penalty, replay = small boost) as a first step toward collaborative filtering.

---

## 9. Personal Reflection

**Biggest learning moment:** realizing that "recommend" really just means "score everything, then sort." Once I wrote `score_song` and `recommend_songs` was basically one `sorted(...)` call, I understood that the hard part of a recommender isn't the code, it's deciding what the numbers should mean. The High-Energy Pop vs. Deep Intense Rock result (same 5 songs!) made this click. My "rock fan" and "pop fan" were different people in my head, but not in my math.

**How AI tools helped, and when I double-checked:** my AI coding assistant was great for brainstorming. It explained collaborative vs. content-based filtering, suggested the `1 − |gap|` formula for energy, helped me come up with adversarial profiles like "sad but energy 0.9," and explained `.sort()` vs. `sorted()`. I went with `sorted()` because it returns a new list and doesn't reorder the catalog that every profile shares. I still had to verify things by running them. The starter `main.py` imported `from recommender import ...`, which breaks when you run `python -m src.main`, so I fixed the import. I also assumed "indie pop" would count as pop until the terminal output showed *Rooftop Lights* getting no genre points. Every claim in this card comes from actual output, not from what I expected the code to do.

**What surprised me:** how much a short scoring function *feels* like a real recommendation, especially with the reasons printed underneath. "Library Rain, genre match, mood match, energy 0.35 vs target 0.35" honestly reads like something Spotify would say. It also surprised me that the feeling is fragile: one weight change, or one missing genre in the CSV, and it starts recommending gym music to someone who wants happy pop.

**What I'd try next:** add fake listening history for ~50 simulated users and build a tiny collaborative filter ("users who liked *Library Rain* also liked..."), then blend it with this content-based score. I'd want to see if that fixes the "loud pack" problem or just creates a new bubble around whatever is most popular.


---

# Final Project: VibeFinder 2.0

## 10. What Changed

VibeFinder 2.0 keeps the Project 3 scoring rule unchanged and wraps it in a reliability layer (`src/reliability.py`):

- **Input guardrails:** reject energy outside 0-1 or not a number, empty profiles, non-text genres, and k outside 1-10. Clean messy input (`"  LoFi "` becomes `lofi`).
- **Catalog warnings:** warn when a genre or mood isn't in the catalog, or when only energy was given.
- **Conflict check:** flag when the #1 song is 0.40 or more away from the target energy.
- **Confidence score (0-1):** `0.5 × top fit + 0.2 × list fit + 0.3 × catalog coverage`.
- **Decision:** OK (0.70 or higher, no conflict), LOW_CONFIDENCE (0.45-0.70, or any conflict), or ABSTAINED (below 0.45, returns no songs).
- **Logging** of every request and decision to `logs/recommender.log`.
- **Evaluation harness** (`src/evaluate.py`): 12 predefined cases. Each one checks the decision status and a behavior check written from the listener's point of view, and the harness prints the reason for any failure.
- **Visible cleaning:** when the guardrail cleans an input, the CLI prints a `Cleaned:` line so the user can see exactly what was scored.

## 11. Limitations and Biases

- **Confidence measures fit to the rule, not to the listener.** A happy-pop listener gets *Gym Hero* (pop, intense) over *Rooftop Lights* (indie pop, happy) at 0.91 confidence. The genre-label bias from Section 6 is invisible to the reliability layer because every score is high.
- **Catalog imbalance is still there.** Lofi has 3 songs and most genres have 1, so lofi fans get high confidence and a rock fan's list runs out of real matches after #1. The confidence score partly reflects this (list fit), but it can't add songs that don't exist.
- **Exact string matching.** "hip hop" vs "hip-hop", or "sad" vs "melancholic", still get zero credit. The system now *warns* about unknown labels but doesn't suggest the close one.
- **The thresholds are tuned to this data.** 0.70, 0.45, and the 0.40 energy gap were chosen using 20 songs and 12 test cases. They are not universal.
- **Confidence depends on list length.** List fit is averaged over the *k* songs returned, so the same Sad but Hyped profile scores 0.80 at k=3 and 0.78 at k=5. The decision didn't change in any case I tested, but a borderline profile could flip between OK and LOW_CONFIDENCE just by asking for more songs.
- **Energy-only profiles are allowed through as OK** (with a warning). The list fits the request, but it's ranked on one number, so it says little about real taste.

## 12. Misuse and Prevention

| Possible misuse | How the system responds |
|---|---|
| Malformed or extreme input to crash it or skew results (energy 1.7, "loud", k=50, empty profile) | Input guardrails reject it with a clear message. Every rejection is logged. |
| Presenting weak or guessed results as real recommendations | Confidence score plus LOW_CONFIDENCE and ABSTAINED statuses. Every song still shows its reasons. |
| Using it to rank artists for exposure or payouts | Out of scope (see Section 2). The catalog bias in Sections 6 and 11 would hurt underrepresented genres. |
| Trusting a high confidence number blindly | This card documents that confidence can be high while the ranking is wrong (Section 11). A human should still read the reasons. |

## 13. Testing Results

- **Unit tests:** 28/28 pass (`python -m pytest -v`): 8 from Project 3 plus 20 for guardrails, the conflict check, confidence, and end-to-end decisions.
- **Evaluation harness:** 11/12 cases pass (`python -m src.evaluate`). Average confidence on non-rejected cases is 0.76. The harness reports the one failure as: *status was right, but behavior check failed: wanted #2 is Rooftop Lights (happy indie pop); got top 3 = Sunrise City, Gym Hero, Rooftop Lights*.

| Test input | Evaluation criteria | Result |
|---|---|---|
| Default Pop/Happy, Chill Lofi, Deep Intense Rock | Status OK, expected #1 song | Pass (0.91, 0.94, 0.90) |
| `"  LoFi "`, `"CHILL"`, energy `"0.35"` | Input cleaned, status OK, lofi #1 | Pass (0.94) |
| folk / sad / energy 0.9 | LOW_CONFIDENCE with a conflict warning | Pass (0.78) |
| k-pop / happy / 0.7 | LOW_CONFIDENCE with an unknown-genre warning | Pass (0.50) |
| polka / spooky / 0.5 | ABSTAINED, no songs | Pass (0.23) |
| energy 1.7, energy "loud", empty profile, k=50 | REJECTED with a clear message | Pass (4/4) |
| pop / happy / 0.76 | *Rooftop Lights* at #2 | **Fail**: *Gym Hero* at #2, confidence 0.91 |

## 14. What Surprised Me While Testing

The failing case. I expected the confidence score to drop whenever the results were bad, but case 12 scored 0.91, one of the highest, while still putting a gym song above a happy song for a happy-pop listener. The system is confident because it's measuring how well songs fit its *own* rule, and the rule itself is what's biased toward genre labels. The guardrails catch broken input and missing data, but only a test written from the listener's point of view caught a flaw in the design.

## 15. AI Collaboration

**How I used AI on this project:** I used my AI coding assistant as a design partner and a second reviewer, not as an autopilot. I gave it my Project 3 model card and asked which documented failures could become automatic checks, then had it help draft the guardrail functions, the confidence formula, and pytest cases. I ran every suggestion through the tests and the evaluation harness myself, and I set the thresholds (0.70, 0.45, and the 0.40 energy gap) by reading real outputs for all 12 cases.

**A suggestion I accepted:** turning my Project 3 findings into automatic checks: the conflict check for "Sad but Hyped" and the unknown-genre warning for "Ghost Genre." I kept these because they fix exactly the failures I had already documented in Section 6, and Future Work #2 had asked for the genre warning.

**A suggestion I rejected:** an artist-diversity cap (at most one song per artist in a list). The AI proposed it to reduce filter bubbles, but in this catalog it would have pushed *Focus Flow* (LoRoom) out of the Chill Lofi list, even though it's a real lofi match. The "loud pack" bubble I found in Project 3 comes from energy, not from repeated artists, so the cap would have made results worse without fixing the actual problem.

## 16. Portfolio Reflection: What This Project Says About Me as an AI Engineer

I care about whether an AI system deserves trust, not just whether it produces output. In this project I turned the failures I had documented in my own earlier work into guardrails, a confidence score, an abstain option, and an evaluation harness. I also kept a failing test in the final scorecard instead of hiding it, because a system that is 91% confident and wrong is exactly what I want to learn to catch. I want to build tools that explain their decisions, say "I'm not sure" when they should, and come with evidence that anyone can rerun.

**Code:** https://github.com/Cintraa/applied-ai-system-final
