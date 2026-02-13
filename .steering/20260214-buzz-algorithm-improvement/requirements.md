# 要求内容

## 概要

Buzzスコア算出アルゴリズムを改善し、5つの構成要素（Recency、Consensus、SocialProof、Interest、Authority）を統合した総合スコアリングシステムを実装する。単一要素が支配せず、取りこぼしを防止し、LLMが主役となる設計を実現する。

## 背景

### 現状の課題

現在のBuzzスコア（`src/services/buzz_scorer.py`）は以下3要素のみで構成されている:

1. **Recency（鮮度）**: 公開からの経過日数（重み50%）
2. **Consensus（複数ソース出現）**: 同一URLの出現回数（重み40%）
3. **Domain Diversity（ドメイン多様性）**: 同一ドメインの記事数（重み10%）

**計算式**:
```
total_score = (source_count_score × 0.4) + (recency_score × 0.5) + (diversity_score × 0.1)
```

この実装の問題点:

1. **SocialProofの欠如**: はてブ数などの外部反応が考慮されていない
2. **Interestとの未連携**: 興味プロファイルとの一致度が反映されていない
3. **Authorityの未実装**: 公式ブログや一次情報源への補正がない
4. **単一要素の支配**: Recency（50%）が強すぎて、古い重要記事が埋もれる
5. **取りこぼしのリスク**: 話題性が低くても興味と一致する記事が見逃される

### なぜ今実装するか

- **興味リストのマスタ化との連携**: `.steering/20260214-interest-list-master/`でInterestProfileが実装されるため、Interest要素との統合が可能になる
- **判定精度の向上**: Buzzスコアの精度向上により、LLM判定対象の選定がより適切になる
- **PRDの実現**: 「出力最小主義」「判断コストゼロ」を達成するため、LLM投入前の絞り込み精度が重要

## 実装対象の機能

### 1. SocialProof（外部反応）の追加

- はてなブックマーク数を取得・スコア化
- ソースごとに外部指標を収集（Phase 1ははてブのみ、Phase 2でSNS等拡張）
- スコア化ロジック:
  - 0件: 0点
  - 1-9件: 20点
  - 10-49件: 50点
  - 50-99件: 70点
  - 100件以上: 100点

**実装方針**:
- はてブAPIを使用（`https://bookmark.hatenaapis.com/count/entry?url={url}`）
- タイムアウト: 5秒/URL
- 並列度制限: 10件同時（Buzzスコア計算時）
- エラー時: 0点として継続（ログ記録）

### 2. Interest（興味との一致度）の追加

- InterestProfile（興味リストのマスタ化で実装）と記事タイトル・概要のマッチング
- キーワードマッチングによる簡易スコアリング（LLM判定前の粗い判定）

**スコア化ロジック**:
- `high_interest`トピックのキーワードに一致: 100点
- `medium_interest`トピックのキーワードに一致: 60点
- `low_priority`トピックのキーワードに一致: 20点
- いずれにも一致しない: 40点（デフォルト）

**実装方針**:
- InterestProfileから各トピックのキーワードを抽出
- 記事のタイトル・概要に対して部分一致検索（大文字小文字区別なし）
- 複数トピックに一致する場合は最高スコアを採用

### 3. Authority（公式補正）の追加

- 公式ブログ・一次情報源への加点
- SourceConfig（sources.yaml）に`authority_level`フィールドを追加

**スコア化ロジック**:
- `authority_level: official`: 100点（AWS公式、PostgreSQL公式など）
- `authority_level: high`: 80点（Uber Engineering Blogなど）
- `authority_level: medium`: 50点（Zenn、Qiitaなど）
- `authority_level: low` or 未設定: 0点

**実装方針**:
- `config/sources.yaml`に`authority_level`フィールドを追加
- SourceConfigモデルに`authority_level`を追加
- BuzzScorerでArticle.source_nameからauthority_levelを取得

### 4. 優先順位の原則の実装

#### 原則1: 単一要素が支配しない

新しい重み配分:
- **Recency（鮮度）**: 25%（現状50% → 半減）
- **Consensus（複数ソース出現）**: 20%（現状40% → 半減）
- **SocialProof（外部反応）**: 20%（新規）
- **Interest（興味との一致度）**: 25%（新規）
- **Authority（公式補正）**: 10%（新規）

合計: 100%

**計算式**:
```
total_score = (recency × 0.25) + (consensus × 0.20) + (social_proof × 0.20) + (interest × 0.25) + (authority × 0.10)
```

