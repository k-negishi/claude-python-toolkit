"""CacheRepositoryのユニットテスト."""

from datetime import datetime, timezone
from unittest.mock import Mock

from src.models.judgment import BuzzLabel, InterestLabel, JudgmentResult
from src.repositories.cache_repository import CacheRepository


def _create_repository() -> tuple[CacheRepository, Mock]:
    dynamodb_resource = Mock()
    table = Mock()
    dynamodb_resource.Table.return_value = table
    repository = CacheRepository(dynamodb_resource=dynamodb_resource, table_name="cache-table")
    return repository, table


def test_put_stores_tags_field() -> None:
    repository, table = _create_repository()

    judgment = JudgmentResult(
        url="https://example.com/a",
        title="Title",
        description="Description",
        interest_label=InterestLabel.ACT_NOW,
        buzz_label=BuzzLabel.HIGH,
        confidence=0.95,
        summary="Reason",
        model_id="model",
        judged_at=datetime(2026, 2, 14, 0, 0, 0, tzinfo=timezone.utc),
        published_at=datetime(2026, 2, 13, 12, 0, 0, tzinfo=timezone.utc),
        tags=["Kotlin", "Claude"],
    )

    repository.put(judgment)

    put_item = table.put_item.call_args.kwargs["Item"]
    assert put_item["tags"] == ["Kotlin", "Claude"]


def test_get_restores_tags_when_present() -> None:
    repository, table = _create_repository()
    table.get_item.return_value = {
        "Item": {
            "PK": "URL#abc",
            "SK": "JUDGMENT#v1",
            "url": "https://example.com/a",
            "title": "Title",
            "description": "Description",
            "interest_label": "ACT_NOW",
            "buzz_label": "HIGH",
            "confidence": 0.95,
            "summary": "Reason",
            "model_id": "model",
            "judged_at": "2026-02-14T00:00:00+00:00",
            "published_at": "2026-02-13T12:00:00+00:00",
            "tags": ["Kotlin", "Claude"],
        }
    }

    result = repository.get("https://example.com/a")

    assert result is not None
    assert result.tags == ["Kotlin", "Claude"]


def test_get_uses_empty_tags_when_missing() -> None:
    repository, table = _create_repository()
    table.get_item.return_value = {
        "Item": {
            "PK": "URL#abc",
            "SK": "JUDGMENT#v1",
            "url": "https://example.com/a",
            "title": "Title",
            "description": "Description",
            "interest_label": "ACT_NOW",
            "buzz_label": "HIGH",
            "confidence": 0.95,
            "summary": "Reason",
            "model_id": "model",
            "judged_at": "2026-02-14T00:00:00+00:00",
            "published_at": "2026-02-13T12:00:00+00:00",
        }
    }

    result = repository.get("https://example.com/a")

    assert result is not None
    assert result.tags == []


def test_cache_repository_get_with_summary() -> None:
    """新規キャッシュ（summaryフィールド）の読み込みを検証."""
    repository, table = _create_repository()
    # 新規のキャッシュデータ（summaryフィールドを持つ）
    table.get_item.return_value = {
        "Item": {
            "PK": "URL#def",
            "SK": "JUDGMENT#v1",
            "url": "https://example.com/new-cache",
            "title": "New Cache Title",
            "description": "New cache description",
            "interest_label": "ACT_NOW",
            "buzz_label": "HIGH",
            "confidence": 0.95,
            "summary": "This is a new cache summary",
            "model_id": "model-new",
            "judged_at": "2026-02-15T00:00:00+00:00",
            "published_at": "2026-02-14T12:00:00+00:00",
            "tags": ["Kotlin", "AWS"],
        }
    }

    result = repository.get("https://example.com/new-cache")

    assert result is not None
    assert result.summary == "This is a new cache summary"
    assert result.url == "https://example.com/new-cache"


def test_cache_repository_put_with_summary() -> None:
    """summaryフィールドが正しく保存されることを検証."""
    repository, table = _create_repository()

    judgment = JudgmentResult(
        url="https://example.com/save-test",
        title="Save Test Title",
        description="Save test description",
        interest_label=InterestLabel.FYI,
        buzz_label=BuzzLabel.LOW,
        confidence=0.75,
        summary="This is a test summary for saving",
        model_id="test-model",
        judged_at=datetime(2026, 2, 15, 10, 0, 0, tzinfo=timezone.utc),
        published_at=datetime(2026, 2, 14, 12, 0, 0, tzinfo=timezone.utc),
        tags=["Test", "Cache"],
    )

    repository.put(judgment)

    put_item = table.put_item.call_args.kwargs["Item"]
    assert put_item["summary"] == "This is a test summary for saving"
    assert "reason" not in put_item  # reasonフィールドは保存されない


