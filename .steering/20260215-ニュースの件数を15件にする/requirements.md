# 要件定義

## GitHub Issue
https://github.com/k-negishi/ai-curated-newsletter/issues/13

## issue 内容
- タイトル: ニュースの件数15件に
- 本文: なし
- ラベル: なし
- コメント: なし

## 概要

ニュースレターの最終選定件数の既定値を 12 件から 15 件へ変更する。

## 背景

- 現在は最終選定件数の既定値が 12 件になっている
- issue #13 で「15件に変更する」要求が明示されている
- 既定値・実装コメント・サンプル設定・テストの不整合をなくす必要がある

## 実装対象

1. 最終選定件数の既定値変更
- `src/shared/config.py` の `FINAL_SELECT_MAX` 既定値を 15 に変更
- `src/services/final_selector.py` の `max_articles` 既定値を 15 に変更

2. 設定サンプルの更新
- `.env.example` の `FINAL_SELECT_MAX=12` を `15` に更新

3. 関連テストの更新
- `tests/unit/services/test_final_selector.py` の件数上限テストを 15 件基準に更新
- `tests/unit/shared/test_config.py` の既定値系期待値を 15 件に更新

4. 仕様コメントの整合
- `src/services/final_selector.py` と `src/models/execution_summary.py` の件数説明を 15 件に更新
- `README.md` の処理フロー説明を 15 件に更新

## 受け入れ条件

- [x] 最終選定件数の既定値が 15 件になっている
- [x] `.env.example` の `FINAL_SELECT_MAX` が 15 になっている
- [x] 15件上限を検証するユニットテストが通る
- [x] 設定読み込み関連テストが通る
- [x] 変更箇所の説明コメント/READMEが実装と矛盾しない

## スコープ外

- `docs/` 配下の大規模な永続ドキュメント一括更新
- 本番 SSM Parameter (`/ai-curated-newsletter/dotenv`) の値更新作業
- 既存 `.env`（ローカル個人設定）の強制書き換え

## 実装方針
- Kent Beck の TDD (Test-Driven Development) で実装する
- RED → GREEN → REFACTOR のサイクルを遵守
- テストを先に書き、最小限の実装でパスさせ、その後リファクタリング
