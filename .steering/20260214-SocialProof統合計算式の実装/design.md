# 設計書

## アーキテクチャ概要

SocialProof要素を単一指標（Hatena）から複数指標統合版（yamadashy, Hatena, Zenn, Qiita）に拡張する。

**設計原則**:
- 既存のBuzzScorerインターフェースを維持（破壊的変更なし）
- SocialProofFetcherを拡張し、複数情報源に対応
- 各情報源の取得失敗は個別に処理し、全体のフローを継続
- 外部サービス利用ポリシー（同時接続制限、jitter、リトライ）を一貫して適用

## コンポーネント設計

### 1. MultiSourceSocialProofFetcher（新規）

**責務**:
- 4つの情報源（yamadashy, Hatena, Zenn, Qiita）から指標を取得
- 各指標を0-100のスコアに正規化
- 統合計算式 `S = (0.20Y + 0.45H + 0.25Z + 0.10Q) / sum(observed_weights)` を適用
- 欠損対応（欠損時は分母から除外、全欠損時はS=40）

**実装の要点**:
- 既存のSocialProofFetcherを継承・拡張するのではなく、新しいクラスとして実装
- 各情報源の取得を非同期で並列実行（asyncio.gather）
- 外部サービス利用ポリシーを適用（同時接続制限、jitter、リトライ）
- 取得失敗時は該当指標を欠損扱いにし、ログに記録

**インターフェース**:
```python
class MultiSourceSocialProofFetcher:
    async def fetch_batch(self, articles: list[Article]) -> dict[str, float]:
        """
        複数記事のSocialProofスコアを一括取得する。

        Args:
            articles: 記事リスト

        Returns:
            URLをキーとするSocialProofスコア（0-100）の辞書
        """
        ...
```

### 2. YamadashySignalFetcher（新規）

**責務**:
- yamadashy RSSフィードを取得
- 記事URLがフィードに掲載されているか判定
- Yシグナルを生成（掲載=100、非掲載=0）

**実装の要点**:
- フィードは1回のみ取得し、全記事に対して判定
- 正規化URLで照合（yamadashy RSSのURLも正規化）
- タイムアウト5秒、リトライ3回（2s→4s→8s）

**インターフェース**:
```python
class YamadashySignalFetcher:
    async def fetch_signals(self, urls: list[str]) -> dict[str, int]:
        """
        yamadashy掲載シグナルを取得する。

        Args:
            urls: 記事URLリスト（正規化済み）

        Returns:
            URLをキーとするシグナル（100 or 0）の辞書
        """
        ...
```

### 3. HatenaCountFetcher（拡張）

**責務**:
- はてなブックマーク数を一括取得
- `/count/entries` API使用（最大50件）
- 50件超過時は分割処理
- log変換を使った連続値スコア（0-100）を返す

**実装の要点**:
- 既存のSocialProofFetcherを改修
- APIエンドポイントを `/count/entry` から `/count/entries` に変更
- 50件ごとにバッチ処理
- スコア計算: `H = min(100, log10(count + 1) * 25)`
- タイムアウト5秒、リトライ3回（2s→4s→8s）

**インターフェース**:
```python
class HatenaCountFetcher:
    async def fetch_batch(self, urls: list[str]) -> dict[str, float]:
        """
        はてなブックマーク数を一括取得し、スコア化する。

        Args:
            urls: 記事URLリスト（最大50件、超過時は分割）

        Returns:
            URLをキーとするスコア（0-100）の辞書
        """
        ...
```

### 4. ZennLikeFetcher（新規）

**責務**:
- Zenn週間ランキングAPIから記事リストを取得
- 記事URLがランキングに掲載されているか判定
- 掲載順位に基づくスコア（0-100）を返す

**実装の要点**:
- Zenn API: `https://zenn.dev/api/articles?order=weekly` （ページネーション対応）
  - page=1, page=2, page=3 と順次取得（各ページ最大30件程度）
  - 合計100件程度まで取得（ランキング範囲）
- スコア計算:
  - ランキング1-10位: 100点
  - ランキング11-30位: 80点
  - ランキング31-50位: 60点
  - ランキング51-100位: 40点
  - ランキング外: 0点
