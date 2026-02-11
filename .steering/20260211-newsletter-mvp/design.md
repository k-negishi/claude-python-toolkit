# 設計書

## アーキテクチャ概要

MVP Phase 1では**レイヤードアーキテクチャ + 単一Lambda構成**を採用します。

### アーキテクチャ図

```
┌─────────────────────────────────────────────────────────┐
│ EventBridge Scheduler (週2-3回)                          │
└────────────────────┬────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────┐
│ Lambda Function (Python 3.12, 1024MB, 15min timeout)   │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ handler.py (Lambda Entry Point)                     │ │
│ └────────┬────────────────────────────────────────────┘ │
│          ↓                                               │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ Orchestrator (全体フロー制御)                        │ │
│ │  ├─ Step 1: Collect & Normalize (収集・正規化)     │ │
│ │  ├─ Step 2: Deduplicate (重複排除)                 │ │
│ │  ├─ Step 3: Calculate Buzz Score (Buzzスコア)      │ │
│ │  ├─ Step 4: Select Candidates (候補選定)           │ │
│ │  ├─ Step 5: LLM Judge (LLM判定, 最大150件)         │ │
│ │  ├─ Step 6: Final Select (最終選定, 最大12件)      │ │
│ │  ├─ Step 7: Format & Notify (フォーマット・通知)   │ │
│ │  └─ Step 8: Save History (履歴保存)                │ │
│ └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
         │              │              │
         ↓              ↓              ↓
    ┌────────┐    ┌─────────┐    ┌──────┐
    │DynamoDB│    │ Bedrock │    │ SES  │
    └────────┘    └─────────┘    └──────┘
```

### レイヤー構造

```
handler.py (Lambda Entry Point)
    ↓
orchestrator/ (Orchestration Layer)
    ↓
services/ (Service Layer - ビジネスロジック)
    ↓
repositories/ (Data Layer - データ永続化)
    ↓
models/ + shared/ (Domain Models + Utilities)
```

## コンポーネント設計

### 1. handler.py (Lambda Entry Point)

**責務**:
- Lambda イベントの受信
- Orchestrator の初期化・実行
- レスポンスの返却

**実装の要点**:
- イベントから `dry_run` フラグを取得（デフォルト: false）
- run_id は UUID で生成
- エラー発生時は500レスポンス、CloudWatch Logsに記録

### 2. orchestrator.py (Orchestrator)

**責務**:
- 全体フローの制御（8ステップを順次実行）
- 各サービスの呼び出し
- エラーハンドリング
- 実行履歴の記録

**実装の要点**:
- 各ステップの開始・終了をログに記録
- エラー発生時は中断（ただしソース単位のエラーは継続）
- dry_run モードでは通知をスキップ

### 3. services/collector.py (Collector)

**責務**:
- RSS/Atom フィードの収集
- 複数ソースの並列収集
- タイムアウト・リトライ処理

**実装の要点**:
- httpx の AsyncClient を使用（並列収集）
- feedparser でフィード解析
- ソース単位でエラーハンドリング（1つ失敗しても他は継続）
- 収集元マスタ（SourceMaster）から設定を読み込み

### 4. services/normalizer.py (Normalizer)

**責務**:
- URL正規化
- 日時のUTC統一
- タイトル・概要の整形

**実装の要点**:
- URL正規化: クエリパラメータ除去、utm_*除去、スキーム統一（https）
- 日時: すべてUTC ISO8601形式に変換
- タイトル: 前後空白除去、HTML実体参照デコード
- 概要: 最大800文字に制限

### 5. services/deduplicator.py (Deduplicator)

**責務**:
- URL完全一致による重複排除
- キャッシュ済みURL除外
- 重複統計の記録

**実装の要点**:
- CacheRepository の batch_exists() を使用
- 重複件数、キャッシュヒット件数を記録

### 6. services/buzz_scorer.py (BuzzScorer)

