# Question schema

Each true/false **pair** is one YAML file: `questions/<product_area>/<id>.yaml`. The folder names match the article domains in [aws-graph](https://github.com/john1hsu/aws-graph). The quiz serves one side of a pair at random and never both sides in one session.

```yaml
id: aws-000002                    # stable, never reused
product_area: serverless-and-integration   # = source article's domain = folder
true_statement: Amazon SQS FIFO queues deliver each message exactly once and preserve its order within a message group.
false_statement: Amazon SQS standard queues deliver each message exactly once and preserve its order within a message group.
explanation: Exactly-once processing and per-group ordering are FIFO queue features. Standard queues deliver at least once and only make a best effort at ordering.
source:
  repo: john1hsu/aws-graph
  path: articles/serverless-and-integration/amazon-sqs.md
  commit: <source repo HEAD when written or last verified>
  blob: <git blob of the article at that point>
verified_on: '2026-11-08'         # the article's `verified` date when this pair was written or last checked
feature_status: current           # current (GA) | preview | closed-to-new-customers | deprecated | retired | concept, from the article
certs: []                         # from the article's coveredBy edges, e.g. kt:aws-certified-cloud-practitioner
concepts: [kt:amazon-sqs]         # graph node ids; the source article's id comes first
related: []                       # optional: other pair ids
supersedes: aws-000041            # only on a pair that replaced an outdated one
difficulty: 2                     # 1-3
created: '2026-11-15'
status: active                    # active | stale | retired
stale_reason: ...                 # only while stale
retired_reason: ...               # optional, on retired pairs
```

`schema/question.schema.json` has the same rules as a JSON Schema for editors.

## Lifecycle

| Status | Meaning | In the quiz? |
| --- | --- | --- |
| active | Verified against the latest version of its source article | Yes |
| stale | The source article was re-verified or edited since the pair was verified | Only with `--include-stale` |
| retired | The fact changed (a newer pair `supersedes` it), the service/article is gone, or the pair repeated a fact another pair already tests | No |

AWS ships continuously and has no named releases. aws-graph re-verifies each article when it is older than 180 days or older than the latest re:Invent, and moves its `verified` date; that change is what makes the article's pairs stale here.

## Checks (`scripts/validate.py`)

| Check | Fails when |
| --- | --- |
| Schema | A required field is missing, malformed or unknown |
| Unique ID | An ID repeats, or the file name or folder doesn't match |
| Duplicate | A statement closely matches one in another non-retired pair |
| Same fact | Two non-retired pairs, from any articles, have true statements that state one fact in different words: most of their words match, or they share their numbers and most of the shorter statement's words |
| Pair quality | The two statements are identical or differ only by negation |
| Explanation | Shorter than 60 characters |
| Statement form | A statement is a question, under 20 or over 280 characters |
| Source | Repo, path, commit or blob is malformed; with `--source`, the article's domain differs, or an active pair's article is missing, changed, or has a different `verified` date (run `refresh.py mark-stale` first; stale pairs are exempt because they are waiting to be refreshed or retired) |
| Verified date | `verified_on` is not a YYYY-MM-DD date, or `feature_status` is missing or invalid |
| Supersedes | Points to an ID that is missing or not retired |
| Exam-like wording | "Which of the following", "Choose two", "A company wants…", "least operational overhead", exam example companies such as AnyCompany or Example Corp |
