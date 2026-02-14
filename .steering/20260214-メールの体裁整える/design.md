# 設計書

## 設計方針
- 変更の中心は `Formatter` と `Orchestrator` に限定し、影響範囲を最小化する
- UI（メール本文）要件はテストで文字列比較できる形に落とす
- 未確定仕様（リンク制御、Tag 生成）は実装前に意思決定し、分岐なく進める

## TDDサイクル
1. **RED**: 失敗するテストを先に書く
2. **GREEN**: 最小限の実装でテストをパスさせる
3. **REFACTOR**: 振る舞いを変えずに可読性・保守性を改善する

## TDD適用単位
- 1要件1テストを基本に、小さなスライスで実装する
- 1スライスごとに `pytest` を実行してから次へ進む
- 複数要件を同時実装しない（失敗原因を局所化する）

## 変更対象コンポーネント
- `src/services/formatter.py`
  - 罫線長、日時表示、記事連番、Tag 行、リンク表現
- `src/orchestrator/orchestrator.py`
  - 件名フォーマットの変更（`Techニュースレター - YYYY年M月D日`）
- `src/services/notifier.py`（選択肢次第）
  - リンク化制御のため HTML パートを併送する場合に変更
- `src/models/judgment.py` / `src/services/llm_judge.py` / `src/repositories/cache_repository.py`（Tag 生成方式次第）
  - Tag を構造データとして持つ場合のみ変更

## 詳細設計

### 1. 罫線の短縮
- `Formatter` の固定長罫線 (`"=" * 80`, `"-" * 80`) を定数化し、短い値へ変更する
- 推奨値: 36〜48 文字（初期値 40）
- 実装例:
  - `SECTION_SEPARATOR = "=" * 40`
  - `ITEM_SEPARATOR = "-" * 40`

### 2. JST 表示（タイムゾーン名なし）
- `executed_at` を `ZoneInfo("Asia/Tokyo")` へ変換して表示
- 出力形式は `YYYY-MM-DD HH:MM:SS`（末尾に `UTC`/`JST` を付与しない）
- 例:
  - 変換前: `2026-02-13 18:00:00 UTC`
  - 変換後: `2026-02-14 03:00:00`

### 3. 件名フォーマット
- `orchestrator.py` の件名生成を以下へ変更:
  - `Techニュースレター - {year}年{month}月{day}日`
- `strftime` のプラットフォーム依存を避けるため、`datetime` の数値属性を直接連結する

### 4. 連番の通番化
- 現在のセクション別 `enumerate(..., 1)` を廃止
- `article_index` を `format()` スコープで 1 回だけ初期化し、記事描画ごとにインクリメント
- `_format_article(index, article)` のシグネチャは現状維持

### 5. Tag 行追加
- 記事描画に `Tag: ...` 行を追加（`概要` の直下）
- `Tag` 生成方式は以下 2 案:
  - A案（推奨）: `JudgmentResult.tags: list[str]` を追加し、LLM 出力で tags を返す
  - B案（暫定）: title/description から簡易抽出（正規表現ベース）
- 推奨理由:
  - A案は精度と再現性が高く、将来のランキング/分析にも利用しやすい

### 6. リンク化制御
- 技術的制約: Text メールのみではクライアント側の自動リンク化を完全制御できない
- 選択肢:
  - A案（推奨）: SES で Text + Html のマルチパート送信にし、HTML 側で URL のみ `<a>` 化
  - B案: Text のまま非 URL 文字列をデファング（可読性低下リスクあり）
- 推奨理由:
  - A案は要件「URL のみリンク」を実現しやすく、表示品質を担保できる

## データモデル変更（A案採用時）

### `JudgmentResult`
- 追加: `tags: list[str]`

### `LlmJudge`
- LLM 出力 JSON に `tags` を追加
- パース時のバリデーションに `tags` を含める（最大件数上限を設定）
- フォールバック判定時は `tags=[]`

### `CacheRepository`
- `put/get` で `tags` を保存・復元
- 既存データ互換のため、欠損時デフォルト `[]`

## テスト設計
- `tests/unit/services/test_formatter.py`（新規）
  - 罫線長、JST 表示、通番、Tag 行、リンク文字列の出力を検証
- `tests/unit/orchestrator/test_orchestrator_subject.py`（新規または既存拡張）
  - 件名フォーマット検証
- `tests/unit/services/test_llm_judge.py` / `tests/unit/repositories/test_cache_repository.py`（A案時）
  - `tags` の保存・復元・フォールバックを検証
- `tests/integration/test_notification_flow.py`
  - Notifier の送信ペイロード（Text/Html）を検証（A案時）

## リスクと対策
- リスク: 仕様未確定のまま実装すると手戻りが大きい
  - 対策: `tasklist.md` の先頭で意思決定タスクを完了させてから実装開始
- リスク: タグ抽出を暫定実装すると誤検知が増える
  - 対策: 可能なら LLM 構造化出力へ寄せる
- リスク: メールクライアント差異
  - 対策: Gmail/Outlook の代表ケースで表示確認手順を用意
