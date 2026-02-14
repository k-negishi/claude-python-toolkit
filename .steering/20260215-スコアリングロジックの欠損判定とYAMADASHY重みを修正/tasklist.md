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

## GitHub Issue
https://github.com/k-negishi/ai-curated-newsletter/issues/31

### issue 内容
- タイトル: スコアリングロジックの欠損判定とYAMADASHY重みを修正
- ラベル: bug, enhancement

### 問題点
1. スコア0を欠損として誤認（全メディア共通）
   - `if y > 0:`, `if h > 0:`, `if z > 0:`, `if q > 0:` という条件により、スコア0が分母から除外される
   - はてぶ0件のQiita記事が10倍に水増しされる問題
2. WEIGHT_YAMADASHYが重すぎる（現在0.20）
   - YAMADASHYの目的は広範に記事を拾うことであり、品質判定での重要度は低い
3. DEFAULT_SCOREが高すぎる（現在40）
   - 低品質記事の底上げを引き起こす

### 実装方針
- Kent Beck の TDD (Test-Driven Development) で実装する
- RED → GREEN → REFACTOR のサイクルを遵守
- テストを先に書き、最小限の実装でパスさせ、その後リファクタリング

### 変更パラメータ
- WEIGHT_YAMADASHY: 0.20 → 0.05
- WEIGHT_ZENN: 0.25 → 0.35
- WEIGHT_QIITA: 0.10 → 0.15
- DEFAULT_SCORE: 40 → 20

---

## フェーズ1: テスト作成（RED - 失敗するテストを先に書く）

- [x] スコア0が正しく扱われるテストを追加
  - [x] `test_multi_source_social_proof_fetcher.py`にスコア0のケースを追加
  - [x] はてぶ0件のQiita記事が正しく低評価されることを検証するテスト
  - [x] 全メディアスコア0の場合のテスト（DEFAULT_SCORE=20を検証）- 既存のtest_fetch_batch_all_signals_missingを後で修正

- [x] 重み変更を検証するテストを追加
  - [x] WEIGHT_YAMADASHY=0.05での統合スコア計算テスト - 既存テストの期待値を後で修正
  - [x] 重み配分テスト（Y=0.05, H=0.45, Z=0.35, Q=0.15）を更新 - 既存テストの期待値を後で修正

- [x] テスト実行（RED確認）
  - [x] `.venv/bin/pytest tests/unit/services/test_multi_source_social_proof_fetcher.py -v`
  - [x] 新しいテストが失敗することを確認（RED状態）- 期待値7.5、実際50.0で失敗

## フェーズ2: 実装（GREEN - 最小限の実装でテストをパスさせる）

- [x] 欠損判定を修正（`multi_source_social_proof_fetcher.py`）
  - [x] `if y > 0:` を削除（行153-155）
  - [x] `if h > 0:` を削除（行157-159）
  - [x] `if z > 0:` を削除（行161-163）
  - [x] `if q > 0:` を削除（行165-167）
  - [x] すべてのスコアを無条件で統合計算に含めるロジックに変更

- [x] 重み配分を変更（`multi_source_social_proof_fetcher.py`）
  - [x] `WEIGHT_YAMADASHY = 0.20` → `WEIGHT_YAMADASHY = 0.05`（行35）
  - [x] `WEIGHT_ZENN = 0.25` → `WEIGHT_ZENN = 0.35`（行37）
  - [x] `WEIGHT_QIITA = 0.10` → `WEIGHT_QIITA = 0.15`（行38）
  - [x] docstringの統合計算式を更新（行21）

- [x] DEFAULT_SCOREを20に変更（`multi_source_social_proof_fetcher.py`）
  - [x] `DEFAULT_SCORE = 40.0` → `DEFAULT_SCORE = 20.0`（行41）
  - [x] docstringのデフォルト値を更新（行21-25）

- [x] DEFAULT_SCOREを20に変更（`buzz_scorer.py`）
  - [x] `MultiSourceSocialProofFetcher`のDEFAULT_SCORE参照箇所を確認
  - [x] 必要に応じてコメントやログメッセージを更新 - 行79のデフォルト値を40.0→20.0に変更

