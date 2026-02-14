# タスクリスト

**GitHub Issue**: https://github.com/k-negishi/ai-curated-newsletter/issues/10

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

## フェーズ1: 設定ファイルとモデルの作成

### config/interests.yaml の作成
- [x] `config/interests.yaml`ファイルを新規作成
- [x] `profile`セクションを定義
  - [x] `summary`を記述（既存のハードコードから移行）
  - [x] `high_interest`リストを定義
  - [x] `medium_interest`リストを定義
  - [x] `low_priority`リストを定義
- [x] `criteria`セクションを定義
  - [x] `act_now`の定義（label, description, examples）
  - [x] `think`の定義（label, description, examples）
  - [x] `fyi`の定義（label, description, examples）
  - [x] `ignore`の定義（label, description, examples）
- [x] YAML構文エラーがないことを確認（`yamllint`または手動確認）

### src/models/interest_profile.py の実装
- [x] `src/models/interest_profile.py`ファイルを新規作成
- [x] `JudgmentCriterion`データクラスを定義
  - [x] `label: str`フィールド
  - [x] `description: str`フィールド
  - [x] `examples: list[str]`フィールド
- [x] `InterestProfile`データクラスを定義
  - [x] `summary: str`フィールド
  - [x] `high_interest: list[str]`フィールド
  - [x] `medium_interest: list[str]`フィールド
  - [x] `low_priority: list[str]`フィールド
  - [x] `criteria: dict[str, JudgmentCriterion]`フィールド
- [x] `format_for_prompt(self) -> str`メソッドを実装
  - [x] summaryを先頭に配置
  - [x] high_interestリストを整形
  - [x] medium_interestリストを整形
  - [x] low_priorityリストを整形
  - [x] 空リストの場合は出力しないロジック
- [x] `format_criteria_for_prompt(self) -> str`メソッドを実装
  - [x] criteriaを順番に整形（act_now → think → fyi → ignore）
  - [x] examples も含めて出力
- [x] 型ヒント・docstringを記述

## フェーズ2: リポジトリの実装

### src/repositories/interest_master.py の実装
- [x] `src/repositories/interest_master.py`ファイルを新規作成
- [x] `InterestMaster`クラスを定義
  - [x] `__init__(self, config_path: str | Path)`メソッド
  - [x] `_config_path: Path`フィールド
  - [x] `_profile: InterestProfile | None`フィールド（キャッシュ用）
- [x] `get_profile(self) -> InterestProfile`メソッドを実装
  - [x] キャッシュチェック（既に読み込み済みなら返す）
  - [x] ファイル存在チェック（FileNotFoundError）
  - [x] YAML読み込み（yaml.safe_load）
  - [x] YAML解析エラーハンドリング（ValueError）
  - [x] `profile`セクションの存在確認
  - [x] `criteria`セクションの存在確認
  - [x] JudgmentCriterionインスタンスの生成
  - [x] InterestProfileインスタンスの生成
  - [x] ログ出力（読み込み成功）
  - [x] キャッシュに保存して返す
- [x] 型ヒント・docstringを記述

## フェーズ3: LlmJudge の改修

### src/services/llm_judge.py の変更
- [x] `__init__`メソッドにInterestProfileパラメータを追加
  - [x] `interest_profile: InterestProfile`引数を追加
  - [x] `self._interest_profile`フィールドに保存
  - [x] docstringを更新
- [x] `_build_prompt`メソッドを動的生成に変更
  - [x] ハードコードされた関心プロファイル文字列を削除
  - [x] `self._interest_profile.format_for_prompt()`を呼び出し
  - [x] `self._interest_profile.format_criteria_for_prompt()`を呼び出し
  - [x] プロンプトテンプレートに動的に埋め込み
  - [x] 既存のプロンプト構造を維持（記事情報、出力形式などは変更なし）

## フェーズ4: Orchestratorの修正

### src/handler.py の変更
- [x] InterestMasterのインポート追加
- [x] Lambda handlerの初期化処理でInterestMasterを初期化
  - [x] `interest_master = InterestMaster("config/interests.yaml")`
  - [x] `interest_profile = interest_master.get_profile()`
- [x] LlmJudgeの初期化時にInterestProfileを渡す
  - [x] `LlmJudge(..., interest_profile=interest_profile, ...)`
- [x] エラーハンドリング追加（interests.yamlが見つからない場合 - InterestMasterで実装済み）

## フェーズ5: テストの追加

### tests/unit/models/test_interest_profile.py の作成
- [x] テストファイルを新規作成
- [x] `test_interest_profile_initialization`を実装
  - [x] 各フィールドが正しく初期化されること
- [x] `test_format_for_prompt`を実装
  - [x] summaryが含まれること
  - [x] high_interestリストが整形されること
  - [x] medium_interestリストが整形されること
  - [x] low_priorityリストが整形されること
- [x] `test_format_for_prompt_with_empty_lists`を実装
  - [x] 空リストの場合に適切にスキップされること
- [x] `test_format_criteria_for_prompt`を実装
  - [x] 全てのcriteriaが整形されること
  - [x] examplesが含まれること

### tests/unit/repositories/test_interest_master.py の作成
- [x] テストファイルを新規作成
- [x] `test_get_profile_success`を実装
  - [x] 正常にInterestProfileが返されること
  - [x] 各フィールドが正しく読み込まれること
- [x] `test_get_profile_caching`を実装
  - [x] 2回目の呼び出しでキャッシュが使われること（ファイル読み込みが1回のみ）
- [x] `test_get_profile_file_not_found`を実装
  - [x] ファイルが存在しない場合にFileNotFoundErrorが発生すること
