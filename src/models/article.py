"""記事エンティティモジュール."""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class Article:
    """記事エンティティ.

    RSS/Atomフィードから収集された記事を表す.

    Attributes:
        url: 正規化されたURL（一意キー）
        title: 記事タイトル
        published_at: 公開日時（UTC）
        source_name: ソース名（例: "Hacker News"）
        description: 記事の概要（最大800文字）
        normalized_url: 正規化前の元URL
        collected_at: 収集日時（UTC）
    """

    url: str
    title: str
    published_at: datetime
    source_name: str
    description: str
    normalized_url: str
    collected_at: datetime