**責務**:
- 複数ソース出現スコア計算
- 鮮度スコア計算
- ドメイン多様性スコア計算
- 総合Buzzスコア算出

**実装の要点**:
- 計算式:
  - `source_count_score = min(source_count * 20, 100)`
  - `recency_score = max(100 - (days_old * 10), 0)`
  - `domain_diversity_score = max(100 - (same_domain_count * 5), 0)`
  - `total_score = (source_count_score * 0.4) + (recency_score * 0.5) + (domain_diversity_score * 0.1)`

### 7. services/candidate_selector.py (CandidateSelector)

**責務**:
- Buzzスコアと鮮度でソート
- 上位最大150件を選定
- キャッシュヒット済みURLの除外

**実装の要点**:
- ソート順: Buzzスコア降順 → 鮮度降順
- 最大候補数: 150件（推奨120件）

### 8. services/llm_judge.py (LlmJudge)

**責務**:
- AWS Bedrock への判定リクエスト
- 関心プロファイルの適用
- JSON形式の判定結果取得
- リトライ・エラーハンドリング
- 判定結果のキャッシュ保存

**実装の要点**:
- Bedrock モデル: `anthropic.claude-3-5-sonnet-20241022-v2:0`
- 並列度: 5件（同時に5件判定）
- リトライ: 最大2回（JSON崩れの場合）
- 失敗時: IGNORE扱い
- キャッシュ: CacheRepository の put() を使用

### 9. services/final_selector.py (FinalSelector)

**責務**:
- Interest Labelによる優先順位付け
- 同一ラベル内でのソート
- 最大12件の選定
- ドメイン偏り制御

**実装の要点**:
- 優先度: ACT_NOW > THINK > FYI > IGNORE（IGNOREは除外）
- ソート順: Interest Label → Buzz Label → 鮮度 → Confidence
- 同一ドメイン: 最大4件

### 10. services/formatter.py (Formatter)

**責務**:
- メール本文のフォーマット
- サマリ統計の生成
- プレーンテキスト形式

**実装の要点**:
- フォーマット: セクション別（ACT_NOW / THINK / FYI）
- サマリ: 収集数、LLM判定数、最終通知数、実行日時

### 11. services/notifier.py (Notifier)

**責務**:
- AWS SESへのメール送信
- 送信結果の記録

**実装の要点**:
- SES send_email() を使用
- 送信先・送信元: Secrets Manager から取得
- メールアドレスはログにマスクして記録

### 12. repositories/cache_repository.py (CacheRepository)

**責務**:
- DynamoDBへの判定結果保存
- URL単位のキャッシュ取得
- 再判定禁止の保証

**実装の要点**:
- テーブル: `ai-curated-newsletter-cache`
- PK: `URL#<sha256(url)>`, SK: `JUDGMENT#v1`
- TTL: なし（永続的にキャッシュ）

### 13. repositories/history_repository.py (HistoryRepository)

**責務**:
- DynamoDBへの実行履歴保存
- 週単位の実行履歴取得

**実装の要点**:
- テーブル: `ai-curated-newsletter-history`
- PK: `RUN#<YYYYWW>`, SK: `SUMMARY#<timestamp>`
- TTL: 90日

### 14. repositories/source_master.py (SourceMaster)

**責務**:
- 収集元設定の読み込み
- 有効な収集元のフィルタリング

**実装の要点**:
- Phase 1: S3 または config/sources.json から読み込み
- pydantic で設定ファイルをバリデーション

### 15. models/ (Data Models)

**配置ファイル**:
- `article.py`: Article エンティティ
- `judgment.py`: JudgmentResult エンティティ
- `buzz_score.py`: BuzzScore エンティティ
- `execution_summary.py`: ExecutionSummary エンティティ
- `source_config.py`: SourceConfig エンティティ

**実装の要点**:
- 全て `@dataclass` で定義
- 型ヒント必須