def test_get_returns_none_when_item_not_exists() -> None:
    """アイテムが存在しない場合、Noneを返す."""
    repository, table = _create_repository()
    table.get_item.return_value = {}  # "Item"キーが存在しない

    result = repository.get("https://example.com/not-exists")

    assert result is None


def test_get_returns_none_on_client_error() -> None:
    """ClientErrorが発生した場合、Noneを返す."""
    from botocore.exceptions import ClientError

    repository, table = _create_repository()
    table.get_item.side_effect = ClientError(
        {"Error": {"Code": "ResourceNotFoundException", "Message": "Table not found"}},
        "GetItem",
    )

    result = repository.get("https://example.com/error")

    assert result is None


def test_put_raises_error_on_client_error() -> None:
    """putでClientErrorが発生した場合、エラーを再送出する."""
    from botocore.exceptions import ClientError

    repository, table = _create_repository()
    table.put_item.side_effect = ClientError(
        {"Error": {"Code": "ResourceNotFoundException", "Message": "Table not found"}},
        "PutItem",
    )

    judgment = JudgmentResult(
        url="https://example.com/error",
        title="Error Title",
        description="Error description",
        interest_label=InterestLabel.FYI,
        buzz_label=BuzzLabel.LOW,
        confidence=0.75,
        summary="Error summary",
        model_id="error-model",
        judged_at=datetime(2026, 2, 15, 10, 0, 0, tzinfo=timezone.utc),
        published_at=datetime(2026, 2, 14, 12, 0, 0, tzinfo=timezone.utc),
        tags=[],
    )

    try:
        repository.put(judgment)
        assert False, "Expected ClientError to be raised"
    except ClientError:
        pass  # Expected


def test_exists_returns_true_when_cached() -> None:
    """existsメソッドでキャッシュが存在する場合、Trueを返す."""
    repository, table = _create_repository()
    table.get_item.return_value = {
        "Item": {
            "PK": "URL#abc",
            "SK": "JUDGMENT#v1",
            "url": "https://example.com/exists",
            "title": "Title",
            "description": "Description",
            "interest_label": "ACT_NOW",
            "buzz_label": "HIGH",
            "confidence": 0.95,
            "summary": "Summary",
            "model_id": "model",
            "judged_at": "2026-02-14T00:00:00+00:00",
            "published_at": "2026-02-13T12:00:00+00:00",
        }
    }

    result = repository.exists("https://example.com/exists")

    assert result is True


def test_exists_returns_false_when_not_cached() -> None:
    """existsメソッドでキャッシュが存在しない場合、Falseを返す."""
    repository, table = _create_repository()
    table.get_item.return_value = {}  # "Item"キーが存在しない

    result = repository.exists("https://example.com/not-exists")

    assert result is False


def test_batch_exists_empty_list() -> None:
    """batch_existsで空のリストを渡した場合、空の辞書を返す."""
    repository, table = _create_repository()

    result = repository.batch_exists([])

    assert result == {}


def test_batch_exists_single_url() -> None:
    """batch_existsで単一URLを確認できる."""
    repository, _ = _create_repository()
    dynamodb_resource = repository._dynamodb
    dynamodb_resource.batch_get_item.return_value = {
        "Responses": {
            "cache-table": [
                {
                    "url": "https://example.com/exists",
                }
            ]
        }
    }

    result = repository.batch_exists(["https://example.com/exists"])

    assert result == {"https://example.com/exists": True}


def test_batch_exists_multiple_urls() -> None:
    """batch_existsで複数URLを一括確認できる."""
    repository, _ = _create_repository()
    dynamodb_resource = repository._dynamodb
    dynamodb_resource.batch_get_item.return_value = {
        "Responses": {
            "cache-table": [
                {"url": "https://example.com/exists1"},
                {"url": "https://example.com/exists2"},
            ]
        }
    }

    result = repository.batch_exists([
        "https://example.com/exists1",
        "https://example.com/exists2",
        "https://example.com/not-exists",
    ])

    assert result == {
        "https://example.com/exists1": True,
        "https://example.com/exists2": True,
        "https://example.com/not-exists": False,
    }


def test_batch_exists_handles_client_error() -> None:
    """batch_existsでClientErrorが発生した場合、全てFalseを返す."""
    from botocore.exceptions import ClientError

    repository, _ = _create_repository()
    dynamodb_resource = repository._dynamodb
    dynamodb_resource.batch_get_item.side_effect = ClientError(
        {"Error": {"Code": "ResourceNotFoundException", "Message": "Table not found"}},
        "BatchGetItem",
    )

    result = repository.batch_exists([
        "https://example.com/url1",
        "https://example.com/url2",
    ])

    assert result == {
        "https://example.com/url1": False,
        "https://example.com/url2": False,
    }
