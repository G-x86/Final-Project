"""เทสต์ของ grades.py: 5 ข้อ, ต้องแดง 2 ข้อ (average, letter-80)."""
import grades


def test_average_basic():
    assert grades.average([80, 90, 100]) == 90.0


def test_average_empty():
    assert grades.average([]) == 0.0


def test_letter_a():
    assert grades.letter(85) == "A"


def test_letter_boundary_80():
    assert grades.letter(80) == "A"


def test_top_student():
    recs = [{"name": "มานี", "score": 75}, {"name": "ปิติ", "score": 92}]
    assert grades.top_student(recs) == "ปิติ"
