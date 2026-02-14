# タスクリスト

## フェーズ1: RED（失敗テストを先に作る）

- [x] FinalSelector の上限テストを 15 件前提に変更
  - [x] `tests/unit/services/test_final_selector.py` のフィクスチャを `max_articles=15` に変更
  - [x] `test_respects_max_articles` を「20件入力で15件選定」検証に変更
- [x] Config 既定値テストを 15 件前提に変更
  - [x] `tests/unit/shared/test_config.py` の既定値系入力を `FINAL_SELECT_MAX=15` に変更
  - [x] 既定値系アサーションを `15` に変更
- [x] RED確認: 変更した2テストファイルを実行し、失敗を確認

## フェーズ2: GREEN（最小実装でテストを通す）

- [x] `src/shared/config.py` の `FINAL_SELECT_MAX` 既定値を 15 に変更
- [x] `src/services/final_selector.py` の `max_articles` 既定値を 15 に変更
- [x] `.env.example` の `FINAL_SELECT_MAX` を 15 に変更
- [x] GREEN確認: 変更した2テストファイルが通ることを確認

## フェーズ3: REFACTOR（整合性と品質の仕上げ）

- [x] 表記整合を更新
  - [x] `src/services/final_selector.py` の「最大12件」表記を更新
  - [x] `src/models/execution_summary.py` の範囲表記を `0-15` に更新
  - [x] `README.md` の `FinalSelector (max 12...)` 表記を更新
- [x] 回帰確認として関連テストを再実行
  - [x] `.venv/bin/pytest tests/unit/services/test_final_selector.py tests/unit/shared/test_config.py -v`
- [x] 品質チェックを実行
  - [x] `.venv/bin/ruff check src/`
  - [x] `.venv/bin/ruff format src/`
  - [x] `.venv/bin/mypy src/`

## 実装後の振り返り

- [x] 実装完了日を記録
- [x] 計画と実績の差分を記録
- [x] 学んだことと次回への改善を記録

### 実装完了日
2026-02-15

### 計画と実績の差分
- `mypy src/` 実行時に `feedparser` の型スタブ不足で失敗したため、`src/services/yamadashy_signal_fetcher.py` と `src/services/qiita_rank_fetcher.py` の import に `# type: ignore[import-untyped]` を追加した
- これは件数変更の本質要件ではないが、`/implement` の品質ゲート（mypyパス）達成のために必要な最小修正だった

### 学んだこと
- 件数変更のような小規模要件でも、実効値は「デフォルト値・サンプル設定・テスト」の3点を同時に整合させる必要がある
- TDDで「デフォルトコンストラクタの期待値」を明示したことで、単なるテストフィクスチャ更新だけでは見逃す不整合を防げた

### 次回への改善
- 既存品質ゲート実行時に依存ライブラリの型スタブ状況を先に確認し、`mypy` の失敗要因を早期に可視化する
- Issueが短文の場合でも、反映対象（コード・設定・ドキュメント）の最小セットを初期段階でチェックリスト化する
