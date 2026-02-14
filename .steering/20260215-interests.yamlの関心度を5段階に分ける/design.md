# 設計書

## GitHub Issue
https://github.com/k-negishi/ai-curated-newsletter/issues/25

## issue 内容
- タイトル: interests.yaml の関心度を5段階に分ける
- 本文: 5 ... MAX\n1 ... IGNORE
- ラベル: なし

## 要件確認結果

### 5段階の定義
- 5 = max (最高関心)
- 4 = high (高関心)
- 3 = medium (中関心)
- 2 = low (低関心)
- 1 = ignore (関心外)

### スコア配分
- max: 100点
- high: 85点
- medium: 70点
- low: 50点
- ignore: 0点

### 移行方針
既存の3段階をそのまま維持し、maxとignoreを新規追加:
- 既存の `high_interest` → そのまま `high_interest`
- 既存の `medium_interest` → そのまま `medium_interest`
- 既存の `low_priority` → `low_interest` に改名
- 新規追加: `max_interest` (空リスト)
- 新規追加: `ignore_interest` (空リスト)

## 実装方針
- Kent Beck の TDD (Test-Driven Development) で実装する
- RED → GREEN → REFACTOR のサイクルを遵守
- テストを先に書き、最小限の実装でパスさせ、その後リファクタリング

## アーキテクチャ概要

既存の3段階の関心度システムを5段階に拡張します。データモデル、リポジトリ、サービスの各層で変更が必要です。

```
[interests.yaml (設定ファイル)]
         ↓
[InterestMaster (リポジトリ)]
         ↓
[InterestProfile (モデル)]
         ↓
[BuzzScorer (サービス)] → スコア計算
```

## コンポーネント設計

### 1. InterestProfile モデル（`src/models/interest_profile.py`）

**変更内容**:
- 5つのフィールドを定義:
  - `max_interest: list[str]` (新規追加)
  - `high_interest: list[str]` (既存)
  - `medium_interest: list[str]` (既存)
  - `low_interest: list[str]` (既存の`low_priority`を改名)
  - `ignore_interest: list[str]` (新規追加)

**実装の要点**:
- `format_for_prompt()` メソッドを5段階対応に修正
- 各段階のセクション名を更新:
  - "**最高関心を持つトピック**:" (max_interest)
  - "**強い関心を持つトピック**:" (high_interest)
  - "**中程度の関心を持つトピック**:" (medium_interest)
  - "**低関心のトピック**:" (low_interest)
  - "**関心外のトピック**:" (ignore_interest)

**技術的な制約**:
- 後方互換性を保つため、`low_priority`属性も残す（deprecatedマーク）
- `low_priority`にアクセスした場合は`low_interest`を返す

### 2. InterestMaster リポジトリ（`src/repositories/interest_master.py`）

**変更内容**:
- YAMLから5段階の関心度を読み込むように修正
- 後方互換性のため、古い3段階のYAMLも読み込めるようにする

**実装の要点**:
- `get_profile()` メソッドで5つのフィールドを読み込む
- 古いYAMLフォーマット（`low_priority`）も許容し、`low_interest`にマッピング
- 存在しないフィールドは空リスト`[]`として初期化

**後方互換性の処理**:
```python
# 新形式のフィールドを優先、存在しない場合は旧形式を使用
low_interest = profile_data.get("low_interest") or profile_data.get("low_priority", [])
```

### 3. BuzzScorer サービス（`src/services/buzz_scorer.py`）

**変更内容**:
- `_calculate_interest_score()` メソッドを5段階のスコア計算に対応

**実装の要点**:
- スコア計算ロジック:
  ```python
  # max_interestトピックとのマッチング
  for topic in self._interest_profile.max_interest:
      if self._match_topic(topic, text):
          return 100.0

  # high_interestトピックとのマッチング
  for topic in self._interest_profile.high_interest:
      if self._match_topic(topic, text):
          return 85.0

  # medium_interestトピックとのマッチング
  for topic in self._interest_profile.medium_interest:
      if self._match_topic(topic, text):
          return 70.0

  # low_interestトピックとのマッチング
  for topic in self._interest_profile.low_interest:
      if self._match_topic(topic, text):
          return 50.0

  # ignore_interestトピックとのマッチング
  for topic in self._interest_profile.ignore_interest:
      if self._match_topic(topic, text):
          return 0.0

  # いずれにも一致しない場合はデフォルト（中程度）
  return 50.0
  ```

