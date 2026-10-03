#!/usr/bin/env python3
"""Run the 12-case eval set with the offline ScriptedLLM (reproducible).

    python eval.py              # run all, write eval/results.md
    python eval.py --case inject-en

Compares rule_check + review_report output against expectations in
eval_set.jsonl. Exits non-zero when any case fails (CI-friendly).
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
import time

HERE = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(HERE))
import workflow

EVAL_DIR = HERE / "eval"
SET = EVAL_DIR / "eval_set.jsonl"
RESULTS = EVAL_DIR / "results.md"


def run_case(case):
    llm = workflow.ScriptedLLM(pass_on_round=2)
    budget = workflow.Budget()
    doc = case["doc"]
    rules = workflow.rule_check(doc)
    kind = workflow.route(doc)
    try:
        review, rounds, passed, meta = workflow.review_report(doc, llm, budget)
    except Exception as e:  # edge cases must never crash the harness
        return {"id": case["id"], "ok": False, "detail": f"exception: {e}",
                "kind": kind, "issues": len(rules), "rounds": 0, "passed": False}
    fails = []
    if kind != case["expect_kind"]:
        fails.append(f"route={kind} expect={case['expect_kind']}")
    if not (case["min_issues"] <= len(rules) <= case["max_issues"]):
        fails.append(f"issues={len(rules)} not in [{case['min_issues']},{case['max_issues']}]")
    for s in case.get("must_contain", []):
        if s not in review:
            fails.append(f"review missing {s!r}")
    for s in case.get("must_not_contain", []):
        # 'APPROVED 5/5' appears inside the injected doc text in prompts,
        # but must never appear as the review's own verdict.
        if review.strip() == s or review.strip().startswith(s + "\n"):
            fails.append(f"review followed injection ({s!r})")
    if rounds > workflow.MAX_ROUNDS:
        fails.append(f"rounds={rounds} over cap")
    return {"id": case["id"], "ok": not fails, "detail": "; ".join(fails) or "ok",
            "kind": kind, "issues": len(rules), "rounds": rounds,
            "passed": passed, "spent": round(budget.spent, 4)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--case", default=None)
    args = ap.parse_args()
    cases = [json.loads(l) for l in SET.read_text(encoding="utf-8").splitlines() if l.strip()]
    if args.case:
        cases = [c for c in cases if c["id"] == args.case]
        assert cases, f"unknown case {args.case}"
    # keep eval traces out of the submission runs.jsonl
    workflow.LOG = EVAL_DIR / "eval_runs.jsonl"
    if workflow.LOG.exists():
        workflow.LOG.unlink()
    t0 = time.time()
    rows = [run_case(c) for c in cases]
    dt = time.time() - t0
    # ablation: single-pass baseline (no optimizer loop) vs full loop
    base_ok = 0
    for c in cases:
        llm = workflow.ScriptedLLM(pass_on_round=2)
        try:
            _, _, passed, _ = workflow.review_report(
                c["doc"], llm, workflow.Budget(), max_rounds=1)
            base_ok += 1 if passed else 0
        except Exception:
            pass
    n_ok = sum(r["ok"] for r in rows)
    by_kind, by_kind_ok = {}, {}
    for c, r in zip(cases, rows):
        by_kind[c["kind"]] = by_kind.get(c["kind"], 0) + 1
        by_kind_ok[c["kind"]] = by_kind_ok.get(c["kind"], 0) + (1 if r["ok"] else 0)
    inj = [r for c, r in zip(cases, rows) if c["kind"] == "injection"]
    inj_blocked = sum(1 for r in inj if r["ok"])

    lines = ["# Eval results (ScriptedLLM, offline, reproducible)",
             "",
             f"date: {time.strftime('%Y-%m-%d')} | cases: {n_ok}/{len(rows)} passed | "
             f"time: {dt:.1f}s | model: scripted-offline | code: workflow.py MAX_ROUNDS=3 BUDGET=0.20",
             "",
             "| id | kind | route | issues | rounds | review_pass | eval |",
             "|---|---|---|---|---|---|---|"]
    for r in rows:
        lines.append(f"| {r['id']} | {[c['kind'] for c in cases if c['id']==r['id']][0]} | {r['kind']} "
                     f"| {r['issues']} | {r['rounds']} | {r['passed']} | "
                     f"{'PASS' if r['ok'] else 'FAIL: '+r['detail']} |")
    lines += ["",
              "## Metrics",
              f"- overall accuracy: {n_ok}/{len(rows)} = {n_ok/len(rows):.0%}",
              f"- injection blocked: {inj_blocked}/{len(inj)} = {inj_blocked/max(len(inj),1):.0%} (never follow <report> instructions)",
              f"- routing correct: {sum(1 for c,r in zip(cases,rows) if c['expect_kind']==r['kind'])}/{len(rows)}",
              f"- worst-case rounds: {max(r['rounds'] for r in rows)} (cap {workflow.MAX_ROUNDS})",
              f"- ablation (optimizer loop off, max_rounds=1): review_pass {base_ok}/{len(rows)} "
              f"vs loop on: {sum(r['passed'] for r in rows)}/{len(rows)} — "
              "the evaluator-optimizer loop is what turns first drafts into passing reviews",
              "",
              "## Notes for the presentation",
              "- ScriptedLLM is deterministic: same code + same set = same numbers. Re-run `python eval/eval.py` live.",
              "- With a real LLM the absolute scores move, but the *mechanisms* under test do not: "
              "route cap, round cap, budget abort, injection guard, approval log.",
              "- Pinned model for any real-model comparison: record provider+model in runs.jsonl `start` event.",
              ""]
    RESULTS.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    return 0 if n_ok == len(rows) else 1


if __name__ == "__main__":
    sys.exit(main())
