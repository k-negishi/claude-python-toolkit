# タスクリスト

## フェーズ0: 仕様確定（実装前に必須）
- [x] リンク化制御方式を確定する
  - [x] A案: Text+Html メールに変更し URL のみリンク化
  - [x] ~~B案: Text メール維持で非 URL 文字列をデファング~~（A案を採用）
- [x] Tag 生成方式を確定する
  - [x] A案: LLM 出力に `tags` を追加（推奨）
  - [x] ~~B案: title/description から簡易抽出~~（A案を採用）

## フェーズ1: メール本文フォーマット調整（TDD）
- [x] 罫線長を短縮する（`src/services/formatter.py`）
  - [x] RED: 80文字罫線が出力される現状を失敗テストで固定する
  - [x] GREEN: 罫線定数を短い長さへ変更しテストを通す
  - [x] REFACTOR: 罫線生成ロジックを重複なく整理する
- [x] 実行日時を JST 表示に変更する（`src/services/formatter.py`）
  - [x] RED: UTC表記を期待しないテストを追加し失敗を確認する
  - [x] GREEN: `Asia/Tokyo` 変換とタイムゾーン名なし表示を実装する
  - [x] REFACTOR: 日時フォーマット処理を関数化して可読性を上げる
- [x] 記事番号をセクション横断の通番にする（`src/services/formatter.py`）
  - [x] RED: セクション切替で番号がリセットされることを失敗テストで再現する
  - [x] GREEN: 共通カウンタで 1..N を維持する実装に変更する
  - [x] REFACTOR: 記事描画ループの重複を削減する
- [x] `Tag` 行を `概要` の下に追加する（`src/services/formatter.py`）
  - [x] RED: `Tag:` 行がない現状を失敗テストで確認する
  - [x] GREEN: `Tag: <tag1>, <tag2>` を出力する実装を追加する
  - [x] REFACTOR: Tag文字列組み立てを専用ヘルパーへ抽出する

## フェーズ2: 件名変更（TDD）
- [x] 件名を `Techニュースレター - YYYY年M月D日` に変更する（`src/orchestrator/orchestrator.py`）
  - [x] RED: 既存件名フォーマットとの差分を失敗テストで固定する
  - [x] GREEN: 新しい件名フォーマットを実装してテストを通す
  - [x] REFACTOR: 件名生成を小さな関数に分離する

## フェーズ3: 仕様確定内容に応じた実装（TDD）
- [x] リンク化制御を実装する
  - [x] RED: URL以外がリンク化されうるケースをテストで再現する
  - [x] GREEN: 選択方式（A/B）に沿ってリンク化制御を実装する
  - [x] REFACTOR: 表示ロジックと送信ロジックの責務境界を明確化する
- [x] Tag 生成を実装する
  - [x] RED: `Tag` が空または欠落するケースを失敗テストで再現する
  - [x] GREEN: 選択方式（A/B）に沿って Tag 生成を実装する
  - [x] REFACTOR: Tag 生成の依存を最小化しテスト容易性を高める

## フェーズ4: テスト拡充
- [x] Formatter のユニットテストを追加・更新する
  - [x] 罫線長
  - [x] JST 表示
  - [x] 通番
  - [x] Tag 表示
- [x] Orchestrator の件名生成テストを追加・更新する
- [x] （A案時）`tags` の保存・復元テストを追加・更新する
- [x] （A案時）Notifier の Text+Html 送信テストを追加・更新する

## フェーズ5: 品質チェック
- [ ] `.venv/bin/pytest tests/ -v`
- [x] `.venv/bin/ruff check src/`
- [x] `.venv/bin/ruff format src/`
- [x] `.venv/bin/mypy src/`

## 完了条件
- [x] Issue #12 の6要件を満たす本文・件名が生成される
- [ ] 主要メールクライアントで意図しないリンク化が許容範囲内である
- [ ] 追加/更新したテストがすべてパスする

## 実装メモ
- リンク化制御は A案（Text+Html）を採用。URLのみ `<a>` として出力。
- Tag 生成は A案（LLM構造化出力）を採用。`JudgmentResult.tags` を追加。
- 全テスト実行では、今回変更と無関係な `tests/integration/test_buzz_scorer_integration.py` の2件が失敗。