- タイムアウト5秒、リトライ3回（2s→4s→8s）
- Zenn以外のURLは欠損扱い（スコア0）
- **slug単位ではなくランキング一覧を取得するため、リクエスト数を大幅削減**

**インターフェース**:
```python
class ZennLikeFetcher:
    async def fetch_batch(self, urls: list[str]) -> dict[str, float]:
        """
        Zenn週間ランキングを取得し、スコア化する。

        Args:
            urls: 記事URLリスト（Zenn以外は欠損扱い）

        Returns:
            URLをキーとするスコア（0-100）の辞書
        """
        ...
```

### 5. QiitaRankFetcher（新規）

**責務**:
- Qiita popular feedから順位を取得
- 段階的変換（上位10件=100, 11-20件=70, etc.）

**実装の要点**:
- Qiita popular feed: `https://qiita.com/popular-items/feed`（既存の収集元）
- フィード内の順位を判定（1位、2位...）
- スコア計算:
  - 上位10件: 100点
  - 11-20件: 70点
  - 21-30件: 40点
  - 31-50件: 20点
  - 51件以降: 0点
- タイムアウト5秒、リトライ3回（2s→4s→8s）
- Qiita以外のURLは欠損扱い（スコア0）

**インターフェース**:
```python
class QiitaRankFetcher:
    async def fetch_batch(self, urls: list[str]) -> dict[str, float]:
        """
        Qiita popular feed内の順位を取得し、スコア化する。

        Args:
            urls: 記事URLリスト（Qiita以外は欠損扱い）

        Returns:
            URLをキーとするスコア（0-100）の辞書
        """
        ...
```

### 6. ExternalServicePolicy（新規）

**責務**:
- 外部サービス利用ポリシーの実装
- 同時接続制限（同一ドメイン1、全体3）
- リクエスト間隔（3〜6秒 jitter）
- リトライ戦略（2s→4s→8s、最大3回）

**実装の要点**:
- asyncio.Semaphoreで同時接続制限
- ドメイン単位のセマフォ管理
- random.uniform(3, 6)でjitter生成
- httpx.AsyncClientのリトライ機能を利用（または自前実装）
- 429 / 5xx のみリトライ対象

**インターフェース**:
```python
class ExternalServicePolicy:
    def __init__(
        self,
        domain_concurrency: int = 1,
        total_concurrency: int = 3,
        jitter_range: tuple[float, float] = (3.0, 6.0),
        timeout: int = 5,
        retry_delays: list[float] = [2.0, 4.0, 8.0],
    ):
        ...

    async def fetch_with_policy(
        self, url: str, client: httpx.AsyncClient
    ) -> httpx.Response:
        """
        外部サービス利用ポリシーを適用してHTTPリクエストを実行する。

        Args:
            url: リクエストURL
            client: httpxクライアント

        Returns:
            HTTPレスポンス

        Raises:
            httpx.HTTPError: リトライ後も失敗した場合
        """
        ...
```

### 7. BuzzScorer（変更なし）

**変更点**:
- `_social_proof_fetcher` の型を `SocialProofFetcher` から `MultiSourceSocialProofFetcher` に変更
- `_calculate_social_proof_score` メソッドは削除（MultiSourceSocialProofFetcherが直接スコアを返す）

**実装の要点**:
- BuzzScorerのインターフェースは維持
- `calculate_scores` メソッドは変更なし
- `_social_proof_fetcher.fetch_batch()` の戻り値が `dict[str, int]`（はてブ数）から `dict[str, float]`（スコア0-100）に変更

## データフロー

### SocialProofスコア統合フロー

```
1. BuzzScorer.calculate_scores(articles)
2. ↓
3. MultiSourceSocialProofFetcher.fetch_batch(articles)
4. ↓
5. 並列実行（asyncio.gather）:
   - YamadashySignalFetcher.fetch_signals(urls)
   - HatenaCountFetcher.fetch_batch(urls)
   - ZennLikeFetcher.fetch_batch(urls)
   - QiitaRankFetcher.fetch_batch(urls)
6. ↓
7. 各指標を統合:
   S = (0.20Y + 0.45H + 0.25Z + 0.10Q) / sum(observed_weights)
8. ↓
9. 欠損対応:
   - 欠損した指標は分母から除外
   - 全欠損時は S=40
10. ↓
11. BuzzScorerに統合スコアを返す
```

