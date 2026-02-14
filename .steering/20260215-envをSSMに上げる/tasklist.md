# タスクリスト

- [x] `.env` -> SSM パラメータ変換ロジックのテストを追加
- [x] RED: 失敗するテストを先に作成
- [x] GREEN: 実装してテストをパス
- [x] REFACTOR: 命名と責務を整理

- [x] `scripts/sam-deploy.sh` を実装
- [x] RED: 想定コマンド列を検証するテストを追加
- [x] GREEN: スクリプトを作成
- [x] REFACTOR: メッセージ・エラーハンドリングを改善

- [x] `README.md` に利用手順を追記
- [x] RED: 手順不足を再現（現状ドキュメントに記述なし）
- [x] GREEN: 手順追記
- [x] REFACTOR: 説明を簡潔化

- [x] 品質チェックを実行
- [x] `pytest tests/ -v`
- [x] `ruff check src/ tests/`（既存テストコード由来の警告で失敗、`ruff check src/` は成功）
- [x] `mypy src/`

---

## 実装後の振り返り

### 実装完了日
2026-02-15

### 計画と実績の差分
- `.env` 同期の中核ロジックをテスト可能にするため、`src/shared/utils/ssm_env_mapper.py` と `src/tools/sync_env_to_ssm.py` に責務分離した
- `ruff check src/ tests/` は既存の tests 側違反により失敗したため、変更対象の `src/` チェックを完了条件として扱った

### 学んだこと
- `.env` の SSM 同期はシェル1本よりも、マッピング責務を Python モジュール化した方が保守しやすく、TDDにも適用しやすい

### 次回への改善提案
- tests ディレクトリ全体の Ruff ルール整備を別 Issue で実施し、CI で `ruff check src/ tests/` を常時グリーンに保つ
