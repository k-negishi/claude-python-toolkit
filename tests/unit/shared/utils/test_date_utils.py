"""日時ユーティリティのユニットテスト."""

import time
from datetime import UTC, datetime, timedelta, timezone

import pytest

from src.shared.utils.date_utils import now_utc, parse_rfc2822, struct_time_to_datetime, to_utc


class TestToUtc:
    """to_utc関数のテスト."""

    def test_converts_jst_to_utc(self) -> None:
        """JST日時をUTCに変換できる."""
        jst = timezone(timedelta(hours=9))
        dt = datetime(2025, 1, 15, 18, 0, 0, tzinfo=jst)
        result = to_utc(dt)

        assert result.tzinfo == UTC
        assert result.hour == 9  # JST 18:00 -> UTC 09:00

    def test_converts_naive_datetime_to_utc(self) -> None:
        """タイムゾーン情報がない日時をUTCとして扱う."""
        dt = datetime(2025, 1, 15, 9, 0, 0)
        result = to_utc(dt)

        assert result.tzinfo == UTC
        assert result == datetime(2025, 1, 15, 9, 0, 0, tzinfo=UTC)

    def test_keeps_utc_datetime_unchanged(self) -> None:
        """既にUTCの日時はそのまま."""
        dt = datetime(2025, 1, 15, 9, 0, 0, tzinfo=UTC)
        result = to_utc(dt)

        assert result == dt


class TestStructTimeToDatetime:
    """struct_time_to_datetime関数のテスト."""

    def test_converts_struct_time_to_datetime(self) -> None:
        """struct_timeをUTC datetimeに変換できる."""
        st = time.struct_time((2025, 1, 15, 9, 0, 0, 0, 15, 0))
        result = struct_time_to_datetime(st)

        assert isinstance(result, datetime)
        assert result.tzinfo == UTC


class TestParseRfc2822:
    """parse_rfc2822関数のテスト."""

    def test_parses_rfc2822_format(self) -> None:
        """RFC 2822形式の日時文字列を解析できる."""
        date_string = "Mon, 15 Jan 2025 09:00:00 +0000"
        result = parse_rfc2822(date_string)

        assert result.year == 2025
        assert result.month == 1
        assert result.day == 15
        assert result.hour == 9
        assert result.tzinfo == UTC

    def test_raises_error_on_invalid_format(self) -> None:
        """不正な形式の場合、ValueErrorを送出する."""
        with pytest.raises(ValueError, match="日時文字列の解析に失敗しました"):
            parse_rfc2822("invalid date string")


class TestNowUtc:
    """now_utc関数のテスト."""

    def test_returns_utc_datetime(self) -> None:
        """現在のUTC日時を返す."""
        result = now_utc()

        assert isinstance(result, datetime)
        assert result.tzinfo == UTC