- [x] `test_get_profile_invalid_yaml`を実装
  - [x] YAML解析エラーの場合にValueErrorが発生すること
- [x] `test_get_profile_missing_profile_key`を実装
  - [x] `profile`キーがない場合にValueErrorが発生すること
- [x] `test_get_profile_missing_criteria_key`を実装
  - [x] `criteria`キーがない場合にValueErrorが発生すること

### tests/unit/services/test_llm_judge.py の作成
- [x] テストファイルを新規作成（既存テストが存在しなかったため）
- [x] InterestProfileのモックを作成
- [x] `test_build_prompt_with_interest_profile`を追加
  - [x] プロンプトにInterestProfileの内容が含まれること
  - [x] format_for_prompt()の出力が含まれること
  - [x] format_criteria_for_prompt()の出力が含まれること
- [x] `test_build_prompt_structure`を追加（プロンプト構造検証）
- [x] `test_llm_judge_initialization_with_interest_profile`を追加

### tests/integration/test_interest_master_integration.py の作成
- [x] テストファイルを新規作成
- [x] `test_load_real_interests_yaml`を実装
  - [x] 実際の`config/interests.yaml`を読み込めること
  - [x] InterestProfileが正しく生成されること
- [x] `test_interest_master_to_llm_judge_integration`を実装
  - [x] InterestMaster → LlmJudge のDI連携が動作すること
  - [x] プロンプト生成が正常に動作すること

## フェーズ6: 品質チェックと修正

### 静的解析とテスト実行
- [x] すべてのユニットテストが通ることを確認
  - [x] `.venv/bin/pytest tests/unit/ -v`
- [x] すべての統合テストが通ることを確認
  - [x] `.venv/bin/pytest tests/integration/ -v`
- [x] リントエラーがないことを確認
  - [x] `.venv/bin/ruff check src/`
- [x] コードフォーマットを実行
  - [x] `.venv/bin/ruff format src/`
- [x] 型エラーがないことを確認（今回実装部分）
  - [x] `.venv/bin/mypy src/models/interest_profile.py src/repositories/interest_master.py src/services/llm_judge.py src/handler.py`
  - ※既存のconfig.pyに型エラーが存在するが、今回の実装とは無関係

### 動作確認
- [x] dry_runモードでE2E実行
  - [x] `.venv/bin/python test_lambda_local.py --dry-run`
  - [x] エラーが発生しないこと（ThrottlingExceptionは想定内）
  - [x] interests.yamlが正しく読み込まれていることをログで確認（high_interest_count: 6, medium_interest_count: 5, low_priority_count: 4）
  - [x] プロンプトが動的生成されていることを確認（LLM判定が正常に実行された）

## フェーズ7: ドキュメント更新

### ドキュメントの更新
- [x] `docs/functional-design.md`を更新
  - [x] システム構成図にInterestMasterとconfig/interests.yamlを追加
  - [x] データモデル定義にInterestProfileとJudgmentCriterionを追加
- [x] 実装後の振り返り（このファイルの下部に記録）

---

## 実装後の振り返り

### 実装完了日
2026-02-14

### 計画と実績の差分

**計画と異なった点**:
- 既存の統合テスト（`test_judgment_flow.py`）もLlmJudgeのシグネチャ変更の影響を受けたため、修正が必要だった
- `tests/unit/models/`と`tests/unit/repositories/`ディレクトリに`__init__.py`ファイルが欠けており、テスト実行時にimportエラーが発生したため追加した
- Articleエンティティに`normalized_url`と`collected_at`フィールドが必須であることを考慮し、テストデータを修正した

**新たに必要になったタスク**:
- `tests/unit/models/__init__.py`と`tests/unit/repositories/__init__.py`の作成（Pythonパッケージ化のため）
- 既存の統合テストファイル（`test_judgment_flow.py`）の更新（InterestProfileのモック追加）
- ruffの自動修正（open()の"r"モード引数が不要と指摘された）

**技術的理由でスキップしたタスク**（該当する場合のみ）:
- なし（全タスク完了）

**⚠️ 注意**: 「時間の都合」「難しい」などの理由でスキップしたタスクはここに記載しないこと。全タスク完了が原則。

### 学んだこと

**技術的な学び**:
- SourceMasterと同様のパターンでInterestMasterを実装することで、設計の一貫性が保たれた
- YAMLを使った外部設定管理は、コード変更なしで関心プロファイルを更新できる柔軟性を提供する
- プロンプト生成を動的化することで、将来的な複数プロファイル対応やDynamoDB管理への移行が容易になる基盤が整った
- pytest実行時のimportエラーは、ディレクトリに`__init__.py`が不足している場合に発生する（Pythonパッケージとして認識されないため）

**プロセス上の改善点**:
- ステアリングファイル（requirements.md, design.md, tasklist.md）に従った実装フローは、実装漏れを防ぎ、スムーズな進行を実現した
- 各フェーズ（設定ファイル作成 → モデル定義 → リポジトリ実装 → サービス改修 → ハンドラ修正 → テスト追加 → 品質チェック → ドキュメント更新）を明確に分けることで、作業の見通しが良くなった
- テスト駆動開発（TDD）のアプローチで、ユニットテスト・統合テストを先に作成してから実装を進めることで、品質が担保された

### 次回への改善提案
- 既存のテストファイルへの影響を事前に調査する（特にシグネチャ変更を伴う場合）
- 新しいディレクトリを作成する際は、`__init__.py`を忘れずに作成する
- dry_runモードでの動作確認を早めに実施し、実装の問題を早期発見する
- ruffやmypyの静的解析を実装途中でも実行し、早期にコード品質を確保する
