"""คำนวณเกรดนักศึกษา (repo จำลองสำหรับ Final Project MCP).

ฟังก์ชันตั้งใจมีบั๊ก 2 จุด ให้ agent หาผ่าน tools:
  - average(): หารผิด (off-by-one)
  - letter(): ขอบเขตคะแนน 80 ผิด
"""


def average(scores):
    """ค่าเฉลี่ยของคะแนน (บั๊ก: หารด้วย len+1)."""
    if not scores:
        return 0.0
    return sum(scores) / len(scores)


def letter(score):
    """เกรดตัวอักษร: A>=80, B>=70, C>=60, D>=50, F<50 (บั๊ก: 80 ได้ B)."""
    if score >= 80:
        return "A"
    if score >= 70:
        return "B"
    if score >= 60:
        return "C"
    if score >= 50:
        return "D"
    return "F"


def top_student(records):
    """ชื่อนักศึกษาคะแนนสูงสุด (ฟังก์ชันนี้ถูก)."""
    best = max(records, key=lambda r: r["score"])
    return best["name"]