### 16. shared/utils/ (Utilities)

**配置ファイル**:
- `url_normalizer.py`: URL正規化
- `date_utils.py`: 日時ユーティリティ

### 17. shared/logging/ (Logging)

**配置ファイル**:
- `logger.py`: structlog設定

**実装の要点**:
- JSON形式ログ出力
- run_id をログコンテキストに含める
- メールアドレスのマスキング

### 18. shared/exceptions/ (Custom Exceptions)

**配置ファイル**:
- `collection_error.py`: CollectionError
- `llm_error.py`: LlmError, LlmJsonParseError, LlmTimeoutError
- `notification_error.py`: NotificationError

## データフロー

### 通常実行フロー

```
1. handler.py が Lambda イベントを受信
2. Orchestrator.execute() を呼び出し
3. Step 1: Collector.collect() → 記事収集（300-500件）
4. Step 2: Normalizer.normalize() → 記事正規化
5. Step 3: Deduplicator.deduplicate() → 重複排除（200-400件）
6. Step 4: BuzzScorer.calculate_scores() → Buzzスコア計算
7. Step 5: CandidateSelector.select() → 上位120-150件選定
8. Step 6: LlmJudge.judge_batch() → LLM判定（並列5件ずつ）
9. Step 7: FinalSelector.select() → 最終選定（最大12件）
10. Step 8: Formatter.format() → メール本文生成
11. Step 9: Notifier.send() → メール送信（SES）
12. Step 10: HistoryRepository.save() → 実行履歴保存
13. handler.py が成功レスポンスを返却
```

## エラーハンドリング戦略

### カスタムエラークラス

```python
# shared/exceptions/collection_error.py
class CollectionError(Exception):
    """収集エラー（全ソース失敗時）."""
    pass

class SourceCollectionError(CollectionError):
    """単一ソース収集エラー."""
    pass

# shared/exceptions/llm_error.py
class LlmError(Exception):
    """LLM判定エラー."""
    pass

class LlmJsonParseError(LlmError):
    """LLM出力のJSON解析エラー."""
    pass

class LlmTimeoutError(LlmError):
    """LLMタイムアウトエラー."""
    pass

# shared/exceptions/notification_error.py
class NotificationError(Exception):
    """通知エラー."""
    pass
```

### エラーハンドリングパターン

| エラー種別 | 処理 | ログレベル |
|-----------|------|-----------|
| SourceCollectionError | そのソースをスキップ、他ソース継続 | WARNING |
| LlmJsonParseError | リトライ（最大2回）→ 失敗時はIGNORE扱い | WARNING |
| CollectionError（全ソース失敗） | 実行を中断、エラー通知 | ERROR |
| NotificationError | 実行を中断、実行失敗記録 | ERROR |
| DynamoDB エラー | リトライ（最大3回）、失敗時は中断 | ERROR |

## テスト戦略

### ユニットテスト

**テスト対象**:
- `services/normalizer.py`: URL正規化、日時正規化
- `services/buzz_scorer.py`: スコア計算ロジック
- `services/final_selector.py`: 選定ロジック、ドメイン偏り制御
- `services/formatter.py`: メール本文生成
- `shared/utils/url_normalizer.py`: URL正規化関数

**カバレッジ目標**: 80%以上

### 統合テスト

**テストシナリオ**:
- 収集 → 正規化 → 重複排除フロー（DynamoDB連携）
- LLM判定 → キャッシュ保存フロー（DynamoDB連携）
- 最終選定 → フォーマット → 通知フロー（SESモック）

**ツール**: moto（AWSサービスのモック）

### E2Eテスト

**テストシナリオ**:
- 正常系（dry_run=true）: 全ソース成功、LLM判定成功、通知スキップ
- 異常系: 一部ソース失敗 → 他ソース継続、LLM判定失敗 → IGNORE扱い

**ツール**: AWS SAM CLI（ローカルLambda実行）

