# 設計書: 概要はLLMの結果を使いたい

## 変更概要

現在、メールに表示される「概要」は RSS/Atom から取得した `Article.description` を使用しています。この変更では、LLM が生成する内容をメールに表示します。

### 現状

- **LLM が返す**: `reason`（判定理由、最大200文字）
  - 例: "PostgreSQLのインデックス戦略について実践的な知見"
- **メールに表示**: `article.description`（RSS から取得した概要）
  - 例: "This article discusses PostgreSQL indexing strategies for large-scale..."

### 変更後

- **LLM が返す**: `summary`（記事の要約、最大300文字）
  - 例: "PostgreSQLのインデックス戦略に関する実践的な記事。B-treeとGiSTインデックスの使い分け、パフォーマンスチューニング、実運用での注意点を解説。"
- **メールに表示**: `summary`（LLM 生成の要約）
- **`reason` フィールド**: 削除

## 影響範囲

### 1. データモデル変更

**ファイル**: `src/models/judgment.py`

**変更内容**:
- `JudgmentResult.reason` フィールドを削除
- `JudgmentResult.summary` フィールドを追加（型: `str`、最大300文字）

**変更前**:
```python
@dataclass
class JudgmentResult:
    url: str
    title: str
    description: str  # RSS から取得
    interest_label: InterestLabel
    buzz_label: BuzzLabel
    confidence: float
    reason: str  # LLM 判定理由（最大200文字）
    model_id: str
    judged_at: datetime
    published_at: datetime
    tags: list[str] = field(default_factory=list)
```

**変更後**:
```python
@dataclass
class JudgmentResult:
    url: str
    title: str
    description: str  # RSS から取得（LLM プロンプトの入力として使用）
    interest_label: InterestLabel
    buzz_label: BuzzLabel
    confidence: float
    summary: str  # LLM 生成の要約（最大300文字、メール表示用）
    model_id: str
    judged_at: datetime
    published_at: datetime
    tags: list[str] = field(default_factory=list)
```

### 2. LLM プロンプト変更

**ファイル**: `src/services/llm_judge.py`

**変更内容**:
- プロンプトで `reason` の代わりに `summary` を要求
- レスポンス解析で `summary` を取得
- `JudgmentResult` 作成時に `summary` を使用

**変更前のプロンプト**:
```
**reason**（理由）: 判定理由を簡潔に説明（最大200文字）

# 出力形式
{
  "interest_label": "ACT_NOW" | "THINK" | "FYI" | "IGNORE",
  "buzz_label": "HIGH" | "MID" | "LOW",
  "confidence": 0.85,
  "reason": "判定理由の説明",
  "tags": ["Kotlin", "Claude"]
}
```

**変更後のプロンプト**:
```
**summary**（要約）: 記事の内容を簡潔に要約（最大300文字、メール表示用）

# 出力形式
{
  "interest_label": "ACT_NOW" | "THINK" | "FYI" | "IGNORE",
  "buzz_label": "HIGH" | "MID" | "LOW",
  "confidence": 0.85,
  "summary": "記事の内容を簡潔に要約",
  "tags": ["Kotlin", "Claude"]
}
```

**レスポンス解析の変更**:
- `required_fields` を `["interest_label", "buzz_label", "confidence", "summary"]` に変更
- `reason` の検証を削除

### 3. キャッシュリポジトリ変更

**ファイル**: `src/repositories/cache_repository.py`

**変更内容**:
- DynamoDB スキーマを変更（`reason` → `summary`）
- **後方互換性の確保**: 既存キャッシュは `reason` を持つため、読み取り時に互換性を保つ

**DynamoDB スキーマ変更**:

変更前:
```python
{
  "url": "https://example.com/article",
  "title": "Article Title",
  "description": "RSS description",
  "interest_label": "ACT_NOW",
  "buzz_label": "HIGH",
  "confidence": 0.85,
  "reason": "判定理由",  # 既存フィールド
  "model_id": "...",
  "judged_at": "2025-01-15T10:30:00Z",
  "published_at": "2025-01-15T09:00:00Z"
}
```

変更後:
```python
{
  "url": "https://example.com/article",
  "title": "Article Title",
  "description": "RSS description",
  "interest_label": "ACT_NOW",
  "buzz_label": "HIGH",
  "confidence": 0.85,
  "summary": "LLM生成の要約",  # 新フィールド
  "model_id": "...",
  "judged_at": "2025-01-15T10:30:00Z",
  "published_at": "2025-01-15T09:00:00Z"
}
```

