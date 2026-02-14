# 要求内容

## GitHub Issue

https://github.com/k-negishi/ai-curated-newsletter/issues/22

## issue 内容

- タイトル: sonne3.5 よりも安くて良いモデルに変更する
- 本文:
  - 東京リージョンで使える
  - オンデマンドで使える
  - toomanyrequestにならない
- ラベル: なし

## 概要

Claude 3.5 Sonnet v2 から Claude Haiku 4.5 に変更し、LLMコストを83%削減する。

## 背景

現在のLLMモデル（Claude 3.5 Sonnet v2）のコストが高く、月額予算を圧迫している。
東京リージョンで利用可能で、より安価なモデルに変更することで、コストを削減しつつ判定精度を維持する。

**現在のコスト:**
- Claude 3.5 Sonnet v2: input $6.00/1M tokens, output $30.00/1M tokens

**変更後のコスト:**
- Claude Haiku 4.5: input $1.00/1M tokens, output $5.00/1M tokens
- コスト削減率: 83%（約1/6）

**モデル選定の理由:**
- 東京リージョン (ap-northeast-1) で直接利用可能
- オンデマンドで使える
- 最新のHaikuモデルで性能が高い
- TooManyRequestsエラーのリスクが低い（高速処理可能）

## 実装方針

- Kent Beck の TDD (Test-Driven Development) で実装する
- RED → GREEN → REFACTOR のサイクルを遵守
- テストを先に書き、最小限の実装でパスさせ、その後リファクタリング

## 実装対象の機能

### 1. モデルID変更

- `.env` のモデルIDを変更（ローカル環境用）
- `.env.example` のモデルIDを更新
- `config.py` のデフォルト値は変更しない（ハードコードしない）
- SSMパラメータの更新（本番環境、別途手動で実施）

### 2. コスト計算式の更新

- `src/shared/utils/bedrock_cost_estimator.py` のデフォルト単価を更新
- Claude Haiku 4.5 の価格に合わせる

### 3. ドキュメントの更新

- `docs/architecture.md` の技術仕様を更新
- モデルIDと価格情報を最新化

## 受け入れ条件

### モデル変更

- [x] `.env` のモデルIDが `anthropic.claude-haiku-4-5-20251001-v1:0` に変更されている
- [x] `.env.example` のモデルIDが更新されている
- [x] `config.py` のデフォルト値は変更されていない（ハードコードしない）
- [x] ローカル環境で新しいモデルでLLM判定が実行できる

### コスト計算

- [x] `bedrock_cost_estimator.py` のデフォルト単価が更新されている
  - input: $1.00/1M tokens
  - output: $5.00/1M tokens
- [x] コスト計算のユニットテストが通る

### ドキュメント

- [x] `docs/architecture.md` が最新のモデル情報に更新されている
- [x] 価格情報が正確に記載されている

### テスト・品質

- [x] 全てのユニットテストが通る
- [x] リントチェックが通る
- [x] 型チェックが通る
- [x] ローカル環境で実際にLLM判定が実行でき、結果が正常に返る

## 成功指標

- LLMコストが現在の約17%（83%削減）に減少
- 判定精度が許容範囲内（実際の判定結果を確認）
- TooManyRequestsエラーが発生しない

## スコープ外

以下はこのフェーズでは実装しません:

- 本番環境のSSMパラメータ更新（別途手動で実施）
- モデルの判定精度の詳細な比較検証（別タスクで実施）
- バッチ処理やプロンプトキャッシュの活用（Phase 2で検討）

## 参照ドキュメント

- `docs/product-requirements.md` - プロダクト要求定義書
- `docs/functional-design.md` - 機能設計書
- `docs/architecture.md` - アーキテクチャ設計書
- [AWS Bedrock Pricing](https://aws.amazon.com/bedrock/pricing/)
- [Anthropic Pricing](https://platform.claude.com/docs/en/about-claude/pricing)
