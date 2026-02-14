# 要求内容

## GitHub Issue
https://github.com/k-negishi/ai-curated-newsletter/issues/16

## issue 内容
- タイトル: `.env を SSM に上げる`
- 本文: `https://github.com/k-negishi/calendar-auto-register/blob/main/scripts/sam-deploy.sh#L11-L21 と同じ仕組み`
- ラベル: なし

## 概要
ローカルで管理している `.env` の設定値を AWS Systems Manager Parameter Store（SecureString）へ登録できるようにする。
デプロイ時に `.env` から読み込んだ値を SSM に上げる仕組みを追加し、手作業での登録を不要にする。

## 目的
- 本番設定をコード化し、再現可能なデプロイ手順にする
- 設定漏れ・手入力ミスを防止する
- 既存の `src/shared/config.py` が期待する `/ai-curated-newsletter/` 配下パラメータを一括登録できるようにする

## 対象範囲
- `scripts/sam-deploy.sh`（新規）
  - `.env` 読み込み
  - SSM への `put-parameter --overwrite` 実行
  - `sam build` / `sam deploy` 実行
- `README.md` のデプロイ手順更新
- テスト追加（スクリプト内ロジックを検証可能な形で）

## 受け入れ条件
- [ ] `.env` の主要設定値が `/ai-curated-newsletter/{parameter_name}` として SecureString で登録される
- [ ] 既存値がある場合も `--overwrite` で更新される
- [ ] デプロイスクリプト実行時に SSM 登録が先に実行される
- [ ] 手順が README に明記される
- [ ] 追加したテストがパスする

## 実装方針
- Kent Beck の TDD (Test-Driven Development) で実装する
- RED → GREEN → REFACTOR のサイクルを遵守
- テストを先に書き、最小限の実装でパスさせ、その後リファクタリング