**後方互換性の実装**:

```python
def get(self, url: str) -> JudgmentResult | None:
    """キャッシュから判定結果を取得する（後方互換性あり）."""
    # ... DynamoDB GetItem ...

    # 既存キャッシュは reason を持ち、新規は summary を持つ
    # 両方をサポートする
    summary_value = item.get("summary", item.get("reason", ""))

    return JudgmentResult(
        url=item["url"],
        title=item.get("title", "No Title"),
        description=item.get("description", ""),
        interest_label=InterestLabel(item["interest_label"]),
        buzz_label=BuzzLabel(item["buzz_label"]),
        confidence=float(item["confidence"]),
        summary=summary_value,  # summary または reason
        model_id=item.get("model_id", "unknown"),
        judged_at=datetime.fromisoformat(item["judged_at"]),
        published_at=datetime.fromisoformat(item["published_at"]),
        tags=item.get("tags", []),
    )
```

### 4. フォーマッター変更

**ファイル**: `src/services/formatter.py`

**変更内容**:
- メール本文の「概要」フィールドを `article.description` から `article.summary` に変更
- HTML 版も同様に変更

**変更前** (209行目):
```python
f"概要: {article.description}",
```

**変更後**:
```python
f"概要: {article.summary}",
```

**変更前** (HTML版、191行目):
```python
safe_description = self._escape_non_url_html_text(article.description)
# ...
f"概要: {safe_description}"
```

**変更後**:
```python
safe_summary = self._escape_non_url_html_text(article.summary)
# ...
f"概要: {safe_summary}"
```

### 5. テストコード変更

**影響を受けるテストファイル**:
- `tests/unit/models/test_judgment.py`
- `tests/unit/services/test_llm_judge.py`
- `tests/unit/repositories/test_cache_repository.py`
- `tests/unit/services/test_formatter.py`
- `tests/unit/services/test_final_selector.py`
- `tests/integration/test_judgment_flow.py`

**変更内容**:
- `JudgmentResult` を作成するテストコードで `reason=` を `summary=` に変更
- `LlmJudge` のモックレスポンスで `reason` を `summary` に変更
- `CacheRepository` のテストで後方互換性を確認

## アーキテクチャ概要

変更は既存のアーキテクチャパターンに従います。レイヤード アーキテクチャは維持されます。

```
┌─────────────────────────────────────────────────────────┐
│ Service Layer                                           │
│  - LlmJudge: プロンプト変更、summary生成               │
│  - Formatter: summary表示                               │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────┴────────────────────────────────────┐
│ Data Layer                                              │
│  - CacheRepository: 後方互換性を確保                    │
│  - JudgmentResult: reasonフィールド削除、summary追加    │
└─────────────────────────────────────────────────────────┘
```

## データフロー

### LLM 判定フロー

1. **収集**: `Article`（RSS から取得、`description` を含む）を取得
2. **LLM 判定**: `LlmJudge` が `Article.description` をプロンプトに含めて LLM に送信
3. **LLM レスポンス**: `summary`（記事の要約）を含む JSON を返す
4. **キャッシュ保存**: `JudgmentResult`（`summary` を含む）を DynamoDB に保存
5. **最終選定**: `FinalSelector` が `JudgmentResult` を選定
6. **メール送信**: `Formatter` が `JudgmentResult.summary` をメール本文に含める

## エラーハンドリング戦略

### 変更なし

既存のエラーハンドリングパターンを維持します。

- LLM JSON 解析エラー: `LlmJsonParseError`
- `required_fields` に `summary` を追加

## テスト戦略

### ユニットテスト

**新規テスト**:
- `test_judgment_result_with_summary()`: `summary` フィールドを持つ `JudgmentResult` の作成
- `test_llm_judge_prompt_includes_summary()`: プロンプトに `summary` 要求が含まれることを確認
- `test_llm_judge_parses_summary()`: LLM レスポンスから `summary` を正しく解析

**変更テスト**:
- 既存の `reason` を使用するテストをすべて `summary` に変更

**後方互換性テスト**:
- `test_cache_repository_get_with_reason()`: 既存キャッシュ（`reason` のみ）を読み込めることを確認
- `test_cache_repository_get_with_summary()`: 新規キャッシュ（`summary` のみ）を読み込めることを確認

