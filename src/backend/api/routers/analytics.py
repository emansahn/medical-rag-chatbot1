"""
Analytics/dashboard endpoints.

Powers both a future in-app dashboard page and external BI tools:

- `GET /analytics/summary` — JSON summary for an in-app dashboard widget.
- `GET /analytics/conversations` — raw records as JSON.
- `POST /analytics/export` — (re)generates `data/analytics/conversations.csv`.
  Power BI connects to this folder/file directly (Get Data > Folder, or
  Get Data > Text/CSV) — no API auth or special connector needed for the
  academic deliverable.

Currently backed entirely by synthetic sample data (`src/analytics/sample_data.py`)
so the dashboard is demoable before real conversation analytics exist.
"""
from collections import Counter
from typing import List

from fastapi import APIRouter

from src.analytics.sample_data import ConversationRecord, export_to_csv, generate_sample_analytics
from src.backend.schemas.analytics import AnalyticsExportResponse, AnalyticsSummary, ConversationRecordSchema

router = APIRouter(prefix="/analytics", tags=["Analytics"])


def _records() -> List[ConversationRecord]:
    return generate_sample_analytics()


@router.get("/summary", response_model=AnalyticsSummary, summary="Dashboard summary metrics")
def get_summary() -> AnalyticsSummary:
    records = _records()
    total_messages = sum(r.num_messages for r in records)
    avg_response = sum(r.avg_response_time_ms for r in records) / len(records)
    darija_rate = sum(1 for r in records if r.used_darija) / len(records)
    topic_counts = Counter(r.topic for r in records)

    return AnalyticsSummary(
        total_conversations=len(records),
        total_messages=total_messages,
        avg_response_time_ms=round(avg_response, 1),
        darija_usage_rate=round(darija_rate, 3),
        conversations_by_topic=dict(topic_counts),
        is_sample_data=True,
    )


@router.get("/conversations", response_model=List[ConversationRecordSchema], summary="Raw analytics records")
def get_conversations() -> List[ConversationRecordSchema]:
    return [ConversationRecordSchema(**r.__dict__) for r in _records()]


@router.post("/export", response_model=AnalyticsExportResponse, summary="Export CSV for Power BI")
def export_csv() -> AnalyticsExportResponse:
    records = _records()
    path = export_to_csv(records)
    return AnalyticsExportResponse(
        file_path=str(path),
        record_count=len(records),
        message="Power BI: Get Data > Folder (data/analytics/) or Text/CSV, then point to this file.",
    )
