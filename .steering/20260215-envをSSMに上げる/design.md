# 設計書

## 設計方針
Issue参照先と同様に「デプロイスクリプトで `.env` を読み込み、SSM Parameter Store へ投入する」流れを採用する。
本リポジトリでは `src/shared/config.py` が `/ai-curated-newsletter/` 配下の個別パラメータを参照するため、`.env` 全文を1パラメータにするのではなく、必要キーを個別登録する。

## 実装アプローチ
1. `scripts/sam-deploy.sh` を新規作成
2. `.env` を `set -a; source .env; set +a` で読み込む
3. 環境変数名と SSM キー名のマッピングを定義してループ登録
4. `aws ssm put-parameter --type SecureString --overwrite` を実行
5. 続けて `sam build` と `sam deploy` を実行

## SSM キー設計
プレフィックス: `/ai-curated-newsletter`

- `LOG_LEVEL` -> `log_level`
- `DRY_RUN` -> `dry_run`
- `DYNAMODB_CACHE_TABLE` -> `dynamodb_cache_table`
- `DYNAMODB_HISTORY_TABLE` -> `dynamodb_history_table`
- `BEDROCK_MODEL_ID` -> `bedrock_model_id`
- `BEDROCK_REGION` -> `bedrock_region`
- `BEDROCK_MAX_PARALLEL` -> `bedrock_max_parallel`
- `LLM_CANDIDATE_MAX` -> `llm_candidate_max`
- `FINAL_SELECT_MAX` -> `final_select_max`
- `FINAL_SELECT_MAX_PER_DOMAIN` -> `final_select_max_per_domain`
- `SOURCES_CONFIG_PATH` -> `sources_config_path`
- `FROM_EMAIL` -> `from_email`
- `TO_EMAIL` -> `to_email`

## エラーハンドリング
- `.env` がない場合は即時終了
- 必須環境変数（AWS_REGION など）が不足していても既定値で補完
- マッピング対象の値が空の場合は警告を出してスキップせず、失敗として停止

## TDDサイクル
1. **RED**: マッピング生成ロジックのユニットテストを先に追加し、失敗を確認
2. **GREEN**: 最小限の実装でテストを通す
3. **REFACTOR**: 読みやすさ・保守性を改善し、再度テストを通す
