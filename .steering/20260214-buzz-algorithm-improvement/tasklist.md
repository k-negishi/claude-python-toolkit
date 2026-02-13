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
- [ ] `authority_level`フィールドを各ソースに追加
  - [ ] aws_blog: `authority_level: official`
  - [ ] hatena_bookmark_tech: `authority_level: medium`
  - [ ] zenn_trend: `authority_level: medium`
  - [ ] qiita_trend: `authority_level: medium`
  - [ ] hacker_news: `authority_level: medium`
- [ ] YAML構文エラーがないことを確認

### src/repositories/source_master.py の更新
- [ ] `AuthorityLevel` Enumを定義
  - [ ] `OFFICIAL = "official"`
  - [ ] `HIGH = "high"`
  - [ ] `MEDIUM = "medium"`
  - [ ] `LOW = "low"`
- [ ] `SourceConfig`データクラスに`authority_level`フィールドを追加
  - [ ] `authority_level: AuthorityLevel = AuthorityLevel.LOW`（デフォルト値）
- [ ] `SourceMaster.get_all_sources()`でauthority_levelを読み込む
  - [ ] YAML内の`authority_level`文字列をAuthorityLevel Enumに変換
  - [ ] 省略時はLOWをデフォルト設定
- [ ] 型ヒント・docstringを更新

### src/models/buzz_score.py の更新
- [ ] 既存フィールド（`domain_diversity_score`）を削除
- [ ] 新しいフィールドを追加
  - [ ] `recency_score: float`（既存を維持）
  - [ ] `consensus_score: float`（source_count_scoreから改名）
  - [ ] `social_proof_score: float`（新規）
  - [ ] `interest_score: float`（新規）
  - [ ] `authority_score: float`（新規）
  - [ ] `social_proof_count: int`（新規、メタデータ）
  - [ ] `source_count: int`（既存を維持）
  - [ ] `total_score: float`（既存を維持）
- [ ] docstringを更新

## フェーズ2: SocialProofFetcher の実装

### src/services/social_proof_fetcher.py の新規作成
- [ ] `src/services/social_proof_fetcher.py`ファイルを作成
- [ ] `SocialProofFetcher`クラスを定義
  - [ ] `__init__(self, timeout: int = 5, concurrency_limit: int = 10)`
  - [ ] `HATENA_API_URL`定数を定義
- [ ] `fetch_batch(self, urls: list[str]) -> dict[str, int]`メソッドを実装
  - [ ] asyncio.Semaphoreで並列度制限
  - [ ] 各URLに対して`_fetch_single`を並列実行
  - [ ] asyncio.gather()で結果を集約
  - [ ] 例外を個別にハンドリング（failed_count記録）
  - [ ] ログ出力（開始、完了、成功/失敗件数）
- [ ] `_fetch_single(self, url: str) -> int`メソッドを実装
  - [ ] httpx.AsyncClientでGETリクエスト
  - [ ] タイムアウト設定
  - [ ] レスポンスをint変換
  - [ ] エラー時は0を返す（ログ記録）
- [ ] 型ヒント・docstringを記述

## フェーズ3: BuzzScorer の改修

### src/services/buzz_scorer.py の大幅改修
- [ ] クラス変数で重み定数を定義
  - [ ] `WEIGHT_RECENCY = 0.25`
  - [ ] `WEIGHT_CONSENSUS = 0.20`
  - [ ] `WEIGHT_SOCIAL_PROOF = 0.20`
  - [ ] `WEIGHT_INTEREST = 0.25`
  - [ ] `WEIGHT_AUTHORITY = 0.10`
- [ ] `__init__`メソッドを更新
  - [ ] `interest_profile: InterestProfile`引数を追加
  - [ ] `source_master: SourceMaster`引数を追加
  - [ ] `social_proof_fetcher: SocialProofFetcher`引数を追加
  - [ ] 各フィールドに保存
  - [ ] docstringを更新
- [ ] `calculate_scores`メソッドを非同期版に変更
  - [ ] `async def calculate_scores(self, articles: list[Article])`
  - [ ] `await self._social_proof_fetcher.fetch_batch(urls)`を呼び出し
  - [ ] URL出現回数を集計（Consensus用）
  - [ ] 各記事に対して5要素スコアを計算
  - [ ] BuzzScoreインスタンスを生成（新しいフィールド含む）
  - [ ] ログ出力を更新（5要素の詳細を含む）
- [ ] `_calculate_recency_score`メソッドを維持（既存ロジック）
- [ ] `_calculate_consensus_score`メソッドを実装（既存の_calculate_source_count_scoreから改名）
- [ ] `_calculate_social_proof_score`メソッドを実装
  - [ ] はてブ数に応じたスコア分岐（0, 20, 50, 70, 100）
- [ ] `_calculate_interest_score`メソッドを実装
  - [ ] タイトル+概要のテキスト結合
  - [ ] high_interestトピックとのマッチング（100点）
  - [ ] medium_interestトピックとのマッチング（60点）
  - [ ] low_priorityトピックとのマッチング（20点）
  - [ ] いずれにも一致しない場合は40点
