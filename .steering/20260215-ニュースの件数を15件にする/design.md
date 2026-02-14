# 設計書

## アーキテクチャ概要

既存アーキテクチャは維持し、以下の設定値・既定値のみ変更する:
- `src/shared/config.py`
- `src/services/final_selector.py`
- `.env.example`
- 関連ユニットテスト
- 軽微な仕様コメント/README

## 設計方針

1. 実行時の実効値は `ENV > .env > デフォルト` の順で決まるため、デフォルト値変更だけでなくサンプル設定も更新する
2. テストは「15件上限を超える入力で15件に制限される」ことを明示的に検証する
3. ドメイン上限制御 (`max_per_domain=4`) は変更しない

## 変更設計

### 1. Config デフォルト変更
- `src/shared/config.py`
  - `_load_config_local()` の `final_select_max` デフォルトを `"12"` -> `"15"`

### 2. FinalSelector デフォルト変更
- `src/services/final_selector.py`
  - `__init__(max_articles: int = 12, ...)` -> `15`
  - ドキュメント文字列の「最大12件」を「最大15件」に更新

### 3. サンプル環境変数変更
- `.env.example`
  - `FINAL_SELECT_MAX=12` -> `FINAL_SELECT_MAX=15`

### 4. テスト変更
- `tests/unit/services/test_final_selector.py`
  - フィクスチャの `max_articles` を 15 に更新
  - 上限検証テストは 20 件入力で 15 件選定を検証
- `tests/unit/shared/test_config.py`
  - 既定値系テストの `FINAL_SELECT_MAX` を 15 に更新
  - 期待値アサーションも 15 に更新

### 5. 整合性コメント更新
- `src/models/execution_summary.py` の `final_selected_count` 説明を `0-15` に更新
- `README.md` の処理フロー `FinalSelector (max 12...)` を `max 15` に更新

## TDDサイクル

1. RED
- `tests/unit/services/test_final_selector.py` と `tests/unit/shared/test_config.py` を先に 15 件期待に変更
- 対象テストを実行して失敗を確認

2. GREEN
- 実装コードとサンプル設定を変更し、対象テストをパスさせる

3. REFACTOR
- コメント・README の表記揺れを最小範囲で調整
- 再度テストを実行して回帰がないことを確認
