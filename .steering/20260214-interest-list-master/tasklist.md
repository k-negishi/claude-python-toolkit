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
- [ ] `config/interests.yaml`ファイルを新規作成
- [ ] `profile`セクションを定義
  - [ ] `summary`を記述（既存のハードコードから移行）
  - [ ] `high_interest`リストを定義
  - [ ] `medium_interest`リストを定義
  - [ ] `low_priority`リストを定義
- [ ] `criteria`セクションを定義
  - [ ] `act_now`の定義（label, description, examples）
  - [ ] `think`の定義（label, description, examples）
  - [ ] `fyi`の定義（label, description, examples）
  - [ ] `ignore`の定義（label, description, examples）
- [ ] YAML構文エラーがないことを確認（`yamllint`または手動確認）

### src/models/interest_profile.py の実装
- [ ] `src/models/interest_profile.py`ファイルを新規作成
- [ ] `JudgmentCriterion`データクラスを定義
  - [ ] `label: str`フィールド
  - [ ] `description: str`フィールド
  - [ ] `examples: list[str]`フィールド
- [ ] `InterestProfile`データクラスを定義
  - [ ] `summary: str`フィールド
  - [ ] `high_interest: list[str]`フィールド
  - [ ] `medium_interest: list[str]`フィールド
  - [ ] `low_priority: list[str]`フィールド
  - [ ] `criteria: dict[str, JudgmentCriterion]`フィールド
- [ ] `format_for_prompt(self) -> str`メソッドを実装
  - [ ] summaryを先頭に配置
  - [ ] high_interestリストを整形
  - [ ] medium_interestリストを整形
  - [ ] low_priorityリストを整形
  - [ ] 空リストの場合は出力しないロジック
- [ ] `format_criteria_for_prompt(self) -> str`メソッドを実装
  - [ ] criteriaを順番に整形（act_now → think → fyi → ignore）
  - [ ] examples も含めて出力
- [ ] 型ヒント・docstringを記述

## フェーズ2: リポジトリの実装

### src/repositories/interest_master.py の実装
- [ ] `src/repositories/interest_master.py`ファイルを新規作成
- [ ] `InterestMaster`クラスを定義
  - [ ] `__init__(self, config_path: str | Path)`メソッド
  - [ ] `_config_path: Path`フィールド
  - [ ] `_profile: InterestProfile | None`フィールド（キャッシュ用）
- [ ] `get_profile(self) -> InterestProfile`メソッドを実装
  - [ ] キャッシュチェック（既に読み込み済みなら返す）
  - [ ] ファイル存在チェック（FileNotFoundError）
  - [ ] YAML読み込み（yaml.safe_load）
  - [ ] YAML解析エラーハンドリング（ValueError）
  - [ ] `profile`セクションの存在確認
  - [ ] `criteria`セクションの存在確認
  - [ ] JudgmentCriterionインスタンスの生成
  - [ ] InterestProfileインスタンスの生成
  - [ ] ログ出力（読み込み成功）
  - [ ] キャッシュに保存して返す
- [ ] 型ヒント・docstringを記述

## フェーズ3: LlmJudge の改修

### src/services/llm_judge.py の変更
- [ ] `__init__`メソッドにInterestProfileパラメータを追加
  - [ ] `interest_profile: InterestProfile`引数を追加
  - [ ] `self._interest_profile`フィールドに保存
  - [ ] docstringを更新
- [ ] `_build_prompt`メソッドを動的生成に変更
  - [ ] ハードコードされた関心プロファイル文字列を削除
  - [ ] `self._interest_profile.format_for_prompt()`を呼び出し
  - [ ] `self._interest_profile.format_criteria_for_prompt()`を呼び出し
  - [ ] プロンプトテンプレートに動的に埋め込み
  - [ ] 既存のプロンプト構造を維持（記事情報、出力形式などは変更なし）

## フェーズ4: Orchestratorの修正

### src/orchestrator/orchestrator.py の変更
- [ ] InterestMasterのインポート追加
- [ ] Orchestratorの`__init__`または初期化処理でInterestMasterを初期化
  - [ ] `interest_master = InterestMaster("config/interests.yaml")`
  - [ ] `interest_profile = interest_master.get_profile()`
- [ ] LlmJudgeの初期化時にInterestProfileを渡す
  - [ ] `LlmJudge(..., interest_profile=interest_profile, ...)`
- [ ] エラーハンドリング追加（interests.yamlが見つからない場合）

## フェーズ5: テストの追加

### tests/unit/models/test_interest_profile.py の作成
- [ ] テストファイルを新規作成
- [ ] `test_interest_profile_initialization`を実装
  - [ ] 各フィールドが正しく初期化されること
