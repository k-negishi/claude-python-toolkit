"""SocialProofFetcherのユニットテスト."""

import pytest
from unittest.mock import AsyncMock, patch
import httpx

from src.services.social_proof_fetcher import SocialProofFetcher


class TestSocialProofFetcher:
    """SocialProofFetcherクラスのテスト."""

    @pytest.mark.asyncio
    async def test_fetch_single_success(self):
        """_fetch_single: 正常レスポンスで正しい件数が返される."""
        fetcher = SocialProofFetcher(timeout=5)

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = AsyncMock()
            mock_response.text = "42"
            mock_response.raise_for_status = AsyncMock()

            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            count = await fetcher._fetch_single("https://example.com")

            assert count == 42

    @pytest.mark.asyncio
    async def test_fetch_single_timeout(self):
        """_fetch_single: タイムアウト発生時に0が返される."""
        fetcher = SocialProofFetcher(timeout=1)

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=httpx.TimeoutException("Timeout")
            )

            count = await fetcher._fetch_single("https://example.com")

            assert count == 0

    @pytest.mark.asyncio
    async def test_fetch_single_http_error(self):
        """_fetch_single: HTTPエラー時に0が返される."""
        fetcher = SocialProofFetcher(timeout=5)

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=httpx.HTTPStatusError(
                    "Error", request=AsyncMock(), response=AsyncMock()
                )
            )

            count = await fetcher._fetch_single("https://example.com")

            assert count == 0

    @pytest.mark.asyncio
    async def test_fetch_single_value_error(self):
        """_fetch_single: レスポンスがintに変換できない場合に0が返される."""
        fetcher = SocialProofFetcher(timeout=5)

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = AsyncMock()
            mock_response.text = "invalid"
            mock_response.raise_for_status = AsyncMock()

            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            count = await fetcher._fetch_single("https://example.com")

            assert count == 0

    @pytest.mark.asyncio
    async def test_fetch_batch_success(self):
        """fetch_batch: 複数URLの一括取得が成功する."""
        fetcher = SocialProofFetcher(timeout=5, concurrency_limit=2)
        urls = [
            "https://example1.com",
            "https://example2.com",
            "https://example3.com",
        ]

        with patch.object(fetcher, "_fetch_single") as mock_fetch:
            mock_fetch.side_effect = [10, 20, 30]

            result = await fetcher.fetch_batch(urls)

            assert result == {
                "https://example1.com": 10,
                "https://example2.com": 20,
                "https://example3.com": 30,
            }
            assert mock_fetch.call_count == 3

    @pytest.mark.asyncio
    async def test_fetch_batch_partial_failure(self):
        """fetch_batch: 一部失敗時も継続する."""
        fetcher = SocialProofFetcher(timeout=5, concurrency_limit=2)
        urls = [
            "https://example1.com",
            "https://example2.com",
            "https://example3.com",
        ]

        with patch.object(fetcher, "_fetch_single") as mock_fetch:
            # 2番目のURLでエラー発生
            mock_fetch.side_effect = [10, Exception("Error"), 30]

            result = await fetcher.fetch_batch(urls)

            # エラーが発生したURLは結果に含まれない
            assert result == {
                "https://example1.com": 10,
                "https://example3.com": 30,
            }
            assert mock_fetch.call_count == 3

    @pytest.mark.asyncio
    async def test_fetch_batch_empty_urls(self):
        """fetch_batch: 空のURLリストで空の辞書が返される."""
        fetcher = SocialProofFetcher(timeout=5)

        result = await fetcher.fetch_batch([])

        assert result == {}
