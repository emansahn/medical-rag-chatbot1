"""
Analytics sample-data generator.

Why this exists:
    The dashboard (and Power BI) must be connectable and demoable from day
    one, even before real usage data exists. This module generates
    realistic-looking synthetic analytics — conversation counts, response
    times, topic distribution — using only the standard library.

Real data path (future work, see docs/future_improvements.md): once
conversations are persisted (e.g. in PostgreSQL), swap `generate_sample_analytics()`
for a real query and keep `export_to_csv()` unchanged — Power BI keeps working.
"""
import csv
import random
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import List

_TOPICS = ["Diabète", "Hypertension", "Vaccination", "Grossesse", "Nutrition", "Santé mentale"]
_ANALYTICS_DIR = Path("data/analytics")


@dataclass
class ConversationRecord:
    date: str
    conversation_id: str
    topic: str
    num_messages: int
    avg_response_time_ms: int
    used_darija: bool
    is_mock_engine: bool


def generate_sample_analytics(days: int = 30, seed: int = 7) -> List[ConversationRecord]:
    """Generate `days` worth of synthetic daily conversation records."""
    rng = random.Random(seed)
    records: List[ConversationRecord] = []
    today = datetime.utcnow().date()

    for day_offset in range(days):
        day = today - timedelta(days=day_offset)
        num_conversations_today = rng.randint(3, 20)
        for i in range(num_conversations_today):
            records.append(
                ConversationRecord(
                    date=day.isoformat(),
                    conversation_id=f"sample-{day.isoformat()}-{i}",
                    topic=rng.choice(_TOPICS),
                    num_messages=rng.randint(2, 12),
                    avg_response_time_ms=rng.randint(300, 3500),
                    used_darija=rng.random() < 0.15,
                    is_mock_engine=True,
                )
            )
    return records


def export_to_csv(records: List[ConversationRecord] | None = None, filename: str = "conversations.csv") -> Path:
    """Write records to `data/analytics/<filename>` — Power BI can connect to
    this folder directly via Get Data > Folder, or to the file via Get Data > Text/CSV."""
    records = records or generate_sample_analytics()
    _ANALYTICS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = _ANALYTICS_DIR / filename

    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(asdict(records[0]).keys()))
        writer.writeheader()
        for record in records:
            writer.writerow(asdict(record))

    return output_path


if __name__ == "__main__":
    path = export_to_csv()
    print(f"Sample analytics written to {path}")