**技術的な制約**:
- デフォルトスコアを50.0（low相当）に設定

### 4. interests.yaml（`config/interests.yaml`）

**変更内容**:
- 3段階から5段階に拡張

**実装の要点**:
- 既存のトピックを適切に再配置:
  - `high_interest` → そのまま `high_interest`
  - `medium_interest` → そのまま `medium_interest`
  - `low_priority` → `low_interest` に改名
  - `max_interest` と `ignore_interest` を新規追加（初期は空リスト）

## データフロー

### 関心度判定フロー
```
1. interests.yaml を InterestMaster が読み込む
2. InterestMaster が InterestProfile オブジェクトを生成
3. BuzzScorer が InterestProfile を受け取る
4. 記事のタイトル・概要と InterestProfile のトピックをマッチング
5. マッチした段階に応じたスコア（100, 85, 70, 50, 0）を返す
```

## テスト戦略

### ユニットテスト

#### InterestProfile モデルのテスト（`tests/unit/models/test_interest_profile.py`）
- **既存テストの修正**:
  - `test_interest_profile_initialization()`: 5フィールドに対応
  - `test_format_for_prompt()`: 5段階のセクションを検証
  - `test_format_for_prompt_with_empty_lists()`: 5フィールドが空の場合を検証
- **新規テスト**:
  - `test_low_priority_backward_compatibility()`: `low_priority`属性の後方互換性を検証

#### InterestMaster リポジトリのテスト（`tests/unit/repositories/test_interest_master.py`）
- **既存テストの修正**:
  - `temp_interests_yaml` フィクスチャ: 5段階のYAMLに変更
  - `test_get_profile_success()`: 5フィールドの読み込みを検証
- **新規テスト**:
  - `test_get_profile_backward_compatibility()`: 旧形式（3段階）のYAMLも読み込めることを検証

#### BuzzScorer サービスのテスト（`tests/unit/services/test_buzz_scorer.py`）
- **既存テストの修正**:
  - `test_calculate_interest_score_high()`: 85点を返すことを検証
  - `test_calculate_interest_score_medium()`: 70点を返すことを検証
  - `test_calculate_interest_score_low()`: 50点を返すことを検証（`low_priority` → `low_interest`）
- **新規テスト**:
  - `test_calculate_interest_score_max()`: max_interest にマッチした場合、100点を返す
  - `test_calculate_interest_score_ignore()`: ignore_interest にマッチした場合、0点を返す
  - `test_calculate_interest_score_default()`: いずれにもマッチしない場合、50点を返す

## 実装の順序

1. **InterestProfile モデルの拡張**
   - テスト追加（RED）
   - フィールド追加（GREEN）
   - `format_for_prompt()` メソッド修正（GREEN）
   - リファクタリング（REFACTOR）

2. **InterestMaster リポジトリの修正**
   - テスト追加（RED）
   - YAML読み込みロジック修正（GREEN）
   - 後方互換性のテスト（RED → GREEN）
   - リファクタリング（REFACTOR）

3. **BuzzScorer サービスの修正**
   - テスト追加（RED）
   - スコア計算ロジック修正（GREEN）
   - リファクタリング（REFACTOR）

4. **interests.yaml の更新**
   - 5段階の構造に変更
   - 既存トピックの再配置

5. **品質チェック**
   - すべてのテストが通ることを確認
   - リント・型チェック・フォーマットチェック

## エラーハンドリング戦略

### バリデーション
- InterestMaster で YAML 読み込み時にフィールドの存在確認
- 存在しないフィールドは空リスト `[]` として初期化
- 後方互換性のため、`low_priority` が存在する場合は `low_interest` にマッピング

### エラーハンドリングパターン
- 既存のエラーハンドリングを維持（FileNotFoundError, ValueError）
- 新規のエラーは発生しない（後方互換性を保つため）

## パフォーマンス考慮事項

- スコア計算は O(n×m) （n: 記事数, m: トピック数）
- トピック数が5段階に増えても、マッチング処理は早期リターンするため影響は軽微
- キャッシュ機構（InterestMaster._profile）は既存のまま維持

## 将来の拡張性

- 各段階のスコアを設定ファイルで指定可能にする（現在はハードコード）
- トピックの重み付けを段階ごとに調整可能にする
- LLM判定時に5段階の関心度を活用する（現在は4段階のInterestLabel）
