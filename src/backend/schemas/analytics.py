"""Schemas for the analytics/dashboard endpoints."""
from typing import Dict

from pydantic import BaseModel


class AnalyticsSummary(BaseModel):
    total_conversations: int
    total_messages: int
    avg_response_time_ms: float
    darija_usage_rate: float
    conversations_by_topic: Dict[str, int]
    is_sample_data: bool


class ConversationRecordSchema(BaseModel):
    date: str
    conversation_id: str
    topic: str
    num_messages: int
    avg_response_time_ms: int
    used_darija: bool
    is_mock_engine: bool


class AnalyticsExportResponse(BaseModel):
    file_path: str
    record_count: int
    message: str
