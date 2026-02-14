"""MultiSourceSocialProofFetcherのユニットテスト."""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch

from src.services.social_proof.multi_source_social_proof_fetcher import (
    MultiSourceSocialProofFetcher,
)
from src.models.article import Article


def create_test_article(url: str) -> Article:
    """テスト用の記事を作成する."""
    return Article(
        url=url,
        title="Test Article",
        published_at=datetime(2025, 1, 1, 0, 0, 0),
        source_name="test",
        description="test description",
        normalized_url=url,
        collected_at=datetime(2025, 1, 1, 0, 0, 0),
    )


class TestMultiSourceSocialProofFetcher:
    """MultiSourceSocialProofFetcherクラスのテスト."""

    @pytest.mark.asyncio
    async def test_fetch_batch_all_signals_success(self):
        """4指標すべて取得成功時の統合スコア計算."""
        fetcher = MultiSourceSocialProofFetcher()

        articles = [create_test_article("https://example.com/article1")]

        # モック: 各Fetcherが正常にスコアを返す
        # Y=100, H=50, Z=60, Q=70
        mock_yamadashy = AsyncMock()
        mock_yamadashy.fetch_signals = AsyncMock(
            return_value={"https://example.com/article1": 100}
        )

        mock_hatena = AsyncMock()
        mock_hatena.fetch_batch = AsyncMock(
            return_value={"https://example.com/article1": 50.0}
        )

        mock_zenn = AsyncMock()
        mock_zenn.fetch_batch = AsyncMock(
            return_value={"https://example.com/article1": 60.0}
        )

        mock_qiita = AsyncMock()
        mock_qiita.fetch_batch = AsyncMock(
            return_value={"https://example.com/article1": 70.0}
        )

        with patch.object(fetcher, "_yamadashy_fetcher", mock_yamadashy), \
             patch.object(fetcher, "_hatena_fetcher", mock_hatena), \
             patch.object(fetcher, "_zenn_fetcher", mock_zenn), \
             patch.object(fetcher, "_qiita_fetcher", mock_qiita):

            result = await fetcher.fetch_batch(articles)

        # 統合スコア: S = (0.05*100 + 0.45*50 + 0.35*60 + 0.15*70) / 1.0
        # S = (5 + 22.5 + 21 + 10.5) / 1.0 = 59.0
        assert len(result) == 1
        assert 58.5 <= result["https://example.com/article1"] <= 59.5

    @pytest.mark.asyncio
    async def test_fetch_batch_one_signal_missing(self):
        """1指標がスコア0の場合も正しく統合計算に含める."""
        fetcher = MultiSourceSocialProofFetcher()

        articles = [create_test_article("https://example.com/article1")]

        # モック: Zennのみスコア0
        # Y=100, H=50, Z=0, Q=70
        mock_yamadashy = AsyncMock()
        mock_yamadashy.fetch_signals = AsyncMock(
            return_value={"https://example.com/article1": 100}
        )

        mock_hatena = AsyncMock()
        mock_hatena.fetch_batch = AsyncMock(
            return_value={"https://example.com/article1": 50.0}
        )

        mock_zenn = AsyncMock()
        mock_zenn.fetch_batch = AsyncMock(
            return_value={"https://example.com/article1": 0.0}  # スコア0
        )

        mock_qiita = AsyncMock()
        mock_qiita.fetch_batch = AsyncMock(
            return_value={"https://example.com/article1": 70.0}
        )

        with patch.object(fetcher, "_yamadashy_fetcher", mock_yamadashy), \
             patch.object(fetcher, "_hatena_fetcher", mock_hatena), \
             patch.object(fetcher, "_zenn_fetcher", mock_zenn), \
             patch.object(fetcher, "_qiita_fetcher", mock_qiita):

            result = await fetcher.fetch_batch(articles)

        # 統合スコア（Zenn=0も含める）: S = (0.05*100 + 0.45*50 + 0.35*0 + 0.15*70) / 1.0
        # S = (5 + 22.5 + 0 + 10.5) / 1.0 = 38.0
        assert len(result) == 1
        assert 37.5 <= result["https://example.com/article1"] <= 38.5

    @pytest.mark.asyncio
    async def test_fetch_batch_all_signals_zero(self):
        """全指標がスコア0の場合は統合スコアも0."""
        fetcher = MultiSourceSocialProofFetcher()

        articles = [create_test_article("https://example.com/article1")]

        # モック: 全てスコア0
        mock_yamadashy = AsyncMock()
        mock_yamadashy.fetch_signals = AsyncMock(
            return_value={"https://example.com/article1": 0}
        )

        mock_hatena = AsyncMock()
        mock_hatena.fetch_batch = AsyncMock(
            return_value={"https://example.com/article1": 0.0}
        )

        mock_zenn = AsyncMock()
        mock_zenn.fetch_batch = AsyncMock(
            return_value={"https://example.com/article1": 0.0}
        )

        mock_qiita = AsyncMock()
        mock_qiita.fetch_batch = AsyncMock(
            return_value={"https://example.com/article1": 0.0}
        )

        with patch.object(fetcher, "_yamadashy_fetcher", mock_yamadashy), \
             patch.object(fetcher, "_hatena_fetcher", mock_hatena), \
             patch.object(fetcher, "_zenn_fetcher", mock_zenn), \
             patch.object(fetcher, "_qiita_fetcher", mock_qiita):

            result = await fetcher.fetch_batch(articles)

        # 統合スコア: S = (0.05*0 + 0.45*0 + 0.35*0 + 0.15*0) / 1.0 = 0.0
        assert len(result) == 1
        assert result["https://example.com/article1"] == 0.0

    @pytest.mark.asyncio
    async def test_weight_distribution(self):
        """重み配分の検証（Y=0.05, H=0.45, Z=0.35, Q=0.15）."""
        fetcher = MultiSourceSocialProofFetcher()

        articles = [create_test_article("https://example.com/article1")]

        # モック: 全て100点
        mock_yamadashy = AsyncMock()
        mock_yamadashy.fetch_signals = AsyncMock(
            return_value={"https://example.com/article1": 100}
        )

        mock_hatena = AsyncMock()
        mock_hatena.fetch_batch = AsyncMock(
            return_value={"https://example.com/article1": 100.0}
        )

        mock_zenn = AsyncMock()
        mock_zenn.fetch_batch = AsyncMock(
            return_value={"https://example.com/article1": 100.0}
        )

        mock_qiita = AsyncMock()
        mock_qiita.fetch_batch = AsyncMock(
            return_value={"https://example.com/article1": 100.0}
        )

        with patch.object(fetcher, "_yamadashy_fetcher", mock_yamadashy), \
             patch.object(fetcher, "_hatena_fetcher", mock_hatena), \
             patch.object(fetcher, "_zenn_fetcher", mock_zenn), \
             patch.object(fetcher, "_qiita_fetcher", mock_qiita):

            result = await fetcher.fetch_batch(articles)

        # 全て100点の場合、統合スコアも100点
        assert result["https://example.com/article1"] == 100.0

    @pytest.mark.asyncio
    async def test_empty_articles(self):
        """空の記事リストで空の辞書が返される."""
        fetcher = MultiSourceSocialProofFetcher()

        result = await fetcher.fetch_batch([])

        assert result == {}

    @pytest.mark.asyncio
    async def test_score_zero_treated_as_data(self):
        """スコア0が欠損ではなくデータとして扱われることを検証.

        はてぶ0件、Zenn圏外、YAMADASHY未掲載のQiita記事を想定。
        修正前: スコア0が分母から除外され、(0.15*50) / 0.15 = 50 となり不当に高評価
        修正後: スコア0も含めて統合され、(0.05*0 + 0.45*0 + 0.35*0 + 0.15*50) / 1.0 = 7.5 となり正しく低評価
        """
        fetcher = MultiSourceSocialProofFetcher()

        articles = [create_test_article("https://qiita.com/example")]

        # モック: Qiitaのみスコアあり、他は全て0
        # Y=0, H=0, Z=0, Q=50
        mock_yamadashy = AsyncMock()
        mock_yamadashy.fetch_signals = AsyncMock(
            return_value={"https://qiita.com/example": 0}
        )

        mock_hatena = AsyncMock()
        mock_hatena.fetch_batch = AsyncMock(
            return_value={"https://qiita.com/example": 0.0}
        )

        mock_zenn = AsyncMock()
        mock_zenn.fetch_batch = AsyncMock(
            return_value={"https://qiita.com/example": 0.0}
        )

        mock_qiita = AsyncMock()
        mock_qiita.fetch_batch = AsyncMock(
            return_value={"https://qiita.com/example": 50.0}
        )

        with patch.object(fetcher, "_yamadashy_fetcher", mock_yamadashy), \
             patch.object(fetcher, "_hatena_fetcher", mock_hatena), \
             patch.object(fetcher, "_zenn_fetcher", mock_zenn), \
             patch.object(fetcher, "_qiita_fetcher", mock_qiita):

            result = await fetcher.fetch_batch(articles)

        # 修正後の期待値: S = (0.05*0 + 0.45*0 + 0.35*0 + 0.15*50) / 1.0 = 7.5
        assert len(result) == 1
        assert 7.0 <= result["https://qiita.com/example"] <= 8.0