### 統合テスト

- `test_judgment_flow_with_summary()`: LLM 判定から最終選定までのフロー
- `test_cache_backward_compatibility()`: 既存キャッシュと新規キャッシュの混在環境

## 依存ライブラリ

### 変更なし

新しいライブラリの追加は不要です。

## ディレクトリ構造

変更されるファイル:

```
src/
├── models/
│   └── judgment.py                       # reason → summary
├── services/
│   ├── llm_judge.py                      # プロンプト変更、summary解析
│   └── formatter.py                      # summary表示
└── repositories/
    └── cache_repository.py               # 後方互換性確保

tests/
├── unit/
│   ├── models/
│   │   └── test_judgment.py              # summaryテスト
│   ├── services/
│   │   ├── test_llm_judge.py             # summaryテスト
│   │   ├── test_formatter.py             # summary表示テスト
│   │   └── test_final_selector.py        # 変更なし（JudgmentResultは同じ）
│   └── repositories/
│       └── test_cache_repository.py      # 後方互換性テスト
└── integration/
    └── test_judgment_flow.py             # summaryフロー全体テスト
```

## 実装の順序

1. **フェーズ1: モデル変更**
   - `JudgmentResult` の `reason` を `summary` に変更
   - モデルのテストを更新

2. **フェーズ2: LLM プロンプト変更**
   - `LlmJudge` のプロンプトを変更
   - レスポンス解析を更新
   - テストを更新

3. **フェーズ3: キャッシュリポジトリ変更**
   - `CacheRepository` の保存・取得処理を更新
   - 後方互換性を確保
   - テストを更新

4. **フェーズ4: フォーマッター変更**
   - `Formatter` の表示フィールドを変更
   - テストを更新

5. **フェーズ5: 品質チェック**
   - 全テスト実行
   - lint/format/型チェック
   - ローカル実行テスト

## セキュリティ考慮事項

### 変更なし

既存のセキュリティ対策を維持します。

- `summary` フィールドは最大300文字に制限（プロンプトで指示）
- HTML エスケープ処理は既存の `_escape_non_url_html_text()` を使用

## パフォーマンス考慮事項

### LLM コスト

- **変更前**: `reason` 生成（最大200文字）
- **変更後**: `summary` 生成（最大300文字）

**影響**: LLM 出力トークン数が約1.5倍に増加する可能性があります。

**推定コスト増加**:
- 週2回実行 × 120件判定 × 月4週 = 月960件
- 1件あたりの出力トークン増加: 約50トークン（200文字 → 300文字）
- 追加コスト: 960件 × 50トークン × $5.00/1M = **$0.24/月**

**現在のコスト**: $0.70/月
**変更後のコスト**: $0.94/月（依然として$10以内）

## 将来の拡張性

### `description` と `summary` の使い分け

将来的に、以下のような使い分けが可能です：

- **`description`**: RSS から取得した元の概要（LLM 判定の入力）
- **`summary`**: LLM が生成した日本語要約（メール表示用）

この設計により、元の情報を保持しつつ、ユーザーフレンドリーな要約を提供できます。

### 多言語対応

将来的に、記事が英語の場合は LLM が日本語要約を生成するなど、多言語対応も可能です。

## 破壊的変更の影響

### DynamoDB キャッシュ

既存のキャッシュデータは `reason` フィールドを持っています。新しいコードは `summary` フィールドを使用します。

**対策**:
- 読み取り時に `item.get("summary", item.get("reason", ""))` で後方互換性を確保
- 新規判定では `summary` を保存
- 既存キャッシュは徐々に `summary` に置き換わる（再判定時）

**マイグレーション不要**: 後方互換性により、既存データの一括変換は不要です。

## まとめ

この変更により、メールに表示される「概要」が LLM 生成の要約になります。

**メリット**:
- 記事の内容がより分かりやすく要約される
- 日本語記事も英語記事も日本語で要約可能（将来）
- ユーザーが記事の内容を素早く把握できる

**デメリット**:
- LLM コストが約$0.24/月増加（$0.70 → $0.94）
- 既存キャッシュとの互換性処理が必要（後方互換性で解決）

**推奨**: この変更を実装することで、ユーザー体験が大幅に向上します。
