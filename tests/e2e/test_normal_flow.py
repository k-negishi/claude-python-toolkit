"""E2Eテスト（通常フロー）."""

from unittest.mock import Mock, patch

import pytest


def test_lambda_handler_error() -> None:
    """Lambda handlerがエラーを適切にハンドリングすることを確認."""
    # すべてのAWSクライアントとサービスをモック
    with (
        patch("src.handler.boto3.client") as mock_boto3_client,
        patch("src.handler.boto3.resource") as mock_boto3_resource,
        patch("src.handler.Orchestrator") as mock_orchestrator_class,
        patch("src.handler.asyncio.run") as mock_asyncio_run,
    ):
        # boto3クライアントのモック
        mock_dynamodb_client = Mock()
        mock_bedrock_client = Mock()
        mock_ses_client = Mock()
        mock_boto3_client.side_effect = lambda service, **kwargs: {
            "dynamodb": mock_dynamodb_client,
            "bedrock-runtime": mock_bedrock_client,
            "ses": mock_ses_client,
        }[service]

        # boto3リソースのモック
        mock_dynamodb_resource = Mock()
        mock_boto3_resource.return_value = mock_dynamodb_resource

        # Orchestratorのモック
        mock_orchestrator = Mock()
        mock_orchestrator_class.return_value = mock_orchestrator

        # asyncio.run()がエラーを発生させる
        mock_asyncio_run.side_effect = Exception("Orchestrator error")

        # handler.pyをインポート
        from src import handler

        # Lambda handlerを呼び出し
        event = {"dry_run": True}
        context = {}

        result = handler.lambda_handler(event, context)

        # エラーレスポンスを確認
        assert result["statusCode"] == 500
        assert "body" in result
        assert "error" in result["body"]
