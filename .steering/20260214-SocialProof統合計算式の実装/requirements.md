# 要求内容

## GitHub Issue
https://github.com/k-negishi/ai-curated-newsletter/issues/19

## issue 内容
- タイトル: SocialProof統合計算式の実装（Phase 2: yamadashy/Zenn/Qiita連携）
- ラベル: なし

## 概要

Issue #11 Phase 1で実装した5要素統合型Buzzスコアの基盤を元に、SocialProof要素を複数指標統合版に拡張する。Phase 1ではHatena単一指標版（件数に応じた5段階スコア）だったが、Phase 2では4つの情報源（yamadashy, Hatena, Zenn, Qiita）から統合計算する。

## 背景

Phase 1では以下を実装済み:
- 5要素フレームワーク（Recency, Consensus, SocialProof, Interest, Authority）
- SocialProof: Hatena単一指標版（件数に応じた5段階スコア）
- 拡張可能な設計基盤

Phase 2では、SocialProofを4つの情報源から統合計算することで、より正確な話題性スコアを算出する。

## 実装対象の機能

### 1. SocialProof統合計算式

**計算式**:
```
S = (0.20Y + 0.45H + 0.25Z + 0.10Q) / sum(observed_weights)
```

- **Y**: yamadashy シグナル（掲載/再出現）
- **H**: Hatena 件数（正規化）
- **Z**: Zenn API 指標（liked_count中心）
- **Q**: Qiita popular 順位

**欠損対応**:
- 欠損した指標は分母から除外
- 全欠損時は `S=40`（デフォルト値）

**各指標の計算方法（ユーザー回答を元に決定）**:

- **Y（yamadashy）**: 掲載されていれば100、されていなければ0（シンプルな2値判定）
- **H（Hatena）**: log変換を使った連続値（0-100）
  - 例: `H = min(100, log10(count + 1) * 25)` （100件で50点、1000件で75点、10000件で100点）
- **Z（Zenn）**: log変換を使った連続値（0-100）
  - 例: `Z = min(100, log10(liked_count + 1) * 30)` （10件で30点、100件で60点、1000件で90点）
- **Q（Qiita）**: 段階的変換
  - 上位10件: 100点
  - 11-20件: 70点
  - 21-30件: 40点
  - 31-50件: 20点
  - 51件以降: 0点

### 2. 情報源追加

#### yamadashy RSS
- URL: `https://yamadashy.github.io/tech-blog-rss-feed/feeds/rss.xml`
- 用途: 網羅性向上、Y シグナル生成
- `config/sources.yaml`に追加

#### Zenn API
- URL: `https://zenn.dev/api/articles`
- 取得項目: `liked_count`, `published_at`
- 用途: Z スコア算出

#### Qiita順位
- RSS: `https://qiita.com/popular-items/feed`（既存）
- 用途: フィード内順位をQ スコアに変換

### 3. 外部サービス利用ポリシー

**同時接続制限**:
- 同一ドメイン: 1接続
- 全体: 3接続

**リクエスト間隔**:
- 3〜6秒 jitter（ランダム）

**タイムアウト**:
- 5秒（Phase 1と同じ）

**リトライ戦略**:
- 対象: 429 / 5xx のみ
- 間隔: 2s → 4s → 8s（最大3回）
- 失敗時: 該当指標のみ欠損扱いで継続

### 4. Hatena API 最適化

**Phase 1の課題**:
- `/count/entry` 使用（単一URL、並列取得）
- 大量記事時にリクエスト数が多い

**Phase 2の改善**:
- `/count/entries` 使用（複数URL一括、最大50件）
- 50件超過時は分割処理
- `MAX_HATENA_LOOKUPS=50`（1 run あたり最大1リクエスト）

## 受け入れ条件

### SocialProof統合計算式
- [ ] SocialProofが4指標（Y, H, Z, Q）から統合計算される
- [ ] 欠損指標は分母から除外される
- [ ] 全欠損時は `S=40` となる
- [ ] Y（yamadashy）: 掲載されていれば100、されていなければ0
- [ ] H（Hatena）: log変換を使った連続値（0-100）
- [ ] Z（Zenn）: log変換を使った連続値（0-100）
- [ ] Q（Qiita）: 段階的変換（上位10件=100, 11-20件=70, etc.）

### 情報源追加
- [ ] yamadashy RSSが収集元（`config/sources.yaml`）に追加されている
- [ ] Zenn API連携が実装されている
- [ ] Qiita順位が取得されている

### 外部サービス利用ポリシー
- [ ] 同一ドメイン同時接続が1に制限されている
- [ ] リクエスト間隔が3〜6秒 jitterになっている
- [ ] タイムアウトが5秒に設定されている
- [ ] リトライ戦略（2s→4s→8s）が実装されている
- [ ] 429 / 5xx のみがリトライ対象になっている
- [ ] 失敗時は該当指標のみ欠損扱いで継続される

### Hatena API 最適化
- [ ] Hatena API が `/count/entries` を使用している
- [ ] 複数URL一括取得（最大50件）が実装されている
- [ ] 50件超過時に分割処理される
- [ ] `MAX_HATENA_LOOKUPS=50` が設定されている

### テスト
- [ ] ユニットテストが追加されている
- [ ] 統合テストが追加されている
- [ ] dry_run実行が成功する

## 成功指標

- SocialProofスコアの精度向上（4指標統合による）
- 外部API呼び出しの最適化（Hatena: 79件→1-2件）
- レート制限エラーの削減（jitter、リトライ）

## スコープ外

以下はこのPhaseでは実装しません（Phase 3以降）:

- Reddit連携
- Hacker News連携
- 機械学習による重み最適化

## 実装方針

- Kent Beck の TDD (Test-Driven Development) で実装する
- RED → GREEN → REFACTOR のサイクルを遵守
- テストを先に書き、最小限の実装でパスさせ、その後リファクタリング

## 参照ドキュメント

- `docs/product-requirements.md` - プロダクト要求定義書
- `docs/functional-design.md` - 機能設計書
- `docs/architecture.md` - アーキテクチャ設計書
- 関連issue: #11 (Phase 1: 5要素統合型フレームワーク)
- 連携issue: #6 (興味リストのマスタ化)
