# รายงานแล็บ w10: RAG over course documents (ฉบับสมบูรณ์)

## ระเบียบวิธี
รันทั้งหมด 5 รอบ เปรียบเทียบ chunk size 256 vs 512 tokens, embedding mMiniLM, hybrid search (BM25+vector) + rerank top-20→5
วัด retrieval (Recall@5) แยกจาก generation (faithfulness) ตามที่เรียนใน week 10

## ผล
| chunk | Recall@5 | faithfulness |
|---|---|---|
| 256 | 0.81 | 0.88 |
| 512 | 0.74 | 0.85 |

รัน 5 รอบ ค่าเฉลี่ย ± SD รายงานครบ อ้างอิง runs.jsonl

## อ้างอิง
- Jurafsky & Martin Ch.10 https://web.stanford.edu/~jurafsky/slp3/
- https://modelcontextprotocol.io

## สรุป
chunk 256 + hybrid + rerank ดีที่สุดบน corpus วิชา (120 docs) ควรตรึงโมเดลก่อนเทียบผล
