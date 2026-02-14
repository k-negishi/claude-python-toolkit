"""BuzzScorerサービスのユニットテスト（5要素統合版）."""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, Mock

import pytest

from src.models.article import Article
from src.models.interest_profile import InterestProfile, JudgmentCriterion
from src.models.source_config import AuthorityLevel, FeedType, Priority, SourceConfig
from src.repositories.source_master import SourceMaster
from src.services.buzz_scorer import BuzzScorer
from src.services.social_proof_fetcher import SocialProofFetcher


class TestBuzzScorer:
    """BuzzScorerクラスのテスト（5要素統合版）."""

    @pytest.fixture
    def interest_profile(self) -> InterestProfile:
        """テスト用InterestProfileを返す."""
        return InterestProfile(
            summary="テスト用プロファイル",
            high_interest=["AI/ML（大規模言語モデル、機械学習基盤）", "Kubernetes"],
            medium_interest=["PostgreSQL", "Terraform"],
            low_priority=["JavaScript", "React"],
            criteria={
                "act_now": JudgmentCriterion(
                    label="ACT_NOW", description="Test", examples=[]
                ),
                "think": JudgmentCriterion(label="THINK", description="Test", examples=[]),
                "fyi": JudgmentCriterion(label="FYI", description="Test", examples=[]),
                "ignore": JudgmentCriterion(label="IGNORE", description="Test", examples=[]),
            },
        )

    @pytest.fixture
    def source_master(self) -> SourceMaster:
        """テスト用SourceMasterを返す（モック）."""
        mock_master = Mock(spec=SourceMaster)
        mock_master.get_all_sources.return_value = [
            SourceConfig(
                source_id="test_official",
                name="Test Official",
                feed_url="https://example.com/feed",
                feed_type=FeedType.RSS,
                priority=Priority.HIGH,
                authority_level=AuthorityLevel.OFFICIAL,
            ),
            SourceConfig(
                source_id="test_high",
                name="Test High",
                feed_url="https://example.com/feed",
                feed_type=FeedType.RSS,
                priority=Priority.MEDIUM,
                authority_level=AuthorityLevel.HIGH,
            ),
            SourceConfig(
                source_id="test_medium",
                name="Test Medium",
                feed_url="https://example.com/feed",
                feed_type=FeedType.RSS,
                priority=Priority.MEDIUM,
                authority_level=AuthorityLevel.MEDIUM,
            ),
            SourceConfig(
                source_id="test_low",
                name="Test Low",
                feed_url="https://example.com/feed",
                feed_type=FeedType.RSS,
                priority=Priority.LOW,
                authority_level=AuthorityLevel.LOW,
            ),
        ]
        return mock_master

    @pytest.fixture
    def social_proof_fetcher(self) -> SocialProofFetcher:
        """テスト用SocialProofFetcherを返す（モック）."""
        mock_fetcher = Mock(spec=SocialProofFetcher)
        mock_fetcher.fetch_batch = AsyncMock(return_value={})
        return mock_fetcher

    @pytest.fixture
    def buzz_scorer(
        self,
        interest_profile: InterestProfile,
        source_master: SourceMaster,
        social_proof_fetcher: SocialProofFetcher,
    ) -> BuzzScorer:
        """BuzzScorerインスタンスを返す."""
        return BuzzScorer(interest_profile, source_master, social_proof_fetcher)

    @pytest.fixture
    def sample_article(self) -> Article:
        """サンプル記事を返す."""
        return Article(
            url="https://example.com/article",
            title="Test Article",
            published_at=datetime.now(timezone.utc),
            source_name="Test Medium",
            description="Test description",
            normalized_url="https://example.com/article",
            collected_at=datetime.now(timezone.utc),
        )

    def test_calculate_recency_score_new(self, buzz_scorer: BuzzScorer) -> None:
        """新しい記事の鮮度スコアが高いことを確認."""
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

    def test_calculate_consensus_score(self, buzz_scorer: BuzzScorer) -> None:
        """Consensusスコアが正しく計算されることを確認."""
        url_counts = {"https://example.com/article": 3}

        score = buzz_scorer._calculate_consensus_score("https://example.com/article", url_counts)

        # 3 * 20 = 60
        assert score == 60.0

    def test_calculate_consensus_score_max(self, buzz_scorer: BuzzScorer) -> None:
        """Consensusスコアが100を超えないことを確認."""
        url_counts = {"https://example.com/article": 10}

        score = buzz_scorer._calculate_consensus_score("https://example.com/article", url_counts)

        # min(10 * 20, 100) = 100
        assert score == 100.0

    def test_calculate_social_proof_score_zero(self, buzz_scorer: BuzzScorer) -> None:
        """SocialProofスコア: 0件の場合."""
        social_proof_counts = {"https://example.com/article": 0}

        score = buzz_scorer._calculate_social_proof_score(
            "https://example.com/article", social_proof_counts
        )

        assert score == 0.0

    def test_calculate_social_proof_score_low(self, buzz_scorer: BuzzScorer) -> None:
        """SocialProofスコア: 1-9件の場合."""
        social_proof_counts = {"https://example.com/article": 5}

        score = buzz_scorer._calculate_social_proof_score(
            "https://example.com/article", social_proof_counts
        )

        assert score == 20.0

    def test_calculate_social_proof_score_medium(self, buzz_scorer: BuzzScorer) -> None:
        """SocialProofスコア: 10-49件の場合."""
        social_proof_counts = {"https://example.com/article": 30}

        score = buzz_scorer._calculate_social_proof_score(
            "https://example.com/article", social_proof_counts
        )

        assert score == 50.0

    def test_calculate_social_proof_score_high(self, buzz_scorer: BuzzScorer) -> None:
        """SocialProofスコア: 50-99件の場合."""
        social_proof_counts = {"https://example.com/article": 75}

        score = buzz_scorer._calculate_social_proof_score(
            "https://example.com/article", social_proof_counts
        )

        assert score == 70.0

    def test_calculate_social_proof_score_max(self, buzz_scorer: BuzzScorer) -> None:
        """SocialProofスコア: 100件以上の場合."""
        social_proof_counts = {"https://example.com/article": 150}

        score = buzz_scorer._calculate_social_proof_score(
            "https://example.com/article", social_proof_counts
        )

        assert score == 100.0

    def test_calculate_interest_score_high(self, buzz_scorer: BuzzScorer) -> None:
        """Interestスコア: high_interest一致時に100点."""
        article = Article(
            url="https://example.com/article",
            title="大規模言語モデルの最新動向",
            published_at=datetime.now(timezone.utc),
            source_name="Test",
            description="LLMについての記事",
            normalized_url="https://example.com/article",
            collected_at=datetime.now(timezone.utc),
        )

        score = buzz_scorer._calculate_interest_score(article)

        assert score == 100.0

    def test_calculate_interest_score_medium(self, buzz_scorer: BuzzScorer) -> None:
        """Interestスコア: medium_interest一致時に60点."""
        article = Article(
            url="https://example.com/article",
            title="PostgreSQLのパフォーマンスチューニング",
            published_at=datetime.now(timezone.utc),
            source_name="Test",
            description="PostgreSQLについて",
            normalized_url="https://example.com/article",
            collected_at=datetime.now(timezone.utc),
        )

        score = buzz_scorer._calculate_interest_score(article)

        assert score == 60.0

    def test_calculate_interest_score_low(self, buzz_scorer: BuzzScorer) -> None:
        """Interestスコア: low_priority一致時に20点."""
        article = Article(
            url="https://example.com/article",
            title="React 19の新機能",
            published_at=datetime.now(timezone.utc),
            source_name="Test",
            description="Reactについて",
            normalized_url="https://example.com/article",
            collected_at=datetime.now(timezone.utc),
        )

        score = buzz_scorer._calculate_interest_score(article)

        assert score == 20.0

    def test_calculate_interest_score_default(self, buzz_scorer: BuzzScorer) -> None:
        """Interestスコア: いずれにも一致しない場合は40点."""
        article = Article(
            url="https://example.com/article",
            title="Unrelated topic",
            published_at=datetime.now(timezone.utc),
            source_name="Test",
            description="Some other topic",
            normalized_url="https://example.com/article",
            collected_at=datetime.now(timezone.utc),
        )

        score = buzz_scorer._calculate_interest_score(article)

        assert score == 40.0

    def test_match_topic_main_keyword(self, buzz_scorer: BuzzScorer) -> None:
        """_match_topic: メインキーワードが一致する場合."""
        topic = "Kubernetes（コンテナ、オーケストレーション）"
        text = "kubernetesでデプロイする"

        assert buzz_scorer._match_topic(topic, text) is True

    def test_match_topic_sub_keyword(self, buzz_scorer: BuzzScorer) -> None:
        """_match_topic: サブキーワードが一致する場合."""
        topic = "AI/ML（大規模言語モデル、機械学習基盤）"
        text = "大規模言語モデルの最新動向"

        assert buzz_scorer._match_topic(topic, text) is True

    def test_match_topic_no_match(self, buzz_scorer: BuzzScorer) -> None:
        """_match_topic: 一致しない場合."""
        topic = "Kubernetes（コンテナ、オーケストレーション）"
        text = "全く無関係な内容"

        assert buzz_scorer._match_topic(topic, text) is False

    def test_calculate_authority_score_official(self, buzz_scorer: BuzzScorer) -> None:
        """Authorityスコア: OFFICIALの場合は100点."""
        score = buzz_scorer._calculate_authority_score("Test Official")

        assert score == 100.0

    def test_calculate_authority_score_high(self, buzz_scorer: BuzzScorer) -> None:
        """Authorityスコア: HIGHの場合は80点."""
        score = buzz_scorer._calculate_authority_score("Test High")

        assert score == 80.0

    def test_calculate_authority_score_medium(self, buzz_scorer: BuzzScorer) -> None:
        """Authorityスコア: MEDIUMの場合は50点."""
        score = buzz_scorer._calculate_authority_score("Test Medium")

        assert score == 50.0

    def test_calculate_authority_score_low(self, buzz_scorer: BuzzScorer) -> None:
        """Authorityスコア: LOWの場合は0点."""
        score = buzz_scorer._calculate_authority_score("Test Low")

        assert score == 0.0

    def test_calculate_authority_score_unknown(self, buzz_scorer: BuzzScorer) -> None:
        """Authorityスコア: 未知のソースの場合は0点."""
        score = buzz_scorer._calculate_authority_score("Unknown Source")

        assert score == 0.0

    def test_calculate_total_score(self, buzz_scorer: BuzzScorer) -> None:
        """総合スコアが正しく計算されることを確認（5要素）."""
        recency = 100.0
        consensus = 60.0
        social_proof = 50.0
        interest = 80.0
        authority = 100.0

        total = buzz_scorer._calculate_total_score(
            recency, consensus, social_proof, interest, authority
        )

        # (100 * 0.25) + (60 * 0.20) + (50 * 0.20) + (80 * 0.25) + (100 * 0.10)
        # = 25 + 12 + 10 + 20 + 10 = 77
        assert total == 77.0

    @pytest.mark.asyncio
    async def test_calculate_scores(
        self, buzz_scorer: BuzzScorer, sample_article: Article, social_proof_fetcher: Mock
    ) -> None:
        """全記事のスコアが計算されることを確認（非同期版）."""
        # SocialProofFetcherのモック設定
        social_proof_fetcher.fetch_batch.return_value = {
            "https://example.com/article": 25,
        }

        articles = [sample_article]

        scores = await buzz_scorer.calculate_scores(articles)

        assert len(scores) == 1
        assert sample_article.normalized_url in scores

        score = scores[sample_article.normalized_url]
        assert score.url == sample_article.url
        assert score.source_count == 1
        assert score.social_proof_count == 25
        assert 0.0 <= score.total_score <= 100.0
        assert 0.0 <= score.recency_score <= 100.0
        assert 0.0 <= score.consensus_score <= 100.0
        assert 0.0 <= score.social_proof_score <= 100.0
        assert 0.0 <= score.interest_score <= 100.0
        assert 0.0 <= score.authority_score <= 100.0
