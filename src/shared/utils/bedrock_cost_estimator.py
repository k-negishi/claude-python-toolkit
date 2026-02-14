"""Bedrockコスト推定ユーティリティ."""


def estimate_bedrock_cost_usd(
    article_count: int,
    *,
    avg_input_tokens: int = 900,
    avg_output_tokens: int = 140,
    input_cost_per_million: float = 1.0,
    output_cost_per_million: float = 5.0,
) -> float:
    """記事判定件数からBedrockコスト（USD）を推定する.

    デフォルト単価はClaude Haiku 4.5の価格（2026年2月時点）:
    - Input: $1.00 / 1M tokens
    - Output: $5.00 / 1M tokens

    Args:
        article_count: 判定記事件数
        avg_input_tokens: 1記事あたり平均入力トークン数（デフォルト: 900）
        avg_output_tokens: 1記事あたり平均出力トークン数（デフォルト: 140）
        input_cost_per_million: 入力トークン単価（USD/1M tokens、デフォルト: $1.00）
        output_cost_per_million: 出力トークン単価（USD/1M tokens、デフォルト: $5.00）

    Returns:
        推定コスト（USD）

    Raises:
        ValueError: 件数やトークン数、単価が負の場合
    """
    if article_count < 0:
        raise ValueError("article_count must be >= 0")
    if avg_input_tokens < 0:
        raise ValueError("avg_input_tokens must be >= 0")
    if avg_output_tokens < 0:
        raise ValueError("avg_output_tokens must be >= 0")
    if input_cost_per_million < 0:
        raise ValueError("input_cost_per_million must be >= 0")
    if output_cost_per_million < 0:
        raise ValueError("output_cost_per_million must be >= 0")

    input_cost = (article_count * avg_input_tokens * input_cost_per_million) / 1_000_000
    output_cost = (article_count * avg_output_tokens * output_cost_per_million) / 1_000_000
    return input_cost + output_cost
