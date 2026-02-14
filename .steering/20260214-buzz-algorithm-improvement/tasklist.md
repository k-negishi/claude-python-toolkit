# タスクリスト

**GitHub Issue**: https://github.com/k-negishi/ai-curated-newsletter/issues/11

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

## フェーズ1: 設定ファイルとモデルの更新

### config/sources.yaml の更新
- [x] `authority_level`フィールドを各ソースに追加
  - [x] aws_blog: `authority_level: official`
  - [x] hatena_bookmark_tech: `authority_level: medium`
  - [x] zenn_trend: `authority_level: medium`
  - [x] qiita_trend: `authority_level: medium`
  - [x] hacker_news: `authority_level: medium`
- [x] YAML構文エラーがないことを確認

### src/repositories/source_master.py の更新
- [x] `AuthorityLevel` Enumを定義
  - [x] `OFFICIAL = "official"`
  - [x] `HIGH = "high"`
  - [x] `MEDIUM = "medium"`
  - [x] `LOW = "low"`
- [x] `SourceConfig`データクラスに`authority_level`フィールドを追加
  - [x] `authority_level: AuthorityLevel = AuthorityLevel.LOW`（デフォルト値）
- [x] `SourceMaster.get_all_sources()`でauthority_levelを読み込む
  - [x] YAML内の`authority_level`文字列をAuthorityLevel Enumに変換（pydanticが自動処理）
  - [x] 省略時はLOWをデフォルト設定
- [x] 型ヒント・docstringを更新

### src/models/buzz_score.py の更新
- [x] 既存フィールド（`domain_diversity_score`）を削除
- [x] 新しいフィールドを追加
  - [x] `recency_score: float`（既存を維持）
  - [x] `consensus_score: float`（source_count_scoreから改名）
  - [x] `social_proof_score: float`（新規）
  - [x] `interest_score: float`（新規）
  - [x] `authority_score: float`（新規）
  - [x] `social_proof_count: int`（新規、メタデータ）
  - [x] `source_count: int`（既存を維持）
  - [x] `total_score: float`（既存を維持）
- [x] docstringを更新

## フェーズ2: SocialProofFetcher の実装

### src/services/social_proof_fetcher.py の新規作成
- [x] `src/services/social_proof_fetcher.py`ファイルを作成
- [x] `SocialProofFetcher`クラスを定義
  - [x] `__init__(self, timeout: int = 5, concurrency_limit: int = 10)`
  - [x] `HATENA_API_URL`定数を定義
- [x] `fetch_batch(self, urls: list[str]) -> dict[str, int]`メソッドを実装
  - [x] asyncio.Semaphoreで並列度制限
  - [x] 各URLに対して`_fetch_single`を並列実行
  - [x] asyncio.gather()で結果を集約
  - [x] 例外を個別にハンドリング（failed_count記録）
  - [x] ログ出力（開始、完了、成功/失敗件数）
- [x] `_fetch_single(self, url: str) -> int`メソッドを実装
  - [x] httpx.AsyncClientでGETリクエスト
  - [x] タイムアウト設定
  - [x] レスポンスをint変換
  - [x] エラー時は0を返す（ログ記録）
- [x] 型ヒント・docstringを記述

## フェーズ3: BuzzScorer の改修

### src/services/buzz_scorer.py の大幅改修
- [x] クラス変数で重み定数を定義
  - [x] `WEIGHT_RECENCY = 0.25`
  - [x] `WEIGHT_CONSENSUS = 0.20`
  - [x] `WEIGHT_SOCIAL_PROOF = 0.20`
  - [x] `WEIGHT_INTEREST = 0.25`
  - [x] `WEIGHT_AUTHORITY = 0.10`
- [x] `__init__`メソッドを更新
  - [x] `interest_profile: InterestProfile`引数を追加
  - [x] `source_master: SourceMaster`引数を追加
  - [x] `social_proof_fetcher: SocialProofFetcher`引数を追加
  - [x] 各フィールドに保存
  - [x] docstringを更新
- [x] `calculate_scores`メソッドを非同期版に変更
  - [x] `async def calculate_scores(self, articles: list[Article])`
  - [x] `await self._social_proof_fetcher.fetch_batch(urls)`を呼び出し
  - [x] URL出現回数を集計（Consensus用）
  - [x] 各記事に対して5要素スコアを計算
  - [x] BuzzScoreインスタンスを生成（新しいフィールド含む）
  - [x] ログ出力を更新（5要素の詳細を含む）
- [x] `_calculate_recency_score`メソッドを維持（既存ロジック）
- [x] `_calculate_consensus_score`メソッドを実装（既存の_calculate_source_count_scoreから改名）
- [x] `_calculate_social_proof_score`メソッドを実装
  - [x] はてブ数に応じたスコア分岐（0, 20, 50, 70, 100）