- [ ] `test_format_for_prompt`を実装
  - [ ] summaryが含まれること
  - [ ] high_interestリストが整形されること
  - [ ] medium_interestリストが整形されること
  - [ ] low_priorityリストが整形されること
- [ ] `test_format_for_prompt_with_empty_lists`を実装
  - [ ] 空リストの場合に適切にスキップされること
- [ ] `test_format_criteria_for_prompt`を実装
  - [ ] 全てのcriteriaが整形されること
  - [ ] examplesが含まれること

### tests/unit/repositories/test_interest_master.py の作成
- [ ] テストファイルを新規作成
- [ ] `test_get_profile_success`を実装
  - [ ] 正常にInterestProfileが返されること
  - [ ] 各フィールドが正しく読み込まれること
- [ ] `test_get_profile_caching`を実装
  - [ ] 2回目の呼び出しでキャッシュが使われること（ファイル読み込みが1回のみ）
- [ ] `test_get_profile_file_not_found`を実装
  - [ ] ファイルが存在しない場合にFileNotFoundErrorが発生すること
- [ ] `test_get_profile_invalid_yaml`を実装
  - [ ] YAML解析エラーの場合にValueErrorが発生すること
- [ ] `test_get_profile_missing_profile_key`を実装
  - [ ] `profile`キーがない場合にValueErrorが発生すること
- [ ] `test_get_profile_missing_criteria_key`を実装
  - [ ] `criteria`キーがない場合にValueErrorが発生すること

### tests/unit/services/test_llm_judge.py の更新
- [ ] 既存のテストを確認
- [ ] InterestProfileのモックを作成
- [ ] `test_build_prompt_with_interest_profile`を追加
  - [ ] プロンプトにInterestProfileの内容が含まれること
  - [ ] format_for_prompt()の出力が含まれること
  - [ ] format_criteria_for_prompt()の出力が含まれること
- [ ] 既存のテストケースをInterestProfileを使用するよう更新

### tests/integration/test_interest_master_integration.py の作成
- [ ] テストファイルを新規作成
- [ ] `test_load_real_interests_yaml`を実装
  - [ ] 実際の`config/interests.yaml`を読み込めること
  - [ ] InterestProfileが正しく生成されること
- [ ] `test_interest_master_to_llm_judge_integration`を実装
  - [ ] InterestMaster → LlmJudge のDI連携が動作すること
  - [ ] プロンプト生成が正常に動作すること

## フェーズ6: 品質チェックと修正

### 静的解析とテスト実行
- [ ] すべてのユニットテストが通ることを確認
  - [ ] `.venv/bin/pytest tests/unit/ -v`
- [ ] すべての統合テストが通ることを確認
  - [ ] `.venv/bin/pytest tests/integration/ -v`
- [ ] リントエラーがないことを確認
  - [ ] `.venv/bin/ruff check src/`
- [ ] コードフォーマットを実行
  - [ ] `.venv/bin/ruff format src/`
- [ ] 型エラーがないことを確認
  - [ ] `.venv/bin/mypy src/`

### 動作確認
- [ ] dry_runモードでE2E実行
  - [ ] `python test_lambda_local.py --dry-run`
  - [ ] エラーが発生しないこと
  - [ ] interests.yamlが正しく読み込まれていることをログで確認
  - [ ] プロンプトが動的生成されていることを確認

## フェーズ7: ドキュメント更新

### ドキュメントの更新
- [ ] `docs/functional-design.md`を更新（必要に応じて）
  - [ ] InterestMasterの追加を記載
  - [ ] InterestProfileの説明を追加
- [ ] 実装後の振り返り（このファイルの下部に記録）

---

## 実装後の振り返り

### 実装完了日
{YYYY-MM-DD}

### 計画と実績の差分

**計画と異なった点**:
- {計画時には想定していなかった技術的な変更点}
- {実装方針の変更とその理由}

**新たに必要になったタスク**:
- {実装中に追加したタスク}
- {なぜ追加が必要だったか}

**技術的理由でスキップしたタスク**（該当する場合のみ）:
- {タスク名}
  - スキップ理由: {具体的な技術的理由}
  - 代替実装: {何に置き換わったか}

**⚠️ 注意**: 「時間の都合」「難しい」などの理由でスキップしたタスクはここに記載しないこと。全タスク完了が原則。

### 学んだこと

**技術的な学び**:
- {実装を通じて学んだ技術的な知見}
- {新しく使った技術やパターン}

**プロセス上の改善点**:
- {タスク管理で良かった点}
- {ステアリングファイルの活用方法}

### 次回への改善提案
- {次回の機能追加で気をつけること}
- {より効率的な実装方法}
- {タスク計画の改善点}