### Hatena API最適化フロー

```
1. HatenaCountFetcher.fetch_batch(urls)  # urls: 79件
2. ↓
3. 50件ごとに分割:
   - batch1: urls[0:50]
   - batch2: urls[50:79]
4. ↓
5. 各バッチを並列実行（asyncio.gather）:
   - /count/entries?url=url1&url=url2&...&url=url50
   - /count/entries?url=url51&url=url52&...&url=url79
6. ↓
7. 結果を統合して返す
```

## TDDサイクル

Kent BeckのTDD（Test-Driven Development）に従って実装します。

### RED → GREEN → REFACTOR

1. **RED**: 失敗するテストを先に書く
   - 実装前に期待する動作をテストコードで定義
   - テストを実行し、失敗することを確認

2. **GREEN**: 最小限の実装でテストをパスさせる
   - テストをパスさせるための最小限のコードを書く
   - 美しさや拡張性は気にせず、とにかくテストをパスさせる

3. **REFACTOR**: コード品質を向上させる
   - 重複を排除
   - 命名を改善
   - 設計パターンを適用
   - テストは引き続きパスすることを確認

### TDDの利点

- 設計が明確になる（テストを先に書くことで、インターフェースが明確になる）
- バグが減る（全コードがテストでカバーされる）
- リファクタリングが安全（テストがあるので、壊れたことがすぐわかる）
- ドキュメントになる（テストコードが仕様を表す）

### 実装時の注意点

- 各タスクでRED → GREEN → REFACTORサイクルを回す
- テストを先に書くことを徹底する
- テストが失敗することを確認してから実装を始める

## エラーハンドリング戦略

### カスタムエラークラス

- `SocialProofFetchError`: SocialProof取得失敗時の基底エラー
- `YamadashyFetchError`: yamadashy取得失敗
- `HatenaFetchError`: Hatena取得失敗
- `ZennFetchError`: Zenn取得失敗
- `QiitaFetchError`: Qiita取得失敗

### エラーハンドリングパターン

**個別指標の取得失敗**:
- 該当指標を欠損扱いにする
- WARNINGログを出力
- 他の指標の取得を継続

**全指標の取得失敗**:
- デフォルトスコア（S=40）を返す
- ERRORログを出力
- フロー全体は継続（Buzzスコア計算を止めない）

**リトライ対象**:
- HTTPステータス 429（Too Many Requests）
- HTTPステータス 5xx（Server Error）
- タイムアウト

**リトライ非対象**:
- HTTPステータス 4xx（429以外）
- JSON解析エラー（スコア0として扱う）

## テスト戦略

### ユニットテスト

#### MultiSourceSocialProofFetcher
- [ ] 4指標すべて取得成功時の統合スコア計算
- [ ] 1指標欠損時の統合スコア計算（分母から除外）
- [ ] 2指標欠損時の統合スコア計算
- [ ] 3指標欠損時の統合スコア計算
- [ ] 全指標欠損時のデフォルトスコア（S=40）

#### YamadashySignalFetcher
- [ ] yamadashy RSS取得成功時のシグナル生成
- [ ] 掲載記事のシグナル（100）
- [ ] 非掲載記事のシグナル（0）
- [ ] yamadashy RSS取得失敗時の欠損処理

#### HatenaCountFetcher
- [ ] `/count/entries` API呼び出し成功
- [ ] 50件以下の一括取得
- [ ] 50件超過時の分割処理
- [ ] log変換スコア計算（0件→0, 100件→50, 1000件→75, 10000件→100）
- [ ] API失敗時の欠損処理

#### ZennLikeFetcher
- [ ] Zenn記事URLからslug抽出
- [ ] Zenn API呼び出し成功
- [ ] log変換スコア計算（0件→0, 10件→30, 100件→60, 1000件→90）
- [ ] Zenn以外のURL（欠損扱い）
- [ ] API失敗時の欠損処理

#### QiitaRankFetcher
- [ ] Qiita popular feed取得成功
- [ ] 順位抽出（1位、2位...）
- [ ] 段階的スコア計算（上位10件=100, 11-20件=70, etc.）
- [ ] Qiita以外のURL（欠損扱い）
- [ ] feed取得失敗時の欠損処理

