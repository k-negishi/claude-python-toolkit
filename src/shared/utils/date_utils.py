"""日時ユーティリティモジュール."""

import time
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime


def to_utc(dt: datetime) -> datetime:
    """任意の日時をUTCに変換する.

    Args:
        dt: 変換元の日時（タイムゾーン情報あり/なし）

    Returns:
        UTC日時

    Examples:
        >>> from datetime import datetime, timezone, timedelta
        >>> jst = timezone(timedelta(hours=9))
        >>> dt = datetime(2025, 1, 15, 18, 0, 0, tzinfo=jst)
        >>> to_utc(dt)
        datetime.datetime(2025, 1, 15, 9, 0, tzinfo=datetime.timezone.utc)
    """
    if dt.tzinfo is None:
        # タイムゾーン情報がない場合はUTCとみなす
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def struct_time_to_datetime(struct_time: time.struct_time) -> datetime:
    """time.struct_timeをdatetimeに変換する.

    feedparserが返すstruct_timeをdatetimeに変換する.

    Args:
        struct_time: time.struct_time

    Returns:
        UTC datetime

    Examples:
        >>> import time
        >>> st = time.struct_time((2025, 1, 15, 9, 0, 0, 0, 15, 0))
        >>> struct_time_to_datetime(st)
        datetime.datetime(2025, 1, 15, 9, 0, tzinfo=datetime.timezone.utc)
    """
    # struct_timeをtimestampに変換してからdatetimeに変換
    timestamp = time.mktime(struct_time)
    dt = datetime.fromtimestamp(timestamp)
    return to_utc(dt)


def parse_rfc2822(date_string: str) -> datetime:
    """RFC 2822形式の日時文字列を解析してUTC datetimeに変換する.

    RSSフィードで使用される日時フォーマットを解析する.

    Args:
        date_string: RFC 2822形式の日時文字列
                    （例: "Mon, 15 Jan 2025 09:00:00 +0000"）

    Returns:
        UTC datetime

    Raises:
        ValueError: 日時文字列の解析に失敗した場合

    Examples:
        >>> parse_rfc2822("Mon, 15 Jan 2025 09:00:00 +0000")
        datetime.datetime(2025, 1, 15, 9, 0, tzinfo=datetime.timezone.utc)
    """
    try:
        dt = parsedate_to_datetime(date_string)
        return to_utc(dt)
    except Exception as e:
        raise ValueError(f"日時文字列の解析に失敗しました: {date_string}") from e


def now_utc() -> datetime:
    """現在のUTC日時を取得する.

    Returns:
        現在のUTC datetime

    Examples:
        >>> now_utc()
        datetime.datetime(2025, 1, 15, 9, 0, 0, 123456, tzinfo=datetime.timezone.utc)
    """
    return datetime.now(UTC)
