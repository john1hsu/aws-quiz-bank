# AWS quiz bank

A bank of paired true/false AWS questions, generated daily from the cited articles in [aws-graph](https://github.com/john1hsu/aws-graph). Each pair holds a true statement and a plausible false twin; quizzes show one side at random.

## Practice on your phone

**Open the app: [john1hsu.github.io/aws-quiz-bank](https://john1hsu.github.io/aws-quiz-bank/)**

The app in `app/` is published with GitHub Pages. It works like Instagram Reels: an endless, full-screen feed with one question per screen.

| Gesture | What it does |
| --- | --- |
| Swipe right | Answer **true** |
| Swipe left | Answer **false** |
| Swipe up | Next question (only after you've answered) |
| Double-tap | Save the question (or tap the bookmark on the right) |

There are no answer or next buttons. New users get quiet hints that fade away once they've learned the gestures: a gentle sway if they hesitate and a small up-chevron after answering. Screen readers still get hidden answer and next buttons.

The screen is kept minimal: the question, a filter chip, your streak of correct answers in a row, and three icons on the right (save, share, and the source article once you've answered). After each answer the question is replaced by a green check or a red ✗ and the explanation. Tapping the source icon also shows the date the fact was last verified. Tap the filter chip to switch to your saved questions, narrow by service area or certification (for example AWS Certified Cloud Practitioner), and see today's score and your best streak.

There's no skipping and no going back: you answer each question before the next appears, and you can't scroll back to earlier ones. Questions are drawn completely at random with no weighting; each one shows once before any repeats. Scores and saved questions stay on your phone; "Copy scores" exports them. On a computer, use ← / → to answer, ↓ or Space for the next question, and S to save. Add it to your home screen to use it offline.

## Practice in the terminal

```bash
pip install -r requirements.txt
python3 scripts/quiz.py                                   # 10 random questions
python3 scripts/quiz.py --area security --n 25
python3 scripts/quiz.py --cert kt:aws-certified-cloud-practitioner
python3 scripts/quiz.py --list                            # areas and certifications
```

Scores go to a git-ignored `.quiz-progress.jsonl`, or `--progress <path>` (for example a file in a private study repo).

## How it works

| Piece | What it does |
| --- | --- |
| `questions/<area>/aws-000123.yaml` | One pair per file; areas match the source repo's domains. Format in `SCHEMA.md` |
| `index/questions.json` | Generated list the app and `quiz.py` read |
| `coverage/coverage.json` | Generated pair counts per article and area |
| `scripts/validate.py` | All quality checks; runs before every commit and in CI |
| `scripts/generate.py` | Picks the next article and turns drafted pairs into files |
| `scripts/refresh.py` | Marks pairs stale when their source article is re-verified or changed, and verifies, supersedes or retires them |
| `scripts/build_index.py` | Writes the index and coverage files |
| `CLAUDE.md` | The daily run's playbook |

### Daily run

Once a day, a scheduled run handles up to 100 pairs and pushes them to `main` as one combined commit, only if every check passes:

1. Mark stale any pair whose source article was re-verified or changed since the pair was checked.
2. Re-verify every stale pair: preview features first, then quotas, prices and other numbers.
3. Spend the rest of the 100-pair budget on new pairs, up to 3 per article per run, starting with the articles that have the fewest pairs (up to 6 per article).

### Keeping up with AWS

AWS has no named releases; it ships continuously and announces the biggest changes at re:Invent each December. aws-graph re-verifies an article when it is older than 180 days or older than the latest re:Invent, and moves its `verified` date. This repo then refreshes that article's pairs:

| Outcome | Action | ID |
| --- | --- | --- |
| Still true | `verified_on` updated, back to active | Same |
| Fact changed (new quota, price or default) | Old pair retired; new pair with `supersedes` | New |
| Service or feature retired | Pair retired | Same |

Stale pairs are left out of quizzes.

## Local setup

```bash
pip install -r requirements.txt
git clone --depth 1 https://github.com/john1hsu/aws-graph .source/aws-graph
python3 scripts/validate.py --source .source/aws-graph
python3 -m http.server   # then open http://localhost:8000/app/
```
