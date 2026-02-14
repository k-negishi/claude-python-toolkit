"""Deduplicatorサービスのユニットテスト."""

from datetime import datetime, timezone
from unittest.mock import Mock

import pytest

from src.models.article import Article
from src.repositories.cache_repository import CacheRepository
from src.services.deduplicator import Deduplicator, DeduplicationResult


@pytest.fixture
def sample_articles() -> list[Article]:
    """テスト用の記事リストを生成する."""
    now = datetime.now(timezone.utc)
    return [
        Article(
            url="https://example.com/article1",
            title="Article 1",
            published_at=now,
            source_name="Example",
            description="Description 1",
            normalized_url="https://example.com/article1",
            collected_at=now,
        ),
        Article(
            url="https://example.com/article2",
            title="Article 2",
            published_at=now,
            source_name="Example",
            description="Description 2",
            normalized_url="https://example.com/article2",
            collected_at=now,
        ),
        Article(
            url="https://example.com/article1?utm_source=twitter",  # article1の重複
            title="Article 1 Duplicate",
            published_at=now,
            source_name="Example",
            description="Description 1 Duplicate",
            normalized_url="https://example.com/article1",  # 同じnormalized_url
            collected_at=now,
        ),
    ]


@pytest.fixture
def mock_cache_repository() -> Mock:
    """モックのキャッシュリポジトリを生成する."""
    return Mock(spec=CacheRepository)


class TestDeduplicator:
    """Deduplicatorクラスのテストスイート."""

    def test_deduplicate_removes_url_duplicates(
        self, sample_articles: list[Article], mock_cache_repository: Mock
    ) -> None:
        """URL重複排除が正しく動作する."""
        # キャッシュはすべてヒットしない
        mock_cache_repository.batch_exists.return_value = {}

        deduplicator = Deduplicator(mock_cache_repository)
        result = deduplicator.deduplicate(sample_articles)

        # 3記事のうち1件が重複（article1とarticle1?utm_source=twitter）
        assert len(result.unique_articles) == 2
        assert result.duplicate_count == 1
        assert result.cached_count == 0

        # 先に出現した記事が優先される
        assert result.unique_articles[0].url == "https://example.com/article1"
        assert result.unique_articles[1].url == "https://example.com/article2"

    def test_deduplicate_removes_cached_articles(
        self, sample_articles: list[Article], mock_cache_repository: Mock
    ) -> None:
        """キャッシュ済み記事が除外される."""
        # article1がキャッシュヒット
        mock_cache_repository.batch_exists.return_value = {
            "https://example.com/article1": True,
            "https://example.com/article2": False,
        }

        deduplicator = Deduplicator(mock_cache_repository)
        result = deduplicator.deduplicate(sample_articles)

        # article1とその重複が除外され、article2のみ残る
        assert len(result.unique_articles) == 1
        assert result.duplicate_count == 1  # URL重複
        assert result.cached_count == 1  # キャッシュヒット
        assert result.unique_articles[0].url == "https://example.com/article2"

    def test_deduplicate_with_no_cache_repository(
        self, sample_articles: list[Article]
    ) -> None:
        """cache_repositoryがNoneの場合、キャッシュチェックをスキップする."""
        deduplicator = Deduplicator(cache_repository=None)
        result = deduplicator.deduplicate(sample_articles)

        # キャッシュチェックがスキップされるので、URL重複のみ除外
        assert len(result.unique_articles) == 2
        assert result.duplicate_count == 1
        assert result.cached_count == 0

    def test_deduplicate_empty_list(self, mock_cache_repository: Mock) -> None:
        """空のリストを渡した場合、空の結果を返す."""
        mock_cache_repository.batch_exists.return_value = {}

        deduplicator = Deduplicator(mock_cache_repository)
        result = deduplicator.deduplicate([])

        assert len(result.unique_articles) == 0
        assert result.duplicate_count == 0
        assert result.cached_count == 0

    def test_deduplicate_all_cached(
        self, sample_articles: list[Article], mock_cache_repository: Mock
    ) -> None:
        """すべての記事がキャッシュ済みの場合、空のリストを返す."""
        # すべてキャッシュヒット
        mock_cache_repository.batch_exists.return_value = {
            "https://example.com/article1": True,
            "https://example.com/article2": True,
        }

        deduplicator = Deduplicator(mock_cache_repository)
        result = deduplicator.deduplicate(sample_articles)

        assert len(result.unique_articles) == 0
        assert result.duplicate_count == 1  # URL重複
        assert result.cached_count == 2  # すべてキャッシュヒット

    def test_deduplicate_calls_batch_exists(
        self, sample_articles: list[Article], mock_cache_repository: Mock
    ) -> None:
        """batch_existsが正しいURLリストで呼ばれる."""
        mock_cache_repository.batch_exists.return_value = {}

        deduplicator = Deduplicator(mock_cache_repository)
        deduplicator.deduplicate(sample_articles)

        # URL重複排除後の2件のURLでbatch_existsが呼ばれる
        mock_cache_repository.batch_exists.assert_called_once()
        called_urls = mock_cache_repository.batch_exists.call_args[0][0]
        assert set(called_urls) == {
            "https://example.com/article1",
            "https://example.com/article2",
        }
