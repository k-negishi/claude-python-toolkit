# 設計書

## GitHub Issue

https://github.com/k-negishi/ai-curated-newsletter/issues/26

## 実装方針

- Kent Beck の TDD (Test-Driven Development) で実装する
- RED → GREEN → REFACTOR のサイクルを遵守
- テストを先に書き、最小限の実装でパスさせ、その後リファクタリング

## TDDサイクル

1. **RED**: 失敗するテストを先に書く
2. **GREEN**: 最小限の実装でテストをパスさせる
3. **REFACTOR**: コード品質を向上させる

## アーキテクチャ概要

Bedrock API の ThrottlingException に対するリトライ機能を追加します。AWS SDK のベストプラクティスに基づき、指数バックオフ + ジッターによるリトライ戦略を実装します。

### 現在の問題

```
Bedrock API呼び出し
  ↓
ThrottlingException発生
  ↓
リトライされずに raise
  ↓
judge_batch() で Exception キャッチ
  ↓
フォールバック判定（IGNORE扱い）
```

### 改善後のフロー

```
Bedrock API呼び出し
  ↓
ThrottlingException発生
  ↓
指数バックオフ + ジッターでリトライ（最大4回）
  ↓
成功 or 最大リトライ到達
  ↓
成功: 判定結果を返す
失敗: フォールバック判定（IGNORE扱い）
```

## コンポーネント設計

### 1. LlmJudge (`src/services/llm_judge.py`)

**変更内容**:
- `_judge_single()` メソッドにThrottlingException のリトライロジックを追加
- `judge_batch()` メソッドに並列リクエスト間の遅延を挿入
- 指数バックオフ + ジッターの実装

**実装の要点**:
- `botocore.exceptions.ClientError` をキャッチし、エラーコードで判定
- リトライ対象:
  - `ThrottlingException`
  - `ServiceUnavailableException` (5xx エラー)
- リトライ非対象:
  - `ValidationException` (パラメータエラー)
  - `AccessDeniedException` (権限不足)
  - その他の予期しないエラー

**リトライ戦略**:
```python
import random

def calculate_backoff(attempt: int, base_delay: float, max_backoff: float) -> float:
    """指数バックオフ + ジッターを計算."""
    delay = min(base_delay * (2 ** attempt), max_backoff)
    jitter = random.uniform(0, delay * 0.5)  # 最大50%のジッター
    return delay + jitter
```

**並列リクエスト間の遅延**:
```python
async def judge_with_semaphore(article: Article) -> JudgmentResult | None:
    async with semaphore:
        await asyncio.sleep(request_interval)  # リクエスト前に遅延
        return await self._judge_single(article)
```

### 2. AppConfig (`src/shared/config.py`)

**変更内容**:
- 新規環境変数の追加:
  - `BEDROCK_REQUEST_INTERVAL`: リクエスト間隔（秒）
  - `BEDROCK_RETRY_BASE_DELAY`: リトライ初回遅延（秒）
  - `BEDROCK_MAX_BACKOFF`: 最大バックオフ時間（秒）
  - `BEDROCK_MAX_RETRIES`: 最大リトライ回数

**実装の要点**:
- 既存の `bedrock_max_parallel` を活用
- デフォルト値は AWS ベストプラクティスに準拠

### 3. Handler (`src/handler.py`)

**変更内容**:
- `LlmJudge` 初期化時に設定値を渡す
- `config.bedrock_max_parallel` を `concurrency_limit` に適用
- 新規設定値を引数として追加

**実装の要点**:
```python
llm_judge = LlmJudge(
    bedrock_client=bedrock_runtime,
    cache_repository=cache_repository,
    interest_profile=interest_profile,
    model_id=config.bedrock_model_id,
    inference_profile_arn=config.bedrock_inference_profile_arn,
    max_retries=config.bedrock_max_retries,
    concurrency_limit=config.bedrock_max_parallel,
    request_interval=config.bedrock_request_interval,
    retry_base_delay=config.bedrock_retry_base_delay,
    max_backoff=config.bedrock_max_backoff,
)
```

## データフロー

### Bedrock API呼び出しのリトライフロー

```
1. _judge_single() メソッド開始
2. リトライループ（最大 max_retries + 1 回）
   a. Bedrock API呼び出し
   b. 成功 → 判定結果を返す
   c. LlmJsonParseError → 従来通りリトライ
   d. ClientError (ThrottlingException) →
      - エラーコードを確認
      - リトライ対象なら指数バックオフ + ジッターで待機
      - 次のループへ
   e. その他のエラー → raise
3. 最大リトライ到達 → raise
```

### 並列リクエストの遅延制御

```
1. judge_batch() メソッド開始
2. Semaphore で並行数を制限（config.bedrock_max_parallel）
3. 各リクエスト前に config.bedrock_request_interval 秒待機
4. _judge_single() を非同期実行
5. 全結果を集約
```

## エラーハンドリング戦略

### リトライ対象の判定

