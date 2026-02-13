"""Lambda ハンドラーモジュール."""

import asyncio
import json
import os
import uuid
from typing import Any

import boto3

from src.orchestrator.orchestrator import Orchestrator
from src.repositories.source_master import SourceMaster
from src.services.buzz_scorer import BuzzScorer
from src.services.candidate_selector import CandidateSelector
from src.services.collector import Collector
from src.services.deduplicator import Deduplicator
from src.services.final_selector import FinalSelector
from src.services.formatter import Formatter
from src.services.llm_judge import LlmJudge
from src.services.normalizer import Normalizer
from src.services.notifier import Notifier
from src.shared.logging.logger import configure_logging, get_logger
from src.shared.utils.date_utils import now_utc


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Lambda エントリポイント.

    Args:
        event: Lambda イベント
        context: Lambda コンテキスト

    Returns:
        Lambda レスポンス
    """
    # run_id生成
    run_id = str(uuid.uuid4())

    # ログ設定
    configure_logging(run_id=run_id)
    logger = get_logger(__name__)

    logger.info("lambda_handler_start", run_id=run_id)

    try:
        # イベント解析
        dry_run = event.get("dry_run", False)
        logger.info("event_parsed", dry_run=dry_run)

        # 環境変数取得
        # TODO(MVP): DynamoDB未セットアップのため一時的にコメントアウト
        # Phase 2で有効化: DynamoDBテーブル作成後に以下を復元
        # cache_table_name = os.environ.get("CACHE_TABLE_NAME", "ai-curated-newsletter-cache")
        # history_table_name = os.environ.get("HISTORY_TABLE_NAME", "ai-curated-newsletter-history")
        sources_config_path = os.environ.get("SOURCES_CONFIG_PATH", "config/sources.json")
        from_email = os.environ.get("FROM_EMAIL", "noreply@example.com")
        to_email = os.environ.get("TO_EMAIL", "recipient@example.com")
        bedrock_model_id = os.environ.get(
            "BEDROCK_MODEL_ID", "anthropic.claude-3-5-sonnet-20241022-v2:0"
        )

        # AWS クライアント初期化
        # TODO(MVP): DynamoDB未セットアップのため一時的にコメントアウト
        # dynamodb = boto3.resource("dynamodb")
        bedrock_runtime = boto3.client("bedrock-runtime")
        ses = boto3.client("ses")

        # リポジトリ初期化
        source_master = SourceMaster(sources_config_path)
        # TODO(MVP): DynamoDB未セットアップのため一時的にコメントアウト
        # Phase 2で有効化: 以下の2行を復元し、Noneの代入を削除
        # cache_repository = CacheRepository(dynamodb, cache_table_name)
        # history_repository = HistoryRepository(dynamodb, history_table_name)
        cache_repository = None  # MVPフェーズではキャッシュ機能を無効化
        history_repository = None  # MVPフェーズでは履歴保存機能を無効化

        # サービス初期化
        collector = Collector(source_master)
        normalizer = Normalizer()
        deduplicator = Deduplicator(cache_repository)
        buzz_scorer = BuzzScorer()
        candidate_selector = CandidateSelector(max_candidates=150)
        llm_judge = LlmJudge(
            bedrock_client=bedrock_runtime,
            cache_repository=cache_repository,
            model_id=bedrock_model_id,
        )
        final_selector = FinalSelector(max_articles=12, max_per_domain=4)
        formatter = Formatter()
        notifier = Notifier(ses, from_email=from_email, to_email=to_email)

        # Orchestrator初期化
        orchestrator = Orchestrator(
            source_master=source_master,
            cache_repository=cache_repository,
            history_repository=history_repository,
            collector=collector,
            normalizer=normalizer,
            deduplicator=deduplicator,
            buzz_scorer=buzz_scorer,
            candidate_selector=candidate_selector,
            llm_judge=llm_judge,
            final_selector=final_selector,
            formatter=formatter,
            notifier=notifier,
        )

        # Orchestrator実行
        executed_at = now_utc()
        result = asyncio.run(orchestrator.execute(run_id, executed_at, dry_run))

        # レスポンス返却
        logger.info("lambda_handler_success", run_id=run_id)

        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "message": "Newsletter generation completed",
                    "run_id": run_id,
                    "collected_count": result.summary.collected_count,
                    "final_selected_count": result.summary.final_selected_count,
                    "notification_sent": result.notification_sent,
                }
            ),
        }

    except Exception as e:
        logger.error("lambda_handler_failed", run_id=run_id, error=str(e))

        return {
            "statusCode": 500,
            "body": json.dumps(
                {
                    "message": "Newsletter generation failed",
                    "run_id": run_id,
                    "error": str(e),
                }
            ),
        }
