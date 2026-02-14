"""SocialProof取得サービスモジュール."""

import asyncio

import httpx

from src.shared.logging.logger import get_logger

logger = get_logger(__name__)


class SocialProofFetcher:
    """SocialProof（外部反応）取得サービス.

    はてなブックマーク数を取得する.

    Attributes:
        _timeout: タイムアウト（秒）
        _concurrency_limit: 並列度制限
    """

    HATENA_API_URL = "https://bookmark.hatenaapis.com/count/entry?url={url}"

    def __init__(self, timeout: int = 5, concurrency_limit: int = 10) -> None:
        """SocialProof取得サービスを初期化する.

        Args:
            timeout: タイムアウト（秒、デフォルト: 5）
            concurrency_limit: 並列度制限（デフォルト: 10）
        """
        self._timeout = timeout
        self._concurrency_limit = concurrency_limit

    async def fetch_batch(self, urls: list[str]) -> dict[str, int]:
        """複数URLのはてブ数を一括取得する.

        Args:
            urls: URLリスト

        Returns:
            URLをキーとするはてブ数の辞書
        """
        logger.info("social_proof_fetch_start", url_count=len(urls))

        semaphore = asyncio.Semaphore(self._concurrency_limit)

        async def fetch_with_semaphore(url: str) -> tuple[str, int]:
            async with semaphore:
                return url, await self._fetch_single(url)

        tasks = [fetch_with_semaphore(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 結果を集約
        counts: dict[str, int] = {}
        failed_count = 0

        for result in results:
            if isinstance(result, Exception):
                logger.warning("social_proof_fetch_failed", error=str(result))
                failed_count += 1
            elif isinstance(result, tuple):
                url, count = result
                counts[url] = count

        logger.info(
            "social_proof_fetch_complete",
            total_count=len(urls),
            success_count=len(counts),
            failed_count=failed_count,
        )

        return counts

    async def _fetch_single(self, url: str) -> int:
        """単一URLのはてブ数を取得する.

        Args:
            url: 記事URL

        Returns:
            はてブ数（取得失敗時は0）
        """
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(self.HATENA_API_URL.format(url=url))
                response.raise_for_status()

                count = int(response.text or "0")

                logger.debug("hatena_bookmark_fetched", url=url, count=count)

                return count

        except (httpx.HTTPError, ValueError) as e:
            logger.warning("hatena_bookmark_fetch_failed", url=url, error=str(e))
            return 0
