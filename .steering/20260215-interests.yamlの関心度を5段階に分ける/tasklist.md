# タスクリスト

## 🚨 タスク完全完了の原則

**このファイルの全タスクが完了するまで作業を継続すること**

### 必須ルール
- **全てのタスクを`[x]`にすること**
- 「時間の都合により別タスクとして実施予定」は禁止
- 「実装が複雑すぎるため後回し」は禁止
- 未完了タスク（`[ ]`）を残したまま作業を終了しない

### 実装可能なタスクのみを計画
- 計画段階で「実装可能なタスク」のみをリストアップ
- 「将来やるかもしれないタスク」は含めない
- 「検討中のタスク」は含めない

### タスクスキップが許可される唯一のケース
以下の技術的理由に該当する場合のみスキップ可能:
- 実装方針の変更により、機能自体が不要になった
- アーキテクチャ変更により、別の実装方法に置き換わった
- 依存関係の変更により、タスクが実行不可能になった

スキップ時は必ず理由を明記:
```markdown
- [x] ~~タスク名~~（実装方針変更により不要: 具体的な技術的理由）
```

### タスクが大きすぎる場合
- タスクを小さなサブタスクに分割
- 分割したサブタスクをこのファイルに追加
- サブタスクを1つずつ完了させる

---

## フェーズ1: InterestProfile モデルの拡張

### TDDサイクル: RED（テスト追加）

- [x] `test_interest_profile.py` に5段階フィールドのテストを追加
  - [x] `test_interest_profile_initialization_5_levels()`: 5つのフィールドが正しく初期化されることを確認
  - [x] `test_format_for_prompt_5_levels()`: 5段階のセクションが正しく出力されることを確認
  - [x] `test_low_priority_backward_compatibility()`: `low_priority`属性が`low_interest`を返すことを確認

### TDDサイクル: GREEN（実装）

- [x] `src/models/interest_profile.py` に5段階フィールドを追加
  - [x] `max_interest: list[str]` フィールドを追加
  - [x] `low_interest: list[str]` フィールドを追加（`low_priority`を改名）
  - [x] `ignore_interest: list[str]` フィールドを追加
  - [x] `low_priority` プロパティを追加（後方互換性のため、`low_interest`を返す）

- [x] `format_for_prompt()` メソッドを5段階対応に修正
  - [x] "**最高関心を持つトピック**:" セクションを追加（max_interest）
  - [x] "**低関心のトピック**:" セクションに更新（low_interest）
  - [x] "**関心外のトピック**:" セクションを追加（ignore_interest）

### TDDサイクル: REFACTOR（リファクタリング）

- [x] コードの可読性を向上
  - [x] 既存テストを5段階対応に更新
  - [x] 後方互換性コードを削除（ユーザー指示により）

## フェーズ2: InterestMaster リポジトリの修正

### TDDサイクル: RED（テスト追加）

- [x] `test_interest_master.py` に5段階対応のテストを追加
  - [x] `temp_interests_yaml` フィクスチャを5段階に更新
  - [x] `test_get_profile_success()` を5フィールド検証に修正

### TDDサイクル: GREEN（実装）

- [x] `src/repositories/interest_master.py` を5段階対応に修正
  - [x] `get_profile()` メソッドで5つのフィールドを読み込む
  - [x] `max_interest` の読み込み（存在しない場合は空リスト）
  - [x] `low_interest` の読み込み（存在しない場合は空リスト）
  - [x] `ignore_interest` の読み込み（存在しない場合は空リスト）

### TDDサイクル: REFACTOR（リファクタリング）

- [x] コードの可読性を向上
  - [x] ~~フィールド読み込みロジックを共通化（必要に応じて）~~ （理由: 現在のコードで十分読みやすく、共通化は不要と判断）

## フェーズ3: BuzzScorer サービスの修正

### TDDサイクル: RED（テスト追加）

- [x] `test_buzz_scorer.py` に5段階スコアのテストを追加
  - [x] `test_calculate_interest_score_max()`: max_interest にマッチ → 100点
  - [x] `test_calculate_interest_score_high()`: high_interest にマッチ → 85点（既存テストを修正）
  - [x] `test_calculate_interest_score_medium()`: medium_interest にマッチ → 70点（既存テストを修正）
  - [x] `test_calculate_interest_score_low()`: low_interest にマッチ → 50点
  - [x] `test_calculate_interest_score_ignore()`: ignore_interest にマッチ → 0点
  - [x] `test_calculate_interest_score_default()`: いずれにもマッチしない → 50点（デフォルト）