- [x] テスト実行（GREEN確認）
  - [x] `.venv/bin/pytest tests/unit/services/test_multi_source_social_proof_fetcher.py -v`
  - [x] 新テスト test_score_zero_treated_as_data が成功（GREEN状態）- 既存テストの期待値修正はフェーズ3で実施

## フェーズ3: リファクタリングと品質チェック（REFACTOR）

- [x] 既存テストの修正
  - [x] `test_fetch_batch_one_signal_missing`の期待値を更新（行69-107）- スコア0も統合計算に含める
  - [x] `test_fetch_batch_all_signals_zero`の期待値を更新（全スコア0=統合スコア0、行110-146）
  - [x] `test_weight_distribution`のdocstringを更新（重み変更を反映）
  - [x] `test_fetch_batch_all_signals_success`の期待値を更新（新しい重み配分を反映）

- [x] コードの可読性向上（必要に応じて）
  - [x] 統合スコア計算ロジックの見直し - コメント追加済み
  - [x] 変数名やコメントの改善 - 適切に記述済み

- [x] すべてのテストが通ることを確認
  - [x] `.venv/bin/pytest tests/unit/services/test_multi_source_social_proof_fetcher.py -v` - 全6テストパス

- [x] リントチェック
  - [x] `.venv/bin/ruff check src/`
  - [x] エラーがないことを確認 - All checks passed!

- [x] コードフォーマット
  - [x] `.venv/bin/ruff format src/` - 1 file reformatted

- [x] 型チェック
  - [x] `.venv/bin/mypy src/`
  - [x] エラーがないことを確認 - Success: no issues found in 46 source files

## フェーズ4: ドキュメント更新と振り返り

- [x] 実装後の振り返り（このファイルの下部に記録）

---

## 実装後の振り返り

### 実装完了日
2026-02-15

### 計画と実績の差分

**計画と異なった点**:
- 並行開発中のリファクタリング（`src/services/social_proof/`へのファイル移動）により、実装途中で対応が必要になった
- DEFAULT_SCOREの使用箇所が変更により実質的になくなった（全てのスコアが0でも統合スコアは0となり、DEFAULT_SCOREは使用されない）

**新たに必要になったタスク**:
- テストファイルのimport文の修正（並行開発中のファイル移動への対応）
- `social_proof_fetcher.py` の構文エラー修正（Python 2形式のexcept句をPython 3形式に修正）

**技術的理由でスキップしたタスク**（該当する場合のみ）:
- なし（全タスク完了）

**⚠️ 注意**: 「時間の都合」「難しい」などの理由でスキップしたタスクはここに記載しないこと。全タスク完了が原則。

### 学んだこと

**技術的な学び**:
- スコア0と欠損（データなし）の区別が重要
  - `if x > 0:` という条件は「スコア0も欠損として扱う」ことを意味し、意図しない動作を引き起こす
  - 正しくは「全ての指標を無条件で統合計算に含める」べき
- 重み配分の変更は既存テストの期待値にも影響する
  - テストのdocstringやコメントも併せて更新する必要がある

**プロセス上の改善点**:
- TDDサイクル（RED → GREEN → REFACTOR）が効果的に機能した
  - 先にテストを書くことで、問題が明確になった
  - 既存テストの失敗により、実装が正しいことを確認できた
- 並行開発中の変更との競合は、一時的に unstage することで対応できた

**コスト・パフォーマンスの成果**（該当する場合）:
- スコアリング精度の向上により、低品質記事の通知を削減
  - はてぶ0件の記事が不当に高評価される問題を解決
  - ユーザー体験の向上が期待される

### 次回への改善提案

**計画フェーズでの改善点**:
- 並行開発中の変更を事前に確認する必要があった
- 影響範囲調査（ステップ3.5）で並行開発中のファイル移動を検出できなかった

**実装フェーズでの改善点**:
- ファイル移動などの環境変更があった場合の対処法を明確化する
- git status を定期的に確認する習慣をつける

**ワークフロー全体での改善点**:
- `/implement` コマンドは並行開発を考慮した設計になっていない
- ファイル移動などの大規模なリファクタリング中は、ブランチを分けて作業することを推奨
