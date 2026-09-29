"""
export_training_data.py
Turns your real chat history into a JSONL file for fine-tuning a model's TONE.

Run from the backend folder:
    python export_training_data.py
    python export_training_data.py --intents llm,faq,greeting,thanks --out training_data.jsonl

IMPORTANT
- Fine-tune for style/tone only. Never for facts like fees or seats: they change,
  and a fine-tuned model would keep repeating old numbers. Facts stay in the database.
- The default intents skip fees/seats/eligibility answers for exactly that reason.
- Open the file and edit the answers by hand. You are teaching the model, so only keep replies
  you'd be proud of. Aim for 100+ good examples before fine-tuning.
- OpenAI supports fine-tuning of chat models with this format. It is not available through
  the free Gemini/Groq OpenAI-compatible endpoints.
"""
import argparse
import json

from app.database import get_db
from app.models.chat import ChatHistory

SYSTEM = (
    "You are Vivi, a friendly, sharp admissions counsellor at Vivek College of Commerce. "
    "Talk like a real person: warm, short, helpful. Never invent fees, seats or dates."
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="training_data.jsonl")
    parser.add_argument("--intents", default="llm,faq,greeting,thanks")
    args = parser.parse_args()
    intents = {i.strip() for i in args.intents.split(",")}

    db = next(get_db())
    rows = (
        db.query(ChatHistory)
        .filter(ChatHistory.intent.in_(intents))
        .order_by(ChatHistory.created_at.asc())
        .all()
    )

    seen, written = set(), 0
    with open(args.out, "w", encoding="utf-8") as f:
        for r in rows:
            q, a = (r.question or "").strip(), (r.answer or "").strip()
            if len(q) < 3 or len(a) < 10 or q.lower() in seen:
                continue
            seen.add(q.lower())
            f.write(json.dumps({"messages": [
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": q},
                {"role": "assistant", "content": a},
            ]}, ensure_ascii=False) + "\n")
            written += 1
    print(f"Wrote {written} examples to {args.out}")


if __name__ == "__main__":
    main()