#### 原則2: 取りこぼし防止

- **公式・一次情報は一定程度残る**: Authority要素により、公式ブログは低SocialProofでもスコアが底上げされる
- **話題記事は興味外でも残る**: SocialProofが高ければ、Interestが低くても一定スコアを維持
- **興味一致記事は同条件なら優先される**: Interest要素により、同一条件ならInterest一致記事が上位に

#### 原則3: LLMが主役

- Buzzスコアは「並び替え・絞り込み用」であり、最終的な価値判断はLLMが行う
- 上位150件（推奨120件）を選定後、LLMが詳細判定
- LLM判定結果（Interest Label: ACT_NOW/THINK/FYI/IGNORE）が最終的な選定基準

### 5. BuzzScoreモデルの拡張

現在のBuzzScoreモデルに以下フィールドを追加:

```python
@dataclass
class BuzzScore:
    url: str
    # 既存フィールド
    source_count: int
    recency_score: float
    domain_diversity_score: float  # 廃止候補（重みが小さすぎるため）
    # 新規フィールド
    social_proof_score: float       # SocialProofスコア（0-100）
    interest_score: float           # Interestスコア（0-100）
    authority_score: float          # Authorityスコア（0-100）
    total_score: float              # 総合スコア（0-100）
```

## 受け入れ条件

### SocialProof（外部反応）
- [ ] はてブAPI連携が実装されている
- [ ] タイムアウト・並列度制限が機能している
- [ ] エラー時に0点として継続される
- [ ] スコア化ロジックが実装されている

### Interest（興味との一致度）
- [ ] InterestProfileから興味トピックのキーワードを抽出できる
- [ ] 記事タイトル・概要とのマッチングが機能している
- [ ] スコア化ロジックが実装されている
- [ ] 複数トピック一致時に最高スコアが採用される

### Authority（公式補正）
- [ ] sources.yamlに`authority_level`フィールドが追加されている
- [ ] SourceConfigモデルに`authority_level`が追加されている
- [ ] BuzzScorerでauthority_levelを取得できる
- [ ] スコア化ロジックが実装されている

### 優先順位の原則
- [ ] 新しい重み配分（Recency 25%, Consensus 20%, SocialProof 20%, Interest 25%, Authority 10%）が実装されている
- [ ] 総合スコア計算式が更新されている
- [ ] 単一要素が支配しないことをテストで検証できる

### BuzzScoreモデル
- [ ] 新しいフィールド（social_proof_score, interest_score, authority_score）が追加されている
- [ ] 既存のフィールドとの互換性が保たれている

### テスト
- [ ] SocialProof取得のユニットテスト
- [ ] Interest一致のユニットテスト
- [ ] Authority補正のユニットテスト
- [ ] 総合スコア計算のユニットテスト
- [ ] 取りこぼし防止のシナリオテスト（統合テスト）

## 成功指標

### 定量的目標
- **LLM判定対象の精度向上**: 上位150件に「読むべき記事」が含まれる割合が向上（dry_run実行での確認）
- **取りこぼし率の低減**: 公式ブログ・高Interest記事がLLM判定から漏れる件数が減少
- **テストカバレッジ維持**: 既存のテストが全て通過し、カバレッジが80%以上を維持

### 定性的目標
- **バランスの取れたスコアリング**: 単一要素（RecencyやSocialProofのみ）で上位独占しない
- **柔軟な調整**: 重み配分をYAMLで管理し、コード変更なしで調整可能（Phase 2）
- **拡張性**: 将来的なSNS指標（Twitter/X、Reddit）追加が容易

## スコープ外

以下はこのフェーズでは実装しません:

- **SNS指標（Twitter/X、Reddit）の追加**: Phase 2以降
- **機械学習による重み最適化**: 手動調整のみ（Phase 1）
- **リアルタイムSocialProof取得**: バッチ処理のみ
- **ドメイン多様性の削除**: 影響を確認してから判断（Phase 2で検討）
- **重み配分のYAML管理**: まずはコード内で固定（Phase 2で外部化）

## 参照ドキュメント

- `docs/product-requirements.md` - プロダクト要求定義書（Buzz定量の仕様）
- `docs/functional-design.md` - 機能設計書（Buzzスコア計算アルゴリズム）
- `.steering/20260214-interest-list-master/` - 興味リストのマスタ化（Interest要素との連携）
- `src/services/buzz_scorer.py` - 現在の実装
- `config/sources.yaml` - 収集元マスタ（Authority補正のための拡張）