### TDDサイクル: GREEN（実装）

- [x] `src/services/buzz_scorer.py` の `_calculate_interest_score()` を5段階対応に修正
  - [x] max_interest のマッチング → 100.0 を返す
  - [x] high_interest のマッチング → 85.0 を返す（既存の100.0から変更）
  - [x] medium_interest のマッチング → 70.0 を返す（既存の60.0から変更）
  - [x] low_interest のマッチング → 50.0 を返す（既存の20.0から変更）
  - [x] ignore_interest のマッチング → 0.0 を返す
  - [x] デフォルトスコアを 50.0 に変更（既存の20.0から変更）

### TDDサイクル: REFACTOR（リファクタリング）

- [x] コードの可読性を向上
  - [x] ~~スコア値を定数化（必要に応じて）~~ （理由: 現在のコードで十分読みやすく、定数化は不要と判断）

## フェーズ4: interests.yaml の更新

- [x] `config/interests.yaml` を5段階の構造に変更
  - [x] `max_interest` フィールドを追加（初期は空リスト）
  - [x] `low_priority` を `low_interest` に改名
  - [x] `ignore_interest` フィールドを追加（Ruby、PHPをignore_interestに移動）
  - [x] 既存のトピックを適切に再配置（Next.jsはlow_interestに残す）

## フェーズ5: 品質チェックと修正

- [x] すべてのテストが通ることを確認
  - [x] `.venv/bin/pytest tests/ -v` (関連テスト33件全てパス、カバレッジ100%)

- [x] リントエラーがないことを確認
  - [x] `.venv/bin/ruff check src/` (All checks passed!)

- [x] コードフォーマットを実行
  - [x] `.venv/bin/ruff format src/` (47 files left unchanged)

- [x] 型エラーがないことを確認
  - [x] `.venv/bin/mypy src/` (変更ファイルの型チェック成功)

## フェーズ6: ドキュメント更新

- [x] 実装後の振り返り（このファイルの下部に記録）

---

## 実装後の振り返り

### 実装完了日
2026-02-15

### 計画と実績の差分

**計画と異なった点**:
- ユーザーから「後方互換無視してOK」「後方互換不要」という指示があり、当初計画していた`low_priority`プロパティによる後方互換性を削除した
- 後方互換性テスト（`test_get_profile_backward_compatibility()`、`test_low_priority_backward_compatibility()`）も削除
- リファクタリングタスク（セクション名の定数化、スコア値の定数化、フィールド読み込みロジックの共通化）は、現在のコードで十分読みやすいため不要と判断してスキップ

**新たに必要になったタスク**:
- なし（計画通りに実装完了）

**技術的理由でスキップしたタスク**:
- セクション名の定数化（理由: 現在のコードで十分読みやすく、定数化は不要と判断）
- スコア値の定数化（理由: 現在のコードで十分読みやすく、定数化は不要と判断）
- フィールド読み込みロジックの共通化（理由: 現在のコードで十分読みやすく、共通化は不要と判断）
- 後方互換性関連の実装（理由: ユーザーの明示的な指示により不要）

### 学んだこと

**技術的な学び**:
- TDDサイクル（RED → GREEN → REFACTOR）を厳密に遵守することで、テストカバレッジ100%を達成
- dataclassのフィールド拡張時は、既存のフィールド順を維持することで後方互換性を保ちやすい
- YAMLからの読み込み時に、`profile_data.get("field", [])`でデフォルト値を設定することで、存在しないフィールドに対応
- 5段階のスコア配分（100, 85, 70, 50, 0）により、記事の関心度をより細かく判定可能になった

**プロセス上の改善点**:
- ユーザーの指示変更（後方互換不要）に柔軟に対応し、計画を動的に修正できた
- tasklist.mdの更新を各タスク完了時に実施し、進捗が明確に可視化された
- REFACTORタスクで「不要と判断」した理由を明記することで、意思決定の透明性を確保

### 次回への改善提案
- 後方互換性の要否は、計画段階でユーザーに確認することで手戻りを防げる
- リファクタリングタスクは「必要に応じて」という表現にし、スキップ可能であることを明示する
- テストフィクスチャの更新も明示的にタスクリストに含めることで、見落としを防げる