## 依存ライブラリ

```toml
[project]
name = "ai-curated-newsletter"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "boto3>=1.34.0",
    "feedparser>=6.0.0",
    "httpx>=0.27.0",
    "structlog>=24.1.0",
    "pydantic>=2.6.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "mypy>=1.8.0",
    "ruff>=0.2.0",
    "moto>=5.0.0",
    "boto3-stubs>=1.34.0",
]
```

## ディレクトリ構造

```
ai-curated-newsletter/
├── src/
│   ├── handler.py
│   ├── orchestrator/
│   │   ├── __init__.py
│   │   └── orchestrator.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── collector.py
│   │   ├── normalizer.py
│   │   ├── deduplicator.py
│   │   ├── buzz_scorer.py
│   │   ├── candidate_selector.py
│   │   ├── llm_judge.py
│   │   ├── final_selector.py
│   │   ├── formatter.py
│   │   └── notifier.py
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── cache_repository.py
│   │   ├── history_repository.py
│   │   └── source_master.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── article.py
│   │   ├── judgment.py
│   │   ├── buzz_score.py
│   │   ├── execution_summary.py
│   │   └── source_config.py
│   └── shared/
│       ├── __init__.py
│       ├── utils/
│       │   ├── __init__.py
│       │   ├── url_normalizer.py
│       │   └── date_utils.py
│       ├── logging/
│       │   ├── __init__.py
│       │   └── logger.py
│       └── exceptions/
│           ├── __init__.py
│           ├── collection_error.py
│           ├── llm_error.py
│           └── notification_error.py
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── config/
│   └── sources.json
├── template.yaml
├── pyproject.toml
└── requirements.txt
```

## 実装の順序

1. **フェーズ1: プロジェクト基盤構築**
   - pyproject.toml 作成
   - ディレクトリ構造作成
   - `__init__.py` ファイル作成

2. **フェーズ2: データモデル実装**
   - models/ 配下の全エンティティ

3. **フェーズ3: 共通ユーティリティ実装**
   - shared/utils/
   - shared/logging/
   - shared/exceptions/

4. **フェーズ4: リポジトリ実装**
   - repositories/ 配下の全リポジトリ

5. **フェーズ5: サービス実装**
   - services/ 配下の全サービス

6. **フェーズ6: オーケストレーター実装**
   - orchestrator/orchestrator.py

7. **フェーズ7: Lambda ハンドラー実装**
   - handler.py

8. **フェーズ8: 設定ファイル・AWS SAM テンプレート**
   - config/sources.json
   - template.yaml

9. **フェーズ9: テスト実装**
   - tests/ 配下の全テスト

10. **フェーズ10: 品質チェック**
    - pytest 実行
    - mypy 実行
    - ruff 実行

## セキュリティ考慮事項

- **認証情報管理**: メールアドレスはAWS Secrets Managerで管理（ハードコード禁止）
- **ログマスキング**: メールアドレスはログに出力しない
- **IAMロール**: 最小権限の原則（必要な操作のみ許可）
- **入力検証**: pydantic で設定ファイルをバリデーション

## パフォーマンス考慮事項

- **並列収集**: httpx の AsyncClient で複数ソースを並列収集
- **並列判定**: LLM判定を5件ずつ並列実行
- **バッチキャッシュ取得**: DynamoDB BatchGetItemで一括取得
- **Lambda メモリ**: 1024MB（コスト効率とパフォーマンスのバランス）
- **Lambda タイムアウト**: 15分（最大実行時間の余裕）

**目標実行時間**: 10分以内

## 将来の拡張性

- **Step Functions化**: 処理時間が12分を超える場合、3つのLambdaに分割
- **フィードバック機能**: 通知記事の評価収集（Phase 2）
- **近似重複排除**: Embedding + ベクトル検索（Phase 2）
- **マルチユーザー対応**: DynamoDBにuser_id追加（スコープ外）