```python
from botocore.exceptions import ClientError

def is_retryable_error(error: Exception) -> bool:
    """リトライ可能なエラーか判定."""
    if not isinstance(error, ClientError):
        return False

    error_code = error.response.get('Error', {}).get('Code', '')
    return error_code in ['ThrottlingException', 'ServiceUnavailableException']
```

### エラーハンドリングパターン

1. **ThrottlingException**: 指数バックオフ + ジッターでリトライ
2. **ServiceUnavailableException**: 同様にリトライ
3. **ValidationException**: リトライせずに raise
4. **AccessDeniedException**: リトライせずに raise
5. **その他のエラー**: リトライせずに raise
6. **LlmJsonParseError**: 従来通りリトライ（既存ロジック維持）

## テスト戦略

### ユニットテスト (`tests/unit/services/test_llm_judge.py`)

**追加するテストケース**:
- ThrottlingException 発生時のリトライ動作
- 指数バックオフの計算ロジック
- ジッターの範囲確認
- 最大リトライ回数到達時の動作
- ServiceUnavailableException のリトライ
- ValidationException はリトライしないことの確認
- リクエスト間隔の挿入確認

**テスト実装の要点**:
- Bedrock クライアントをモック化
- `side_effect` で連続的な例外発生をシミュレート
- `asyncio.sleep` をモック化して実行時間を短縮
- リトライ回数のカウント確認

### 統合テスト (`tests/integration/test_judgment_flow.py`)

**確認項目**:
- 実際の Bedrock API 呼び出しでリトライが機能するか（オプション）
- 設定値が正しく適用されているか

## 依存ライブラリ

既存の依存関係を使用（新規追加なし）:
- `botocore`: Bedrock API の例外クラス (`ClientError`)
- `random`: ジッターの生成

## ディレクトリ構造

```
src/
├── services/
│   └── llm_judge.py              # リトライロジック追加
├── shared/
│   └── config.py                 # 新規環境変数追加
└── handler.py                    # LlmJudge 初期化時の設定値適用

tests/
├── unit/
│   └── services/
│       └── test_llm_judge.py     # リトライロジックのテスト追加
└── integration/
    └── test_judgment_flow.py     # 統合テストの確認

.env                              # 新規環境変数の追加
.env.example                      # 新規環境変数の例示
```

## 実装の順序（TDDサイクル）

### フェーズ1: リトライロジック実装

1. **RED**: ThrottlingException のリトライテストを書く
2. **GREEN**: 最小限の実装でテストをパスさせる
3. **REFACTOR**: コードを改善

### フェーズ2: 指数バックオフ + ジッター実装

1. **RED**: バックオフ計算のテストを書く
2. **GREEN**: 実装してテストをパスさせる
3. **REFACTOR**: コードを改善

### フェーズ3: 設定値の追加と適用

1. **RED**: 設定値が正しく適用されるテストを書く
2. **GREEN**: 実装してテストをパスさせる
3. **REFACTOR**: コードを改善

### フェーズ4: 並列リクエスト間隔の実装

1. **RED**: リクエスト間隔のテストを書く
2. **GREEN**: 実装してテストをパスさせる
3. **REFACTOR**: コードを改善

### フェーズ5: 統合テストと品質チェック

1. すべてのテストが通ることを確認
2. lint/format/型チェックを実行
3. ドキュメント更新

## セキュリティ考慮事項

- エラーログに機密情報（API キーなど）を含めない
- リトライ時のログ出力はレート制限情報のみ記録

## パフォーマンス考慮事項

### 時間見積もり（並行数2、間隔2.5秒の場合）

**通常時（Throttling なし）**:
- 120件 ÷ 2並列 = 60バッチ
- 各バッチ: 5秒（API応答）+ 2.5秒（間隔）= 7.5秒
- 合計: 60 × 7.5秒 = 450秒 ≈ **7.5分**

**リトライ発生時（10件がフル3回リトライ）**:
- リトライ遅延: 2秒 + 4秒 + 8秒 = 14秒
- 10件 × 14秒 = 140秒 ≈ 2.5分
- 合計: 7.5分 + 2.5分 = **10分**

**最悪時（20件がフル4回リトライ）**:
- リトライ遅延: 2秒 + 4秒 + 8秒 + 16秒 = 30秒
- 20件 × 30秒 = 600秒 = 10分
- 合計: 7.5分 + 10分 = **17.5分**
- **Lambda タイムアウト（15分）を超える可能性あり**

### Lambda タイムアウト対策

- 並行数を3に増やすことでベース時間を短縮（7.5分 → 5分）
- リトライ回数を3回に制限（最悪時を12分以内に抑える）

## 将来の拡張性

### Phase 2 での改善案

- Adaptive Retry Mode の導入（AWS SDK の機能）
- Cross-Region Inference の活用（複数リージョンへの分散）
- Bedrock の Provisioned Throughput への移行（レート制限の緩和）
- CloudWatch メトリクスによるリトライ率の監視

### 設定の最適化

- 運用データを元に並行数とリトライ間隔を調整
- Throttling 発生率に応じた動的な設定変更（将来検討）
