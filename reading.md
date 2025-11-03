

## 1) Architecture / Flow diagram

Mermaid flow (paste into a mermaid renderer):

```mermaid
flowchart TD
	A[User (CLI) - `src/main.py`] --> B[get_difficulty(username) - `src/adaptive_engine.py`]
	B --> C[generate_question(difficulty) - `src/puzzle_generator.py`]
	C --> A
	A --> D[record_answer(...) - `src/tracker.py`]
	D --> E[`user_progress.json` (persistence)]
	D --> B
	B -->|ML/Rules| F[LogisticRegression model (in-memory in `src/adaptive_engine.py`)]
```

ASCII diagram:

- User (CLI via `src/main.py`)
	- `main.py` calls `get_difficulty(username)` in `src/adaptive_engine.py` to choose next difficulty
	- `adaptive_engine.py` decides difficulty using rule-based streak checks first, and an ML fallback
	- `main.py` calls `generate_question(difficulty)` in `src/puzzle_generator.py` to get the question and answer
	- `main.py` presents the question, measures `time_taken`, and receives `user_answer`
	- `main.py` calls `record_answer(...)` in `src/tracker.py` which appends an entry to `user_progress.json`
	- `adaptive_engine.py` reads history with `get_history(username)` to compute the next difficulty

Files referenced:
- `src/main.py` — CLI loop, times answers, coordinates adaptive engine and tracker
- `src/adaptive_engine.py` — hybrid difficulty logic (streak rules + LogisticRegression fallback)
- `src/puzzle_generator.py` — question generation per difficulty
- `src/tracker.py` — persists per-user history to `user_progress.json`

## 2) Explanation of adaptive logic used (rule-based or ML)

Summary: hybrid — rule-based primary layer with an ML fallback.

Detailed behavior (from `src/adaptive_engine.py`):
- Primary, rule-based heuristics (checked first):
	- Increase difficulty by one level if the last 3 answers are all correct.
		- Code check: `len(history) >= 3 and all(item['correct'] for item in history[-3:])`.
	- Decrease difficulty by one level if the last 2 answers are both incorrect.
		- Code check: `len(history) >= 2 and not any(item['correct'] for item in history[-2:])`.
- ML fallback/assistant:
	- A `LogisticRegression` model maps features to next difficulty index.
	- Features: [previous difficulty index, time_taken, correct (0/1)].
	- The file seeds the model with a small `X_dummy` / `y_dummy` dataset.
	- When there is enough variation in labels from the user's history, the code refits the model on history-derived examples (X_train from history[:-1], y_train from history[1:]).
	- The model predicts next difficulty from the last answer's features.
- State note: A module-level `current_difficulty_index` global holds the current difficulty index; this is process-global (not per-user) in the current code.

Why hybrid?
- Rules are deterministic and interpretable (safe default). ML provides nuance when streak rules don't apply.

## 3) Key metrics tracked and how they influence difficulty

Tracked fields (saved by `src/tracker.py` via `record_answer`):
- `question` — text of the question
- `correct_answer` — ground-truth answer
- `user_answer` — the user's response
- `correct` (bool) — whether the user was correct
- `time_taken` (float seconds) — time spent answering
- `difficulty` (string) — difficulty label of the question asked

How these metrics influence difficulty in the current system:
- Correctness (`correct`):
	- Used directly by streak rules: 3 consecutive correct → move up; 2 consecutive incorrect → move down.
	- Used as a feature (0/1) for the ML model, so higher correctness tends to push predicted difficulty upward.
- Response time (`time_taken`):
	- Included as a raw scalar in the ML feature vector. The trained model coefficients (if any) determine whether faster responses increase difficulty.
	- Not currently normalized per-difficulty or per-user, which is a limitation (see improvements below).
- Previous difficulty (`difficulty`):
	- Encoded to an index and used both in rules (indirectly via `current_difficulty_index`) and in the ML features.

Implicit / derived metrics to consider (recommended refinements):
- Rolling accuracy over last N questions (short-term skill estimate).
- Relative speed: compare `time_taken` to a moving median for that difficulty to detect whether the user is faster/slower than typical for that difficulty.
- Combined score (e.g., correctness weighted by normalized speed) to avoid overreacting to one short fast/slow instance.

Concrete mapping suggestions (recommended):
- Increase difficulty: last 5 answers have ≥4 correct OR rolling accuracy ≥ 0.85 and median time ≤ 50th percentile for that difficulty.
- Decrease difficulty: last 4 answers have ≤1 correct OR rolling accuracy ≤ 0.4.
- Otherwise: keep same level or let ML nudge by +/- 1 only when model confidence (probability) > threshold (e.g., 0.6).

## 4) Why this approach was chosen (rationale)

Rationale for hybrid (rules + ML):
- Rules are simple and explainable. They provide immediate, human-understandable behavior (e.g., reward streaks).
- ML adds personalization for patterns rules don't capture (e.g., slow-but-accurate users, variable topic difficulties).
- Practical for early-stage product: rules work with no training data; ML can progressively personalize as data accumulates.

Tradeoffs and risks in the current implementation:
- The global `current_difficulty_index` is shared across users (bug/race/shared-state issue). Difficulty should be per-user.
- The ML model is refit on small in-memory datasets and not persisted: this can cause unstable behavior.
- Exact numeric equality (`user_answer == correct_answer`) is brittle for floating results (use tolerance).
- Raw `time_taken` is not normalized per difficulty or user; absolute times vary by operation.

Low-risk improvements to implement next:
1. Make difficulty state per-user in `user_progress.json` (store `current_difficulty` per user).
2. Use tolerant numeric comparison (e.g., `math.isclose` with a small relative tolerance) rather than exact equality.
3. Normalize `time_taken` per difficulty (e.g., z-score against a rolling median/std) before feeding to ML.
4. Persist trained models (pickle) and retrain periodically offline or use incremental learners (e.g., `SGDClassifier` with `partial_fit`).
5. Only allow ML to nudge difficulty when predicted class probability > threshold (e.g., 0.6) to reduce oscillation.

## Contract (short)
- Inputs: username plus their `user_progress.json` history; last-answer record fields (difficulty, time_taken, correct).
- Output: next difficulty label in {'easy','medium','hard'}.
- Error modes: empty or corrupted history → default difficulty (`easy`); degenerate training data → no ML re-fit.

## Edge cases considered
- New user: returns default difficulty (current code uses `current_difficulty_index` default 'easy').
- Non-numeric input: `src/main.py` already catches ValueError and asks again.
- Division/float answers: `src/puzzle_generator.py` attempts to create integer divisions by construction, but comparison should still be tolerant.
- Corrupted `user_progress.json`: `tracker.load_progress` catches `JSONDecodeError` and returns empty progress.
- Concurrency: file-based persistence can race if multiple sessions write simultaneously.


