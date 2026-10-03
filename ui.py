#!/usr/bin/env python3
"""UI ปลายทางภาษาไทยสำหรับโปรเจค MCP (stdlib ล้วน ไม่ต้อง pip).

- เปิด ANSI บน Windows อัตโนมัติ (ทำไม่ได้ก็ตกกลับข้อความล้วน ไม่พัง)
- ถ้าไม่ใช่ tty / มี NO_COLOR / ส่ง --no-color จะออกข้อความล้วน (CI-safe)
- log ไฟล์ (.jsonl/.md) ไม่ผ่านโมดูลนี้ จึงไม่มีสีปนในไฟล์เสมอ
"""
from __future__ import annotations

import os
import shutil
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

COLORS = {
    "blue": "\033[94m", "green": "\033[92m", "yellow": "\033[93m",
    "red": "\033[91m", "cyan": "\033[96m", "bold": "\033[1m",
    "dim": "\033[2m", "reset": "\033[0m",
}

_enabled = None


def _enable_windows_ansi():
    try:
        import ctypes
        kernel = ctypes.windll.kernel32
        h = kernel.GetStdHandle(-11)
        mode = ctypes.c_ulong()
        if kernel.GetConsoleMode(h, ctypes.byref(mode)):
            kernel.SetConsoleMode(h, mode.value | 4)
    except Exception:
        pass


def enabled(no_color=False) -> bool:
    """ควรใช้สีหรือไม่ (เรียกครั้งเดียวแล้วจำค่า)."""
    global _enabled
    if _enabled is None:
        _enable_windows_ansi()
        _enabled = (not no_color and "NO_COLOR" not in os.environ
                    and sys.stdout.isatty())
    return _enabled


def c(text: str, color: str) -> str:
    if not enabled():
        return text
    return f"{COLORS[color]}{text}{COLORS['reset']}"


def width() -> int:
    return max(60, min(100, shutil.get_terminal_size(fallback=(80, 24)).columns - 2))


def banner(title: str, subtitle: str = ""):
    w = width()
    print(c("╔" + "═" * (w - 2) + "╗", "cyan"))
    print(c("║", "cyan") + c(f"  {title}", "bold") +
          " " * max(0, w - len(title) - 5) + c("║", "cyan"))
    if subtitle:
        print(c("║", "cyan") + c(f"  {subtitle}", "dim") +
              " " * max(0, w - len(subtitle) - 5) + c("║", "cyan"))
    print(c("╚" + "═" * (w - 2) + "╝", "cyan"))


def panel(title: str, lines: list, color="blue"):
    w = width()
    print(c(f"┌─ {title} " + "─" * max(0, w - len(title) - 5) + "┐", color))
    for ln in lines:
        for chunk in (ln[i:i + w - 4] for i in range(0, max(1, len(ln)), w - 4)):
            print(c("│", color) + f" {chunk}")
    print(c("└" + "─" * (w - 2) + "┘", color))


def table(headers: list, rows: list, aligns: str = ""):
    cols = len(headers)
    widths = [len(h) for h in headers]
    for r in rows:
        for i in range(cols):
            widths[i] = max(widths[i], len(str(r[i])))
    total = sum(widths) + cols * 3 + 1
    if total > width():
        over = total - width()
        widths[-1] = max(10, widths[-1] - over)
    def fmt_row(vals, color=None):
        cells = []
        for i, v in enumerate(vals):
            s = str(v)
            if len(s) > widths[i]:
                s = s[:widths[i] - 1] + "…"
            pad = ">" if aligns[i:i + 1] == "r" else "<"
            cells.append(f"{s:{pad}{widths[i]}}")
        line = "│ " + " │ ".join(cells) + " │"
        return c(line, color) if color else line
    bar = "─" * (sum(widths) + cols * 3 + 1)
    print(c("┌" + bar[1:-1] + "┐", "dim"))
    print(fmt_row(headers, "bold"))
    print(c("├" + bar[1:-1] + "┤", "dim"))
    for r in rows:
        print(fmt_row(r))
    print(c("└" + bar[1:-1] + "┘", "dim"))


def step_card(n: int, total: int, tool: str, args: str, status: str, detail: str = ""):
    mark = {"ok": ("green", "✔"), "fail": ("red", "✘"),
            "run": ("yellow", "▸"), "block": ("red", "⛔")}.get(status, ("dim", "•"))
    head = f"STEP {n}/{total} {mark[1]} {tool}({args})"
    print(c(head, mark[0]))
    if detail:
        for ln in detail.splitlines()[:6]:
            print(c(f"         {ln[:width()-10]}", "dim"))


def meter(used: float, limit: float):
    w = 24
    fill = min(w, int(w * used / limit)) if limit else 0
    bar = "█" * fill + "░" * (w - fill)
    col = "green" if used <= limit * 0.7 else ("yellow" if used <= limit else "red")
    print(f"งบใช้ไป: {c(bar, col)} {used:.4f}/{limit:.2f} USD")


def verdict(passed: bool, lines: list):
    title = "ผลลัพธ์: สำเร็จ" if passed else "ผลลัพธ์: ไม่สำเร็จ"
    panel(title, lines, "green" if passed else "red")


def status_row(label: str, ok: bool, detail: str = ""):
    mark = c("✔ PASS", "green") if ok else c("✘ FAIL", "red")
    print(f"  [{mark}] {label}" + (f" — {detail}" if detail and not ok else ""))