- [ ] `_match_topic`メソッドを実装
  - [ ] トピック文字列からキーワードを抽出
  - [ ] 括弧外のメインキーワード
  - [ ] 括弧内のサブキーワード（「、」「,」で分割）
  - [ ] 記事テキストとの部分一致判定
- [ ] `_calculate_authority_score`メソッドを実装
  - [ ] source_nameからSourceConfigを検索
  - [ ] authority_levelに応じたスコア（0, 50, 80, 100）
- [ ] `_calculate_total_score`メソッドを更新
  - [ ] 5要素の重み付け合算
  - [ ] domain_diversity_scoreを削除
- [ ] 既存の`_calculate_domain_diversity_score`メソッドを削除

## フェーズ4: Orchestrator の改修

### src/orchestrator/orchestrator.py の変更
- [ ] SocialProofFetcherのインポート追加
- [ ] `execute`メソッドを非同期対応に変更（または内部で非同期処理）
  - [ ] SocialProofFetcherを初期化
  - [ ] BuzzScorerの初期化時にinterest_profile、source_master、social_proof_fetcherを渡す
  - [ ] `buzz_scores = await buzz_scorer.calculate_scores(articles)`に変更
- [ ] エラーハンドリング追加（はてブAPI失敗時も継続）

## フェーズ5: テストの追加

### tests/unit/services/test_social_proof_fetcher.py の作成
- [ ] テストファイルを新規作成
- [ ] `test_fetch_single_success`を実装
  - [ ] はてブAPI正常レスポンスをモック
  - [ ] 正しい件数が返されること
- [ ] `test_fetch_single_timeout`を実装
  - [ ] タイムアウト発生時に0が返されること
- [ ] `test_fetch_single_http_error`を実装
  - [ ] HTTPエラー時に0が返されること
- [ ] `test_fetch_batch_success`を実装
  - [ ] 複数URLの一括取得が成功すること
- [ ] `test_fetch_batch_partial_failure`を実装
  - [ ] 一部失敗時も継続すること

### tests/unit/services/test_buzz_scorer.py の更新
- [ ] 既存テストを確認・削除（domain_diversity関連）
- [ ] `test_calculate_recency_score`を実装
  - [ ] 鮮度スコアの計算ロジック検証
  - [ ] 境界値テスト（0日、10日以上）
- [ ] `test_calculate_consensus_score`を実装
  - [ ] Consensusスコアの計算ロジック検証
  - [ ] 境界値テスト（1ソース、5ソース以上）
- [ ] `test_calculate_social_proof_score`を実装
  - [ ] はてブ数に応じたスコア分岐検証
  - [ ] 境界値テスト（0, 1, 10, 50, 100）
- [ ] `test_calculate_interest_score`を実装
  - [ ] InterestProfileのモック作成
  - [ ] high_interest一致時に100点
  - [ ] medium_interest一致時に60点
  - [ ] low_priority一致時に20点
  - [ ] 一致なし時に40点
- [ ] `test_match_topic`を実装
  - [ ] キーワード抽出ロジック検証
  - [ ] 括弧内・括弧外のキーワード
  - [ ] 部分一致判定
- [ ] `test_calculate_authority_score`を実装
  - [ ] SourceMasterのモック作成
  - [ ] authority_levelに応じたスコア検証
- [ ] `test_calculate_total_score`を実装
  - [ ] 重み配分の検証
  - [ ] 合計が正しく計算されること

### tests/unit/models/test_buzz_score.py の更新
- [ ] BuzzScoreの新しいフィールドを含むインスタンス生成テスト
- [ ] 各フィールドの型検証

### tests/integration/test_buzz_scorer_integration.py の作成
- [ ] テストファイルを新規作成
- [ ] `test_buzz_scorer_with_real_dependencies`を実装
  - [ ] 実際のInterestProfile、SourceMasterを使用
  - [ ] SocialProofFetcherはモック
  - [ ] 5要素が正しく計算されること
- [ ] `test_no_single_element_dominates`を実装
  - [ ] 単一要素が支配しないことを検証
  - [ ] 高Recencyのみの記事が100点にならないこと
  - [ ] 高SocialProofのみの記事が100点にならないこと
- [ ] `test_no_missing_important_articles`を実装
  - [ ] 公式ブログ（Authority高）が低SocialProofでも一定スコア維持
  - [ ] Interest一致記事が同条件で優先
  - [ ] 話題記事（SocialProof高）が興味外でも一定スコア維持

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
  - [ ] 5要素のスコアが正しく計算されていることをログで確認
  - [ ] はてブAPI呼び出しが動作していることを確認
  - [ ] 総合スコアのバランスを確認（単一要素が支配していないか）

## フェーズ7: ドキュメント更新

### ドキュメントの更新
- [ ] `docs/functional-design.md`を更新
  - [ ] Buzzスコア計算アルゴリズムのセクションを更新
  - [ ] 5要素の説明を追加
  - [ ] 重み配分を記載
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
