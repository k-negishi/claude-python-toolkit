"""Orchestrator件名生成のユニットテスト."""

from datetime import datetime, timezone

from src.orchestrator.orchestrator import Orchestrator


def test_build_newsletter_subject_uses_jst_date_and_japanese_format() -> None:
    executed_at = datetime(2026, 2, 13, 18, 30, 0, tzinfo=timezone.utc)

    subject = Orchestrator._build_newsletter_subject(executed_at)

    assert subject == "Techニュースレター - 2026年2月14日"