- [x] `_calculate_interest_score`メソッドを実装
  - [x] タイトル+概要のテキスト結合
  - [x] high_interestトピックとのマッチング（100点）
  - [x] medium_interestトピックとのマッチング（60点）
  - [x] low_priorityトピックとのマッチング（20点）
  - [x] いずれにも一致しない場合は40点
- [x] `_match_topic`メソッドを実装
  - [x] トピック文字列からキーワードを抽出
  - [x] 括弧外のメインキーワード
  - [x] 括弧内のサブキーワード（「、」「,」で分割）
  - [x] 記事テキストとの部分一致判定
- [x] `_calculate_authority_score`メソッドを実装
  - [x] source_nameからSourceConfigを検索
  - [x] authority_levelに応じたスコア（0, 50, 80, 100）
- [x] `_calculate_total_score`メソッドを更新
  - [x] 5要素の重み付け合算
  - [x] domain_diversity_scoreを削除
- [x] 既存の`_calculate_domain_diversity_score`メソッドを削除

## フェーズ4: Orchestrator の改修

### src/orchestrator/orchestrator.py の変更
- [x] SocialProofFetcherのインポート追加
- [x] `execute`メソッドを非同期対応に変更（または内部で非同期処理）
  - [x] SocialProofFetcherを初期化（handler.pyで実施）
  - [x] BuzzScorerの初期化時にinterest_profile、source_master、social_proof_fetcherを渡す（handler.pyで実施）
  - [x] `buzz_scores = await buzz_scorer.calculate_scores(articles)`に変更
- [x] エラーハンドリング追加（はてブAPI失敗時も継続、SocialProofFetcher内で実装済み）

## フェーズ5: テストの追加

### tests/unit/services/test_social_proof_fetcher.py の作成
- [x] テストファイルを新規作成
- [x] `test_fetch_single_success`を実装
  - [x] はてブAPI正常レスポンスをモック
  - [x] 正しい件数が返されること
- [x] `test_fetch_single_timeout`を実装
  - [x] タイムアウト発生時に0が返されること
- [x] `test_fetch_single_http_error`を実装
  - [x] HTTPエラー時に0が返されること
- [x] `test_fetch_batch_success`を実装
  - [x] 複数URLの一括取得が成功すること
- [x] `test_fetch_batch_partial_failure`を実装
  - [x] 一部失敗時も継続すること

### tests/unit/services/test_buzz_scorer.py の更新
- [x] 既存テストを確認・削除（domain_diversity関連）
- [x] `test_calculate_recency_score`を実装
  - [x] 鮮度スコアの計算ロジック検証
  - [x] 境界値テスト（0日、10日以上）
- [x] `test_calculate_consensus_score`を実装
  - [x] Consensusスコアの計算ロジック検証
  - [x] 境界値テスト（1ソース、5ソース以上）
- [x] `test_calculate_social_proof_score`を実装
  - [x] はてブ数に応じたスコア分岐検証
  - [x] 境界値テスト（0, 1, 10, 50, 100）
- [x] `test_calculate_interest_score`を実装
  - [x] InterestProfileのモック作成
  - [x] high_interest一致時に100点
  - [x] medium_interest一致時に60点
  - [x] low_priority一致時に20点
  - [x] 一致なし時に40点
- [x] `test_match_topic`を実装
  - [x] キーワード抽出ロジック検証
  - [x] 括弧内・括弧外のキーワード
  - [x] 部分一致判定
- [x] `test_calculate_authority_score`を実装
  - [x] SourceMasterのモック作成
  - [x] authority_levelに応じたスコア検証
- [x] `test_calculate_total_score`を実装
  - [x] 重み配分の検証
  - [x] 合計が正しく計算されること

### tests/unit/models/test_buzz_score.py の更新
- [x] BuzzScoreの新しいフィールドを含むインスタンス生成テスト
- [x] 各フィールドの型検証

### tests/integration/test_buzz_scorer_integration.py の作成
- [x] テストファイルを新規作成
- [x] `test_buzz_scorer_with_real_dependencies`を実装
  - [x] 実際のInterestProfile、SourceMasterを使用
  - [x] SocialProofFetcherはモック
  - [x] 5要素が正しく計算されること
- [x] `test_no_single_element_dominates`を実装
  - [x] 単一要素が支配しないことを検証
  - [x] 高Recencyのみの記事が100点にならないこと
  - [x] 高SocialProofのみの記事が100点にならないこと
- [x] `test_no_missing_important_articles`を実装
  - [x] 公式ブログ（Authority高）が低SocialProofでも一定スコア維持
  - [x] Interest一致記事が同条件で優先
  - [x] 話題記事（SocialProof高）が興味外でも一定スコア維持