#### ExternalServicePolicy
- [ ] 同時接続制限（同一ドメイン1）
- [ ] 同時接続制限（全体3）
- [ ] リクエスト間隔（3〜6秒 jitter）
- [ ] タイムアウト（5秒）
- [ ] リトライ戦略（2s→4s→8s）
- [ ] 429 / 5xx のみリトライ
- [ ] 4xx（429以外）はリトライしない

### 統合テスト

- [ ] BuzzScorerとMultiSourceSocialProofFetcherの統合
- [ ] 全指標取得成功時のBuzzスコア計算
- [ ] 一部指標欠損時のBuzzスコア計算
- [ ] 外部サービス利用ポリシーの適用確認

### E2Eテスト

- [ ] dry_run実行が成功する
- [ ] 実際のAPIを使った動作確認（Hatena, Zenn, Qiita）
- [ ] yamadashy RSS取得の動作確認

## 依存ライブラリ

既存のライブラリで実装可能（新規追加なし）:

- `httpx`: HTTP クライアント（既存）
- `feedparser`: RSS/Atom パーサー（既存）
- `asyncio`: 非同期処理（標準ライブラリ）

## ディレクトリ構造

```
src/
├── models/
│   └── buzz_score.py  # 変更なし
├── services/
│   ├── buzz_scorer.py  # _social_proof_fetcherの型変更
│   ├── social_proof_fetcher.py  # 既存（Phase 1のまま、削除予定）
│   ├── multi_source_social_proof_fetcher.py  # 新規
│   ├── yamadashy_signal_fetcher.py  # 新規
│   ├── hatena_count_fetcher.py  # 新規（既存のSocialProofFetcherから分離）
│   ├── zenn_like_fetcher.py  # 新規
│   ├── qiita_rank_fetcher.py  # 新規
│   └── external_service_policy.py  # 新規
├── handler.py  # BuzzScorerの初期化を変更
└── orchestrator/
    └── orchestrator.py  # BuzzScorerの初期化を変更

tests/
├── unit/
│   └── services/
│       ├── test_multi_source_social_proof_fetcher.py  # 新規
│       ├── test_yamadashy_signal_fetcher.py  # 新規
│       ├── test_hatena_count_fetcher.py  # 新規
│       ├── test_zenn_like_fetcher.py  # 新規
│       ├── test_qiita_rank_fetcher.py  # 新規
│       └── test_external_service_policy.py  # 新規
└── integration/
    └── test_buzz_scorer_with_multi_source.py  # 新規

config/
└── sources.yaml  # yamadashy RSSを追加
```

## 実装の順序

1. **Hatena API 最適化**（既存の改善）
   - HatenaCountFetcherクラス作成
   - `/count/entries` 対応
   - 50件制約実装

2. **yamadashy RSS追加**
   - YamadashySignalFetcherクラス作成
   - `config/sources.yaml` にyamadashy RSS追加

3. **Zenn API連携**
   - ZennLikeFetcherクラス作成
   - slug抽出ロジック実装
   - log変換スコア計算

4. **Qiita順位取得**
   - QiitaRankFetcherクラス作成
   - popular feed解析
   - 段階的スコア計算

5. **外部サービス利用ポリシー**
   - ExternalServicePolicyクラス作成
   - 同時接続制限
   - jitter実装
   - リトライ戦略

6. **SocialProof統合計算式**
   - MultiSourceSocialProofFetcherクラス作成
   - 4指標統合
   - 欠損対応

7. **BuzzScorerとの統合**
   - BuzzScorerの_social_proof_fetcher型変更
   - handlerとorchestratorの初期化変更

## セキュリティ考慮事項

- 外部APIへのリクエスト時にタイムアウトを設定（5秒）
- リトライ回数を制限（最大3回）
- 同時接続数を制限（レート制限対策）

## パフォーマンス考慮事項

- Hatena API: 79件→1-2件に削減（50件一括取得）
- 4つの情報源を並列取得（asyncio.gather）
- jitter導入によるレート制限エラー削減

## 将来の拡張性

- 新しい情報源の追加が容易（YamadashySignalFetcherと同様のインターフェースで実装）
- 重みの調整が容易（MultiSourceSocialProofFetcherのWEIGHT定数を変更）
- 機械学習による重み最適化の余地（Phase 3以降）
