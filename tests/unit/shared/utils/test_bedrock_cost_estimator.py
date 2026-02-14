"""Bedrockコスト推定ユーティリティのテスト."""

import pytest

from src.shared.utils.bedrock_cost_estimator import estimate_bedrock_cost_usd


@pytest.mark.parametrize(
    ("article_count", "expected"),
    [
        (30, 0.048),  # Claude Haiku 4.5: (30*900*1.0 + 30*140*5.0)/1M = 0.048
        (60, 0.096),  # (60*900*1.0 + 60*140*5.0)/1M = 0.096
        (90, 0.144),  # (90*900*1.0 + 90*140*5.0)/1M = 0.144
        (120, 0.192), # (120*900*1.0 + 120*140*5.0)/1M = 0.192
        (150, 0.24),  # (150*900*1.0 + 150*140*5.0)/1M = 0.24
    ],
)
def test_estimate_bedrock_cost_usd_default_profile(article_count: int, expected: float) -> None:
    """デフォルト単価・トークン前提で件数別コストを算出できることを確認."""
    cost = estimate_bedrock_cost_usd(article_count)

    assert cost == pytest.approx(expected, rel=1e-9)


def test_estimate_bedrock_cost_usd_supports_custom_pricing_and_tokens() -> None:
    """単価・トークン前提を上書きできることを確認."""
    cost = estimate_bedrock_cost_usd(
        article_count=100,
        avg_input_tokens=800,
        avg_output_tokens=100,
        input_cost_per_million=3.0,
        output_cost_per_million=15.0,
    )

    # (100*800*3 + 100*100*15) / 1_000_000 = 0.39
    assert cost == pytest.approx(0.39, rel=1e-9)


@pytest.mark.parametrize("article_count", [-1, -10])
def test_estimate_bedrock_cost_usd_raises_for_negative_article_count(article_count: int) -> None:
    """件数が負の場合は ValueError になることを確認."""
    with pytest.raises(ValueError, match="article_count"):
        estimate_bedrock_cost_usd(article_count)
