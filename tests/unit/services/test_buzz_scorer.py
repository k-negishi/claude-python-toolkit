"""BuzzScorerサービスのユニットテスト."""

from datetime import datetime, timedelta, timezone

import pytest

from src.models.article import Article
from src.services.buzz_scorer import BuzzScorer


class TestBuzzScorer:
    """BuzzScorerクラスのテスト."""

    @pytest.fixture
    def buzz_scorer(self) -> BuzzScorer:
        """BuzzScorerインスタンスを返す."""
        return BuzzScorer()

    @pytest.fixture
    def sample_article(self) -> Article:
        """サンプル記事を返す."""
        return Article(
            url="https://example.com/article",
            title="Test Article",
            published_at=datetime.now(timezone.utc),
            source_name="Test Source",
            description="Test description",
            normalized_url="https://example.com/article",
            collected_at=datetime.now(timezone.utc),
        )

    def test_calculate_source_count_score(self, buzz_scorer: BuzzScorer) -> None:
        """ソース出現スコアが正しく計算されることを確認."""
        url_counts = {"https://example.com/article": 3}

        score = buzz_scorer._calculate_source_count_score("https://example.com/article", url_counts)

        # 3 * 20 = 60
        assert score == 60.0

    def test_calculate_source_count_score_max(self, buzz_scorer: BuzzScorer) -> None:
        """ソース出現スコアが100を超えないことを確認."""
        url_counts = {"https://example.com/article": 10}

        score = buzz_scorer._calculate_source_count_score("https://example.com/article", url_counts)

        # min(10 * 20, 100) = 100
        assert score == 100.0

    def test_calculate_recency_score_new(self, buzz_scorer: BuzzScorer) -> None:
        """新しい記事の鮮度スコアが高いことを確認."""
        # 今日の記事
        article = Article(
            url="https://example.com/article",
            title="Test",
            published_at=datetime.now(timezone.utc),
            source_name="Test",
            description="Test",
            normalized_url="https://example.com/article",
            collected_at=datetime.now(timezone.utc),
        )

        score = buzz_scorer._calculate_recency_score(article)

        # days_old = 0, score = 100 - (0 * 10) = 100
        assert score == 100.0

    def test_calculate_recency_score_old(self, buzz_scorer: BuzzScorer) -> None:
        """古い記事の鮮度スコアが低いことを確認."""
        # 5日前の記事
        article = Article(
            url="https://example.com/article",
            title="Test",
            published_at=datetime.now(timezone.utc) - timedelta(days=5),
            source_name="Test",
            description="Test",
            normalized_url="https://example.com/article",
            collected_at=datetime.now(timezone.utc),
        )

        score = buzz_scorer._calculate_recency_score(article)

        # days_old = 5, score = 100 - (5 * 10) = 50
        assert score == 50.0

    def test_calculate_recency_score_min(self, buzz_scorer: BuzzScorer) -> None:
        """鮮度スコアが0を下回らないことを確認."""
        # 20日前の記事
        article = Article(
            url="https://example.com/article",
            title="Test",
            published_at=datetime.now(timezone.utc) - timedelta(days=20),
            source_name="Test",
            description="Test",
            normalized_url="https://example.com/article",
            collected_at=datetime.now(timezone.utc),
        )

        score = buzz_scorer._calculate_recency_score(article)

        # max(100 - (20 * 10), 0) = 0
        assert score == 0.0

    def test_calculate_domain_diversity_score(self, buzz_scorer: BuzzScorer) -> None:
        """ドメイン多様性スコアが正しく計算されることを確認."""
        domain_counts = {"example.com": 3}

        score = buzz_scorer._calculate_domain_diversity_score(
            "https://example.com/article", domain_counts
        )

        # 100 - (3 * 5) = 85
        assert score == 85.0

    def test_calculate_total_score(self, buzz_scorer: BuzzScorer) -> None:
        """総合スコアが正しく計算されることを確認."""
        source_score = 60.0
        recency_score = 80.0
        diversity_score = 90.0

        total = buzz_scorer._calculate_total_score(source_score, recency_score, diversity_score)

        # (60 * 0.4) + (80 * 0.5) + (90 * 0.1) = 24 + 40 + 9 = 73
        assert total == 73.0

    def test_calculate_scores(self, buzz_scorer: BuzzScorer, sample_article: Article) -> None:
        """全記事のスコアが計算されることを確認."""
        articles = [sample_article]

        scores = buzz_scorer.calculate_scores(articles)

        assert len(scores) == 1
        assert sample_article.normalized_url in scores

        score = scores[sample_article.normalized_url]
        assert score.url == sample_article.url
        assert score.source_count == 1
        assert 0.0 <= score.total_score <= 100.0