## フェーズ6: 品質チェックと修正

### 静的解析とテスト実行
- [x] すべてのユニットテストが通ることを確認
  - [x] `.venv/bin/pytest tests/unit/ -v` （84件全てパス）
- [x] すべての統合テストが通ることを確認
  - [x] `.venv/bin/pytest tests/integration/ -v` （20件全てパス）
- [x] リントエラーがないことを確認
  - [x] `.venv/bin/ruff check src/` （All checks passed）
- [x] コードフォーマットを実行
  - [x] `.venv/bin/ruff format src/` （38 files unchanged）
- [x] 型エラーがないことを確認
  - [x] `.venv/bin/mypy src/` （Success: no issues found）

### 動作確認
- [x] dry_runモードでE2E実行
  - [x] `python test_lambda_local.py --dry-run`（成功）
  - [x] エラーが発生しないこと（一部LLM ThrottlingExceptionでも処理継続）
  - [x] 5要素のスコアが正しく計算されていることをログで確認（79件全て成功）
  - [x] はてブAPI呼び出しが動作していることを確認（79件/79件成功）
  - [x] 総合スコアのバランスを確認（上位30件選定→最終12件選定）

## フェーズ7: ドキュメント更新

### ドキュメントの更新
- [x] `docs/functional-design.md`を更新
  - [x] Buzzスコア計算アルゴリズムのセクションを更新
  - [x] 5要素の説明を追加
  - [x] 重み配分を記載
- [x] 実装後の振り返り（このファイルの下部に記録）

---

## 実装後の振り返り

### 実装完了日
2026-02-14

### 計画と実績の差分

**計画と異なった点**:
- 統合テスト作成時、実際のconfig/interests.yamlの内容に合わせてテストケースを調整する必要があった
  - 理由: テスト設計時に想定したキーワードと実際のInterestProfileの内容が異なっていた
  - 対応: "AI/ML"キーワードを"PostgreSQL"や"Claude"などの実際のキーワードに変更
- SourceMasterの実装は変更不要だった（pydanticが自動的にYAMLのauthority_levelをEnumに変換）
  - 理由: pydanticのバリデーション機能により、追加のコードが不要だった
  - タスクリストのコメントを追加: 「pydanticが自動処理」

**新たに必要になったタスク**:
- なし（計画したタスクで全て対応できた）

**技術的理由でスキップしたタスク**:
- なし（全タスク完了）

### 学んだこと

**技術的な学び**:
- 5要素統合型のスコアリングシステムの設計パターン
  - 各要素を独立したメソッドで実装することで、テスタビリティと保守性が向上
  - 重み定数をクラス変数で管理することで、将来的なYAML化が容易
- 非同期処理（asyncio）とモック（AsyncMock）の組み合わせ
  - SocialProofFetcher（非同期）のテストでAsyncMockを使用
  - pytest.mark.asyncioでテストを非同期実行
- pydanticの自動型変換機能
  - YAMLの文字列がEnumに自動変換されるため、追加のコードが不要

**プロセス上の改善点**:
- TDDサイクル（RED → GREEN → REFACTOR）の徹底により、高品質なコードを効率的に実装
  - テスト先行で実装することで、要件の明確化とリグレッション防止を実現
  - カバレッジ100%を達成（BuzzScorer, SocialProofFetcher, BuzzScoreモデル）
- 統合テストで実際の設定ファイル（config/interests.yaml, config/sources.yaml）を使用
  - 実際の動作環境に近い条件でテスト実行
  - テストと本番の乖離を最小化

### 次回への改善提案

**機能追加での気をつけること**:
- 実際の設定ファイル（interests.yaml, sources.yamlなど）の内容を事前に確認してからテストケースを設計する
- 非同期処理を含む場合は、早い段階でAsyncMockの使用方法を確認する
- E2E実行（dry_run）は実際のAPI呼び出しが発生するため、テスト環境の準備（AWS認証情報など）を確認

**より効率的な実装方法**:
- 大規模な改修の場合、フェーズごとに小さくリリースすることを検討
  - 例: Phase 1で3要素→4要素、Phase 2で4要素→5要素など
  - ただし、今回のように一気に実装する方が整合性を保ちやすい場合もある
- 統合テストと単体テストのバランス
  - 単体テスト: 各メソッドの動作を詳細に検証（カバレッジ重視）
  - 統合テスト: 実際のユースケースを検証（実用性重視）

**タスク計画の改善点**:
- テスト作成タスクをより細かく分割（fixture作成、各テストケースごとなど）
  - ただし、今回のように一気に作成する方が効率的な場合もある
- ドキュメント更新タスクを実装完了直後に実施する
  - 実装内容を忘れないうちにドキュメント化する
