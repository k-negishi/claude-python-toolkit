"""収集フローの統合テスト."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock, patch

import feedparser
import httpx
import pytest

from src.models.source_config import FeedType, Priority, SourceConfig
from src.repositories.source_master import SourceMaster
from src.services.collector import CollectionResult, Collector


@pytest.fixture
def sample_rss_response() -> str:
    """サンプルRSSレスポンスを返す."""
    return """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Test Feed</title>
    <link>https://example.com</link>
    <description>Test Description</description>
    <item>
      <title>Test Article 1</title>
      <link>https://example.com/article1</link>
      <description>Article 1 description</description>
      <pubDate>Mon, 10 Feb 2025 10:00:00 GMT</pubDate>
    </item>
    <item>
      <title>Test Article 2</title>
      <link>https://example.com/article2</link>
      <description>Article 2 description</description>
      <pubDate>Mon, 10 Feb 2025 11:00:00 GMT</pubDate>
    </item>
  </channel>
</rss>"""


@pytest.fixture
def sample_atom_response() -> str:
    """サンプルAtomレスポンスを返す."""
    return """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>Test Atom Feed</title>
  <link href="https://example.com"/>
  <updated>2025-02-10T10:00:00Z</updated>
  <entry>
    <title>Atom Article 1</title>
    <link href="https://example.com/atom1"/>
    <summary>Atom 1 description</summary>
    <updated>2025-02-10T10:00:00Z</updated>
  </entry>
</feed>"""


@pytest.fixture
def mock_source_master() -> SourceMaster:
    """モックのSourceMasterを返す."""
    source1 = SourceConfig(
        source_id="test_rss",
        name="Test RSS",
        feed_url="https://example.com/rss",
        feed_type=FeedType.RSS,
        priority=Priority.HIGH,
        timeout_seconds=10,
        retry_count=2,
        enabled=True,
    )
    source2 = SourceConfig(
        source_id="test_atom",
        name="Test Atom",
        feed_url="https://example.com/atom",
        feed_type=FeedType.ATOM,
        priority=Priority.MEDIUM,
        timeout_seconds=10,
        retry_count=2,
        enabled=True,
    )
    source_master = Mock(spec=SourceMaster)
    source_master.get_enabled_sources.return_value = [source1, source2]
    return source_master


@pytest.mark.asyncio
async def test_collection_flow_success(
    mock_source_master: SourceMaster,
    sample_rss_response: str,
    sample_atom_response: str,
) -> None:
    """収集フローが正常に動作することを確認."""
    collector = Collector(mock_source_master)

    # httpxのAsyncClientをモック
    mock_response_rss = Mock(spec=httpx.Response)
    mock_response_rss.status_code = 200
    mock_response_rss.text = sample_rss_response

    mock_response_atom = Mock(spec=httpx.Response)
    mock_response_atom.status_code = 200
    mock_response_atom.text = sample_atom_response

    async def mock_get(url: str, *args, **kwargs) -> httpx.Response:
        if "rss" in url:
            return mock_response_rss
        return mock_response_atom

    with patch("httpx.AsyncClient.get", side_effect=mock_get):
        result = await collector.collect()

    # 結果検証
    assert isinstance(result, CollectionResult)
    assert len(result.articles) == 3  # RSS 2件 + Atom 1件
    assert len(result.errors) == 0

    # 記事内容検証
    article_titles = {article.title for article in result.articles}
    assert "Test Article 1" in article_titles
    assert "Test Article 2" in article_titles
    assert "Atom Article 1" in article_titles


@pytest.mark.asyncio
async def test_collection_flow_partial_failure(
    mock_source_master: SourceMaster,
    sample_rss_response: str,
) -> None:
    """一部のソースが失敗しても、他のソースから収集できることを確認."""
    collector = Collector(mock_source_master)

    # RSSは成功、Atomは失敗
    mock_response_rss = Mock(spec=httpx.Response)
    mock_response_rss.status_code = 200
    mock_response_rss.text = sample_rss_response

    async def mock_get(url: str, *args, **kwargs) -> httpx.Response:
        if "rss" in url:
            return mock_response_rss
        # Atomの場合はタイムアウトエラー
        raise httpx.TimeoutException("Timeout")

    with patch("httpx.AsyncClient.get", side_effect=mock_get):
        result = await collector.collect()

    # 結果検証
    assert isinstance(result, CollectionResult)
    assert len(result.articles) == 2  # RSS 2件のみ
    assert len(result.errors) == 1


@pytest.mark.asyncio
async def test_collection_flow_all_failure(mock_source_master: SourceMaster) -> None:
    """全てのソースが失敗した場合でも例外を投げないことを確認."""
    collector = Collector(mock_source_master)

    async def mock_get(url: str, *args, **kwargs) -> httpx.Response:
        raise httpx.HTTPError("Connection error")

    with patch("httpx.AsyncClient.get", side_effect=mock_get):
        result = await collector.collect()

    # 結果検証
    assert isinstance(result, CollectionResult)
    assert len(result.articles) == 0
    assert len(result.errors) == 2
