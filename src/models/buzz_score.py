"""Buzzスコアエンティティモジュール."""

from dataclasses import dataclass


@dataclass
class BuzzScore:
    """話題性スコア（非LLM計算）.

    記事の話題性を定量化したスコア.

    Attributes:
        url: 記事URL
        source_count: 複数ソース出現回数（1以上）
        recency_score: 鮮度スコア（0-100）
        domain_diversity_score: ドメイン多様性スコア（0-100）
        total_score: 総合Buzzスコア（0-100）
    """

    url: str
    source_count: int
    recency_score: float
    domain_diversity_score: float
    total_score: float
