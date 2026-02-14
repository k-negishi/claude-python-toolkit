# 設計書

## アーキテクチャ概要

既存のコンポーネント構成を維持しつつ、設定値のみを変更する。

```
変更対象:
- .env (ローカル環境のモデルID)
- .env.example (環境変数テンプレート)
- src/shared/utils/bedrock_cost_estimator.py (コスト単価)
- docs/architecture.md (ドキュメント)

変更しない:
- src/shared/config.py (デフォルト値はハードコードしない)
```

## TDDサイクル

### RED: テストを先に書く

1. `bedrock_cost_estimator.py` のデフォルト単価をテスト
   - 既存テストがデフォルト値をチェックしているか確認
   - 必要に応じて新しいテストケースを追加

### GREEN: 実装してテストをパスさせる

1. 設定ファイルを変更
2. コスト計算式を更新
3. テストが通ることを確認

### REFACTOR: コードを改善

1. 不要なコメントを削除
2. 一貫性を確保

## コンポーネント設計

### 1. .env (ローカル環境設定)

**変更内容**:
- `BEDROCK_MODEL_ID` の値を変更
  - 変更前: `anthropic.claude-3-5-sonnet-20241022-v2:0`
  - 変更後: `anthropic.claude-haiku-4-5-20251001-v1:0`

**実装の要点**:
- `.env` ファイルのみ変更
- `config.py` のデフォルト値は変更しない（ハードコードしない）
- 環境変数経由でモデルIDを設定する方針を維持

### 2. bedrock_cost_estimator (src/shared/utils/bedrock_cost_estimator.py)

**変更内容**:
- `input_cost_per_million` のデフォルト値を変更
  - 変更前: `6.0` (Claude 3.5 Sonnet v2)
  - 変更後: `1.0` (Claude Haiku 4.5)
- `output_cost_per_million` のデフォルト値を変更
  - 変更前: `30.0` (Claude 3.5 Sonnet v2)
  - 変更後: `5.0` (Claude Haiku 4.5)

**実装の要点**:
- 関数シグネチャは変更しない
- デフォルト引数のみ変更
- 既存のテストが引き続き動作することを確認

### 3. .env.example (環境変数テンプレート)

**変更内容**:
- `BEDROCK_MODEL_ID` の例示値を更新
  - 変更前: `anthropic.claude-3-5-sonnet-20241022-v2:0`
  - 変更後: `anthropic.claude-haiku-4-5-20251001-v1:0`
- コメントを追加して、新しいモデルであることを明記

**実装の要点**:
- `.env` と同じ値に更新
- 新規ユーザーが `.env.example` をコピーして使う際に正しいモデルIDが設定されるようにする

### 4. docs/architecture.md (ドキュメント)

**変更内容**:
- モデルIDを更新
- 価格情報を更新
- コスト推定の計算式を更新

## データフロー

変更なし（モデルIDと単価のみ変更）

```
1. config.py が環境変数または デフォルト値からモデルIDを読み込む
2. LlmJudge が config.bedrock_model_id を使用してBedrockを呼び出す
3. bedrock_cost_estimator がデフォルト単価でコストを推定
```

## エラーハンドリング戦略

変更なし（既存のエラーハンドリングを維持）

## テスト戦略

### TDDサイクルに従ったテスト実施

#### RED: 失敗するテストを書く

1. **コスト計算のテスト**
   - `test_bedrock_cost_estimator.py` を確認
   - デフォルト単価が正しいことをテストするケースを追加（必要に応じて）

#### GREEN: 実装してテストをパスさせる

1. **最小限の実装**
   - デフォルト値を変更
   - テストが通ることを確認

#### REFACTOR: リファクタリング

1. **コード品質の向上**
   - 不要なコメント削除
   - 一貫性確保

### ユニットテスト

- `tests/unit/shared/utils/test_bedrock_cost_estimator.py`
  - デフォルト単価が正しいことを確認
  - コスト計算が正しいことを確認

### 統合テスト

- ローカル環境で実際にLLM判定を実行
  - `./run_local.sh` を使用
  - 新しいモデルで正常に判定結果が返ることを確認
  - エラーが発生しないことを確認

### E2Eテスト（手動）

1. **dry_runモードで実行**
   ```bash
   .venv/bin/python test_lambda_local.py --dry-run
   ```

2. **実行結果の確認**
   - LLM判定が成功すること
   - エラーログがないこと
   - コスト推定値が約1/6になっていること

## 依存ライブラリ

変更なし（既存のライブラリを使用）

## ディレクトリ構造

```
.env (変更 - ローカル環境のモデルID)
.env.example (変更 - テンプレート更新)
src/
├── shared/
│   ├── config.py (変更なし)
│   └── utils/
│       └── bedrock_cost_estimator.py (変更)
docs/
└── architecture.md (変更)
tests/
└── unit/
    ├── shared/
    │   ├── test_config.py (変更なし)
    │   └── utils/
    │       └── test_bedrock_cost_estimator.py (確認・追加)
```

## 実装の順序（TDDサイクル）

### フェーズ1: RED - テストを先に書く

1. `test_bedrock_cost_estimator.py` のテスト確認
   - デフォルト単価をテストするケースがあるか確認
   - 必要に応じて新しいテストケースを追加

### フェーズ2: GREEN - 実装してテストをパスさせる

1. `.env` のモデルIDを変更
2. `.env.example` を更新
3. `bedrock_cost_estimator.py` のデフォルト単価を変更
4. テストが通ることを確認

### フェーズ3: REFACTOR - リファクタリング

1. コードレビュー
2. 不要なコメント削除
3. 一貫性確保

### フェーズ4: ドキュメント更新

1. `docs/architecture.md` を更新

### フェーズ5: 品質チェック

1. 全テスト実行
2. リント・型チェック
3. ローカルで実際にLLM判定を実行

## セキュリティ考慮事項

- 変更なし（既存のセキュリティ設計を維持）

## パフォーマンス考慮事項

**改善点**:
- Claude Haiku 4.5 は高速なモデルなので、レスポンスタイムが短縮される可能性がある
- TooManyRequestsエラーのリスクが低減

**懸念点**:
- モデルの判定精度が若干低下する可能性がある（実測で確認）

## 将来の拡張性

**Phase 2での検討事項**:
- バッチ処理の活用（50%コスト削減）
- プロンプトキャッシュの活用（キャッシュヒット時は1/10のコスト）
- 判定精度のモニタリングとフィードバックループ

**モデル切り替えの柔軟性**:
- 環境変数でモデルIDを上書き可能
- 必要に応じて Sonnet と Haiku を使い分け可能
