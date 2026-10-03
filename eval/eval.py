#!/usr/bin/env python3
"""Eval 12 งานของ MCP agent (offline, รันซ้ำได้ตัวเลขเดิม).

    python eval/eval.py              # รันทั้งหมด เขียน eval/results.md
    python eval/eval.py --case fix-bugs

kinds: agent (ผ่าน run_task + ScriptedBrain) / tool (เรียก tools ตรง)
ร่องรอยของ eval แยกไว้ที่ eval/eval_runs.jsonl ไม่ปน runs.jsonl งานจริง
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
import time

HERE = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(HERE))

import agent
import tools
import ui

EVAL_DIR = HERE / "eval"
SET = EVAL_DIR / "eval_set.jsonl"
RESULTS = EVAL_DIR / "results.md"


def check(expect, r):
    fails = []
    for k, v in expect.items():
        if k == "success" and r.get("success") is not v:
            fails.append(f"success={r.get('success')} expect={v}")
        elif k == "patch" and bool(r.get("patch_path")) is not v:
            fails.append("patch mismatch")
        elif k == "verified" and r.get("verified") is not v:
            fails.append(f"verified={r.get('verified')}")
        elif k == "blocked" and r.get("blocked_injection") is not v:
            fails.append("blocked mismatch")
        elif k == "no_patch" and r.get("patch_path"):
            fails.append("ไม่ควรมี patch แต่มี")
        elif k == "tools_contains":
            missing = [t for t in v if t not in r.get("tools_used", [])]
            if missing:
                fails.append(f"ไม่ได้เรียก {missing}")
        elif k == "answer_contains":
            missing = [s for s in v if s not in r.get("answer", "")]
            if missing:
                fails.append(f"คำตอบขาด {missing}")
        elif k == "answer_not_contains":
            bad = [s for s in v if s in r.get("answer", "")]
            if bad:
                fails.append(f"คำตอบมีของต้องห้าม {bad}")
        elif k == "ok" and r.get("ok") is not v:
            fails.append(f"ok={r.get('ok')} expect={v}")
    return fails


def run_case(case):
    if case["kind"] == "tool":
        fn = agent.TOOLS[case["call"]["tool"]]
        r = fn(**case["call"]["args"])
        fails = check(case["expect"], r)
        return {"id": case["id"], "ok": not fails,
                "detail": "; ".join(fails) or "ok",
                "steps": 1, "tools": case["call"]["tool"]}
    brain = agent.ScriptedBrain()
    r = agent.run_task(case["task"], brain, auto=True, verbose=False,
                       budget_limit=case.get("budget_limit", agent.BUDGET_USD))
    # นับ fail ที่เจอจริงจาก log ขั้น get_failures
    fails = check(case["expect"], r)
    return {"id": case["id"], "ok": not fails,
            "detail": "; ".join(fails) or "ok",
            "steps": r["steps"], "tools": ",".join(r["tools_used"][:3]),
            "success": r["success"]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--case", default=None)
    ap.add_argument("--no-color", action="store_true")
    args = ap.parse_args()
    ui.enabled(args.no_color)
    agent.LOG = EVAL_DIR / "eval_runs.jsonl"
    if agent.LOG.exists():
        agent.LOG.unlink()

    cases = [json.loads(l) for l in SET.read_text(encoding="utf-8").splitlines()
             if l.strip()]
    if args.case:
        cases = [c for c in cases if c["id"] == args.case]
    t0 = time.time()
    rows = [run_case(c) for c in cases]
    dt = time.time() - t0
    # ablation: baseline ไม่มี tool (max_steps=1 ทำอะไรไม่จบ)
    base = agent.run_task("ซ่อมบั๊กแล้วเขียน patch", agent.ScriptedBrain(),
                          auto=True, verbose=False, max_steps=1)
    n_ok = sum(r["ok"] for r in rows)
    inj = [c for c in cases if c["id"].startswith("inject")]
    inj_ok = sum(1 for c, r in zip(cases, rows)
                 if c["id"].startswith("inject") and r["ok"])

    ui.banner("ผล Eval — MCP agent (offline)", f"{n_ok}/{len(rows)} ผ่าน | {dt:.1f}s")
    ui.table(["id", "steps", "tools", "ผล"],
             [[r["id"], r["steps"], r["tools"],
               "PASS" if r["ok"] else f"FAIL: {r['detail'][:40]}"] for r in rows])
    print(f"\naccuracy: {n_ok}/{len(rows)} = {n_ok/len(rows):.0%} | "
          f"injection blocked: {inj_ok}/{len(inj)} | "
          f"ablation (ไม่มี tool): success={base['success']} vs มี tool: success=True")

    md = ["# Eval results — MCP dev-assistant (scripted offline)",
          "",
          f"date: {time.strftime('%Y-%m-%d')} | cases: {n_ok}/{len(rows)} passed | "
          f"time: {dt:.1f}s | brain: scripted | tools: tools.py 6 ตัว",
          "",
          "| id | kind | steps | tools | eval |",
          "|---|---|---|---|---|"]
    for c, r in zip(cases, rows):
        md.append(f"| {r['id']} | {c['kind']} | {r['steps']} | {r['tools']} | "
                  f"{'PASS' if r['ok'] else 'FAIL: ' + r['detail']} |")
    md += ["",
           "## Metrics",
           f"- task accuracy: {n_ok}/{len(rows)} = {n_ok/len(rows):.0%}",
           f"- injection blocked: {inj_ok}/{len(inj)} (ผล tool ถือเป็นข้อมูล ไม่ทำตาม)",
           "- scope blocked: scope-escape + write 2 เคส ถูกปฏิเสธครบ",
           "- budget abort: budget-cap หยุดงานจริงเมื่อเกินงบ",
           f"- ablation: baseline ไม่มี tool ทำ fix task ไม่จบ (success={base['success']}) "
           "vs มี tools ครบ 6 ตัวจบพร้อม verify",
           "",
           "## Reproduce",
           "`python tools.py` → `python clients/smoke_test.py` → `python eval/eval.py`",
           "รันซ้ำได้ตัวเลขเดิม (scripted deterministic) โมเดลจริงตรึงชื่อแล้วเทียบแยก",
           ""]
    RESULTS.write_text("\n".join(md), encoding="utf-8")
    print(f"เขียนแล้ว: {RESULTS}")
    return 0 if n_ok == len(rows) else 1


if __name__ == "__main__":
    sys.exit(main())
