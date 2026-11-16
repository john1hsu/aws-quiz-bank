#!/usr/bin/env python3
"""Keep pairs current as aws-graph re-verifies and edits its articles.

  mark-stale  Mark active pairs stale when their source article changed since they were
              verified (aws-graph re-verified it, so its `verified` date moved, or it was edited),
              or when the article was removed or renamed.
  queue       List stale pairs in refresh order (preview features, then limits, prices and
              other numbers, then the rest; oldest first within each).
  verify      The pair is still true: stamp the article's `verified` date and latest version.
  supersede   The fact changed: retire the old pair and add a new one that points back to it.
  retire      The feature or article is gone: retire the pair.

AWS has no named releases. aws-graph re-verifies an article (and moves its `verified` date)
when it is older than 180 days or older than the latest re:Invent, so a pair simply follows
its article: whenever the article changes, the pair is checked again.

Usage:
  python3 scripts/refresh.py mark-stale --source PATH
  python3 scripts/refresh.py queue      --source PATH
  python3 scripts/refresh.py verify     --source PATH aws-000123
  python3 scripts/refresh.py supersede  --source PATH aws-000123 --input new_pair.json
  python3 scripts/refresh.py retire     aws-000123 --reason "service retired on 2027-06-30"
"""
from __future__ import annotations

import argparse
import re
import sys

from common import (find_question, load_all, load_articles, print_json, resolve_source_dir,
                    save_question, source_blob, source_head)

DIGIT_RE = re.compile(r"\d")


def priority(rec: dict) -> tuple:
    if rec.get("feature_status") == "preview":
        tier = 0
    elif DIGIT_RE.search(rec.get("true_statement", "") + rec.get("false_statement", "")):
        tier = 1  # quotas, prices and defaults change most often
    else:
        tier = 2
    return (tier, str(rec.get("verified_on", "")), rec["id"])


def stale_queue(records: list[dict], articles: dict | None = None) -> list[dict]:
    """Stale pairs in refresh order. Every stale pair is ready: its article is already the
    latest version (a missing article means the pair gets retired)."""
    return sorted((r for r in records if r.get("status") == "stale"), key=priority)


def mark_stale(src_dir) -> None:
    articles = load_articles(src_dir)
    marked = []
    for _, rec in load_all():
        if rec.get("status") != "active":
            continue
        path = rec["source"]["path"]
        art = articles.get(path)
        reason = None
        if art is None:
            reason = "source article removed or renamed"
        elif source_blob(src_dir, path) != rec["source"]["blob"]:
            if art.get("verified") and art["verified"] != str(rec.get("verified_on")):
                reason = f"re-verified: article verified {art['verified']}, pair verified {rec.get('verified_on')}"
            else:
                reason = "drift: source article changed since this pair was verified"
        if reason:
            rec["status"], rec["stale_reason"] = "stale", reason
            save_question(rec)
            marked.append({"id": rec["id"], "reason": reason})
    print_json({"marked_stale": marked})


def show_queue(src_dir) -> None:
    ready = stale_queue([r for _, r in load_all()])
    print_json({"ready": [{"id": r["id"], "article": r["source"]["path"], "reason": r.get("stale_reason")}
                          for r in ready]})


def verify(src_dir, qid: str) -> None:
    articles = load_articles(src_dir)
    _, rec = find_question(qid)
    art = articles.get(rec["source"]["path"])
    if art is None:
        sys.exit(f"{qid}: source article is gone; retire the pair instead")
    rec["verified_on"] = art["verified"]
    rec["feature_status"] = art["status"]
    rec["certs"] = art["certs"]
    rec["source"].update(commit=source_head(src_dir), blob=source_blob(src_dir, art["path"]))
    rec["status"] = "active"
    rec.pop("stale_reason", None)
    save_question(rec)
    print(f"{qid}: verified against the article as of {art['verified']}")


def retire(qid: str, reason: str) -> None:
    _, rec = find_question(qid)
    rec["status"] = "retired"
    rec["retired_reason"] = reason
    rec.pop("stale_reason", None)
    save_question(rec)
    print(f"{qid}: retired ({reason})")


def supersede(src_dir, qid: str, input_path: str) -> None:
    import json
    from generate import add
    data = json.loads(open(input_path, encoding="utf-8").read())
    _, old = find_question(qid)
    data.setdefault("article", old["source"]["path"])
    if len(data.get("pairs", [])) != 1:
        sys.exit("supersede takes exactly one replacement pair")
    data["pairs"][0]["supersedes"] = qid
    data["pairs"][0].setdefault("difficulty", old["difficulty"])
    data["pairs"][0].setdefault("concepts", old.get("concepts"))
    tmp = input_path + ".tmp"
    open(tmp, "w", encoding="utf-8").write(json.dumps(data))
    retire(qid, "fact changed; superseded by a newer pair")
    new_ids = add(src_dir, tmp)
    _, old = find_question(qid)
    old["retired_reason"] = f"fact changed; superseded by {new_ids[0]}"
    save_question(old)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("mark-stale", "queue"):
        sub.add_parser(name).add_argument("--source")
    v = sub.add_parser("verify")
    v.add_argument("--source")
    v.add_argument("id")
    s = sub.add_parser("supersede")
    s.add_argument("--source")
    s.add_argument("id")
    s.add_argument("--input", required=True)
    r = sub.add_parser("retire")
    r.add_argument("id")
    r.add_argument("--reason", required=True)
    args = ap.parse_args()

    if args.cmd == "retire":
        retire(args.id, args.reason)
        return 0
    src_dir = resolve_source_dir(args.source)
    if args.cmd == "mark-stale":
        mark_stale(src_dir)
    elif args.cmd == "queue":
        show_queue(src_dir)
    elif args.cmd == "verify":
        verify(src_dir, args.id)
    else:
        supersede(src_dir, args.id, args.input)
    return 0


if __name__ == "__main__":
    sys.exit(main())
