"""収集元設定エンティティモジュール."""

from enum import StrEnum

from pydantic import BaseModel, Field, HttpUrl


class FeedType(StrEnum):
    """フィード種別.

    Attributes:
        RSS: RSSフィード
        ATOM: Atomフィード
    """

    RSS = "rss"
    ATOM = "atom"


class Priority(StrEnum):
    """優先度.

    Attributes:
        HIGH: 高優先度
        MEDIUM: 中優先度
        LOW: 低優先度
    """

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class SourceConfig(BaseModel):
    """収集元設定.

    pydanticを使用したバリデーション付き設定モデル.

    Attributes:
        source_id: ソースID（一意キー、英数字とアンダースコアのみ）
        name: ソース名
        feed_url: RSS/Atom フィードURL
        feed_type: フィード種別
        priority: 優先度
        timeout_seconds: タイムアウト（5-30秒）
        retry_count: リトライ回数（0-5回）
        enabled: 有効フラグ
    """

    source_id: str = Field(min_length=1, max_length=50, pattern="^[a-z0-9_]+$")
    name: str = Field(min_length=1, max_length=100)
    feed_url: HttpUrl
    feed_type: FeedType
    priority: Priority
    timeout_seconds: int = Field(ge=5, le=30, default=10)
    retry_count: int = Field(ge=0, le=5, default=2)
    enabled: bool = True
