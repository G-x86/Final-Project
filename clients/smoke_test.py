#!/usr/bin/env python3
"""Smoke test: client ตัวที่ 1 (Python SDK ผ่าน stdio).

ตรวจว่า server ตัวเดิมไม่แก้โค้ด ตอบ client นี้ได้ครบ:
6 tools + 2 resources + 1 prompt และเรียก get_failures ได้จริง

ใช้:  python clients/smoke_test.py
"""
from __future__ import annotations

import asyncio
import pathlib
import sys

HERE = pathlib.Path(__file__).parent.parent

for _s in (sys.stdout, sys.stderr):  # กัน UnicodeEncodeError บน console cp1252 (เช่น CI)
    try:
        _s.reconfigure(encoding="utf-8")
    except Exception:
        pass

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main() -> int:
    params = StdioServerParameters(
        command=sys.executable, args=[str(HERE / "server.py")])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as s:
            await s.initialize()
            tools = await s.list_tools()
            names = sorted(t.name for t in tools.tools)
            assert names == ["get_failures", "read_file_scoped", "run_tests",
                             "search_code", "web_search", "write_patch"], names
            res = await s.list_resources()
            assert sorted(str(r.uri) for r in res.resources) == [
                "repo://last-report", "repo://tree"]
            pr = await s.list_prompts()
            assert [p.name for p in pr.prompts] == ["triage_failure"]
            out = await s.call_tool("get_failures", {})
            assert '"failed"' in out.content[0].text
    print("OK: smoke_test ผ่าน (6 tools + 2 resources + 1 prompt + เรียกได้จริง)")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
