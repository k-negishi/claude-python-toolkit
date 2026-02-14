"""InterestProfileモデルのユニットテスト."""

import pytest

from src.models.interest_profile import InterestProfile, JudgmentCriterion


def test_interest_profile_initialization() -> None:
    """InterestProfileの初期化テスト."""
    # Arrange
    criteria = {
        "act_now": JudgmentCriterion(
            label="ACT_NOW", description="今すぐ読むべき", examples=["例1", "例2"]
        )
    }

    # Act
    profile = InterestProfile(
        summary="テストプロファイル",
        high_interest=["AI/ML", "クラウド"],
        medium_interest=["フロントエンド"],
        low_priority=["初心者向け"],
        criteria=criteria,
    )

    # Assert
    assert profile.summary == "テストプロファイル"
    assert profile.high_interest == ["AI/ML", "クラウド"]
    assert profile.medium_interest == ["フロントエンド"]
    assert profile.low_priority == ["初心者向け"]
    assert "act_now" in profile.criteria


def test_format_for_prompt() -> None:
    """format_for_prompt()メソッドのテスト."""
    # Arrange
    profile = InterestProfile(
        summary="プリンシパルエンジニアとして活動",
        high_interest=["AI/ML", "クラウドインフラ"],
        medium_interest=["データベース"],
        low_priority=["チュートリアル"],
        criteria={},
    )

    # Act
    result = profile.format_for_prompt()

    # Assert
    assert "プリンシパルエンジニアとして活動" in result
    assert "**強い関心を持つトピック**:" in result
    assert "- AI/ML" in result
    assert "- クラウドインフラ" in result
    assert "**中程度の関心を持つトピック**:" in result
    assert "- データベース" in result
    assert "**低優先度のトピック**:" in result
    assert "- チュートリアル" in result


def test_format_for_prompt_with_empty_lists() -> None:
    """空リストの場合のformat_for_prompt()テスト."""
    # Arrange
    profile = InterestProfile(
        summary="サマリのみ",
        high_interest=[],
        medium_interest=[],
        low_priority=[],
        criteria={},
    )

    # Act
    result = profile.format_for_prompt()

    # Assert
    assert result == "サマリのみ"
    assert "**強い関心を持つトピック**:" not in result
    assert "**中程度の関心を持つトピック**:" not in result
    assert "**低優先度のトピック**:" not in result


def test_format_criteria_for_prompt() -> None:
    """format_criteria_for_prompt()メソッドのテスト."""
    # Arrange
    criteria = {
        "act_now": JudgmentCriterion(
            label="ACT_NOW",
            description="今すぐ読むべき記事",
            examples=["セキュリティ脆弱性", "重要な技術変更"],
        ),
        "think": JudgmentCriterion(
            label="THINK", description="設計判断に役立つ記事", examples=["アーキテクチャパターン"]
        ),
        "fyi": JudgmentCriterion(label="FYI", description="知っておくとよい記事", examples=[]),
        "ignore": JudgmentCriterion(label="IGNORE", description="関心外の記事", examples=[]),
    }

    profile = InterestProfile(
        summary="テスト",
        high_interest=[],
        medium_interest=[],
        low_priority=[],
        criteria=criteria,
    )

    # Act
    result = profile.format_criteria_for_prompt()

    # Assert
    assert "- **ACT_NOW**: 今すぐ読むべき記事" in result
    assert "- セキュリティ脆弱性" in result
    assert "- 重要な技術変更" in result
    assert "- **THINK**: 設計判断に役立つ記事" in result
    assert "- アーキテクチャパターン" in result
    assert "- **FYI**: 知っておくとよい記事" in result
    assert "- **IGNORE**: 関心外の記事" in result

    # 順序確認（act_now → think → fyi → ignore）
    lines = result.split("\n")
    act_now_index = next(i for i, line in enumerate(lines) if "ACT_NOW" in line)
    think_index = next(i for i, line in enumerate(lines) if "THINK" in line)
    fyi_index = next(i for i, line in enumerate(lines) if "FYI" in line)
    ignore_index = next(i for i, line in enumerate(lines) if "IGNORE" in line)

    assert act_now_index < think_index < fyi_index < ignore_index
