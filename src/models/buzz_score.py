"""Buzzスコアエンティティモジュール."""

from dataclasses import dataclass


@dataclass
class BuzzScore:
    """話題性スコア（非LLM計算）.

    記事の話題性を5つの要素から定量化したスコア.

    Attributes:
        url: 記事URL
        # 各要素のスコア（0-100）
        recency_score: 鮮度スコア
        consensus_score: 複数ソース出現スコア
        social_proof_score: 外部反応スコア（はてブ数など）
        interest_score: 興味との一致度スコア
        authority_score: 公式補正スコア
        # メタデータ
        source_count: 複数ソース出現回数（Consensus計算の元データ）
        social_proof_count: 外部反応数（はてブ数）
        # 総合スコア
        total_score: 総合Buzzスコア（0-100）
    """

    url: str
    # 各要素スコア
    recency_score: float
    consensus_score: float
    social_proof_score: float
    interest_score: float
    authority_score: float
    # メタデータ
    source_count: int
    social_proof_count: int
    # 総合スコア
    total_score: float
