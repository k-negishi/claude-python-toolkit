"""Buzzスコア計算サービスモジュール."""

from collections import Counter
from urllib.parse import urlparse

from src.models.article import Article
from src.models.buzz_score import BuzzScore
from src.shared.logging.logger import get_logger
from src.shared.utils.date_utils import now_utc

logger = get_logger(__name__)


class BuzzScorer:
    """Buzzスコア計算サービス.

    記事の話題性を複数の指標から算出する（非LLM）.

    スコア計算式:
    - source_count_score = min(source_count * 20, 100)
    - recency_score = max(100 - (days_old * 10), 0)
    - domain_diversity_score = max(100 - (same_domain_count * 5), 0)
    - total_score = (source_count * 0.4) + (recency * 0.5) + (diversity * 0.1)
    """

    def calculate_scores(self, articles: list[Article]) -> dict[str, BuzzScore]:
        """全記事のBuzzスコアを計算する.

        Args:
            articles: 重複排除済み記事のリスト

        Returns:
            スコア辞書（normalized_url -> BuzzScore）
        """
        logger.info("buzz_scoring_start", article_count=len(articles))

        # 前処理: URL出現回数とドメイン出現回数を集計
        url_counts: dict[str, int] = Counter(article.normalized_url for article in articles)
        domain_counts: dict[str, int] = Counter(
            urlparse(article.normalized_url).netloc for article in articles
        )

        # 各記事のスコアを計算
        scores: dict[str, BuzzScore] = {}

        for article in articles:
            source_count = url_counts.get(article.normalized_url, 1)
            source_count_score = self._calculate_source_count_score(
                article.normalized_url, url_counts
            )
            recency_score = self._calculate_recency_score(article)
            domain_diversity_score = self._calculate_domain_diversity_score(
                article.normalized_url, domain_counts
            )
            total_score = self._calculate_total_score(
                source_count_score, recency_score, domain_diversity_score
            )

            buzz_score = BuzzScore(
                url=article.url,
                source_count=source_count,
                recency_score=recency_score,
                domain_diversity_score=domain_diversity_score,
                total_score=total_score,
            )

            scores[article.normalized_url] = buzz_score

            logger.debug(
                "buzz_score_calculated",
                url=article.url,
                total_score=total_score,
            )

        logger.info("buzz_scoring_complete", score_count=len(scores))

        return scores

    def _calculate_source_count_score(
        self, normalized_url: str, url_counts: dict[str, int]
    ) -> float:
        """複数ソース出現スコアを計算する.

        同一URLが複数のソースに出現するほどスコアが高い.

        Args:
            normalized_url: 正規化URL
            url_counts: URL出現回数の辞書

        Returns:
            スコア（0-100）
        """
        source_count = url_counts.get(normalized_url, 1)
        return min(source_count * 20.0, 100.0)

    def _calculate_recency_score(self, article: Article) -> float:
        """鮮度スコアを計算する.

        公開日時が新しいほどスコアが高い.

        Args:
            article: 記事

        Returns:
            スコア（0-100）
        """
        now = now_utc()
        days_old = (now - article.published_at).days
        return max(100.0 - (days_old * 10.0), 0.0)

    def _calculate_domain_diversity_score(
        self, normalized_url: str, domain_counts: dict[str, int]
    ) -> float:
        """ドメイン多様性スコアを計算する.

        同一ドメインの記事が少ないほどスコアが高い.

        Args:
            normalized_url: 正規化URL
            domain_counts: ドメイン出現回数の辞書

        Returns:
            スコア（0-100）
        """
        domain = urlparse(normalized_url).netloc
        same_domain_count = domain_counts.get(domain, 1)
        return max(100.0 - (same_domain_count * 5.0), 0.0)

    def _calculate_total_score(
        self, source_count_score: float, recency_score: float, diversity_score: float
    ) -> float:
        """総合Buzzスコアを計算する.

        重み付け合計:
        - source_count_score: 40%
        - recency_score: 50%
        - diversity_score: 10%

        Args:
            source_count_score: ソース出現スコア
            recency_score: 鮮度スコア
            diversity_score: ドメイン多様性スコア

        Returns:
            総合スコア（0-100）
        """
        return (source_count_score * 0.4) + (recency_score * 0.5) + (diversity_score * 0.1)
