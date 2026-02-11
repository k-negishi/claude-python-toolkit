"""URL正規化ユーティリティのユニットテスト."""

import pytest

from src.shared.utils.url_normalizer import normalize_url


class TestNormalizeUrl:
    """normalize_url関数のテスト."""

    def test_preserves_non_tracking_query_parameters(self) -> None:
        """トラッキング以外のクエリパラメータが保持されることを確認."""
        url = "https://example.com/article?foo=bar&baz=qux"
        result = normalize_url(url)
        # トラッキングパラメータでない場合は保持される
        assert "example.com/article" in result
        assert "foo=bar" in result or "baz=qux" in result

    def test_removes_utm_parameters(self) -> None:
        """utm_*パラメータが除去されることを確認."""
        url = "https://example.com/article?utm_source=twitter&utm_medium=social"
        result = normalize_url(url)
        assert result == "https://example.com/article"

    def test_unifies_scheme_to_https(self) -> None:
        """スキームがhttpsに統一されることを確認."""
        url = "http://example.com/article"
        result = normalize_url(url)
        assert result == "https://example.com/article"

    def test_removes_trailing_slash(self) -> None:
        """トレーリングスラッシュが除去されることを確認."""
        url = "https://example.com/article/"
        result = normalize_url(url)
        assert result == "https://example.com/article"

    def test_handles_complex_url(self) -> None:
        """複雑なURLが正しく正規化されることを確認."""
        url = "http://example.com/article/?foo=bar&utm_campaign=test#section"
        result = normalize_url(url)
        # スキームがhttpsに、トレーリングスラッシュとフラグメントが除去、utm_*が除去
        assert result.startswith("https://example.com/article")
        assert "utm_campaign" not in result
        assert "#section" not in result
        # 非トラッキングパラメータは保持される
        assert "foo=bar" in result

    def test_preserves_path(self) -> None:
        """パスが保持されることを確認."""
        url = "https://example.com/blog/2024/01/article"
        result = normalize_url(url)
        assert result == "https://example.com/blog/2024/01/article"

    def test_handles_empty_path(self) -> None:
        """パスが空の場合を処理できることを確認."""
        url = "https://example.com"
        result = normalize_url(url)
        assert result == "https://example.com"

    def test_handles_fragment(self) -> None:
        """フラグメントが除去されることを確認."""
        url = "https://example.com/article#section1"
        result = normalize_url(url)
        assert result == "https://example.com/article"
