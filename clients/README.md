# Client ตัวที่ 2+ : ต่อ server ตัวเดิมโดยไม่แก้โค้ด

server ตัวเดียว (`server.py`) ใช้ได้กับทุก client ที่รองรับ MCP
เปลี่ยนแค่ไฟล์ตั้งค่า

## A. MCP Inspector (เว็บ UI ทดสอบ — ตรวจแล้วว่าเปิดติด)

```powershell
npx @modelcontextprotocol/inspector python server.py
```

เปิดเบราว์เซอร์ตาม URL ที่ขึ้น กด Connect → List Tools → ลองเรียก
`get_failures` จะเห็น test แดง 2 ตัว

## B. Claude Code / Gemini CLI / Qwen Code (AI client)

ตัวอย่าง `mcp.json` (แทน `<ABS_PATH>` ด้วยพาธจริงของโฟลเดอร์นี้):

```json
{
  "mcpServers": {
    "dev-assistant": {
      "command": "python",
      "args": ["<ABS_PATH>/server.py"]
    }
  }
}
```

- Claude Code: `claude mcp add dev-assistant -- python <ABS_PATH>/server.py`
- Gemini CLI: ใส่ก้อนนี้ใน `~/.gemini/settings.json` หัวข้อ `mcpServers`
- Cline / Roo Code: ใส่ในตั้งค่า MCP ของส่วนขยาย VS Code

พาธจริงของเครื่องนี้: `C:\Users\pkhig\Project_got\Final-Project\server.py`

## หลักฐานว่า "server เดียวใช้ได้หลาย client ไม่แก้โค้ด"

1. `python clients/smoke_test.py` — client SDK ผ่าน
2. inspector เปิดติด เห็น 6 tools (รันคำสั่งข้อ A แล้วแคปหน้าจอ)
3. AI client ข้อ B ใช้ `server.py` ไฟล์เดียวกัน ไม่ต้องแก้แม้แต่บรรทัดเดียว
