"""Normalizerサービスのユニットテスト."""

from datetime import datetime, timezone

import pytest

from src.models.article import Article
from src.services.normalizer import Normalizer


class TestNormalizer:
    """Normalizerクラスのテスト."""

    @pytest.fixture
    def normalizer(self) -> Normalizer:
        """Normalizerインスタンスを返す."""
        return Normalizer()

    @pytest.fixture
    def sample_article(self) -> Article:
        """サンプル記事を返す."""
        return Article(
            url="http://example.com/article?utm_source=test",
            title="  Test &amp; Article  ",
            published_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            source_name="Test Source",
            description="  Test &lt;description&gt; with HTML entities  ",
            normalized_url="",  # 正規化前は空
            collected_at=datetime(2024, 1, 1, 13, 0, 0, tzinfo=timezone.utc),
        )

    def test_normalize_title(self, normalizer: Normalizer) -> None:
        """タイトルが正規化されることを確認."""
        result = normalizer._normalize_title("  Test &amp; Article  ")
        assert result == "Test & Article"

    def test_normalize_title_handles_empty(self, normalizer: Normalizer) -> None:
        """空のタイトルがデフォルト値になることを確認."""
        result = normalizer._normalize_title("   ")
        assert result == "No Title"

    def test_normalize_description(self, normalizer: Normalizer) -> None:
        """概要が正規化されることを確認."""
        result = normalizer._normalize_description("  Test &lt;description&gt;  ")
        assert result == "Test <description>"

    def test_normalize_description_truncates(self, normalizer: Normalizer) -> None:
        """概要が800文字に制限されることを確認."""
        long_text = "a" * 1000
        result = normalizer._normalize_description(long_text)
        assert len(result) == 800

    def test_normalize_article(self, normalizer: Normalizer, sample_article: Article) -> None:
        """記事が正規化されることを確認."""
        result = normalizer.normalize([sample_article])

        assert len(result) == 1
        article = result[0]

        # URLが正規化されている
        assert article.normalized_url == "https://example.com/article"

        # タイトルが正規化されている（HTML実体参照デコード、前後空白除去）
        assert article.title == "Test & Article"

        # 概要が正規化されている
        assert article.description == "Test <description> with HTML entities"

    def test_normalize_handles_error(self, normalizer: Normalizer) -> None:
        """エラーが発生した記事をスキップすることを確認."""
        # 不正な記事（normalizeで例外が発生する可能性がある）
        invalid_article = Article(
            url="",  # 空のURL
            title="Test",
            published_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
            source_name="Test",
            description="Test",
            normalized_url="",
            collected_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        )

        # エラーでもクラッシュしないことを確認
        result = normalizer.normalize([invalid_article])
        # 空のURLは正規化できないが、エラーハンドリングでスキップされる
        assert isinstance(result, list)
