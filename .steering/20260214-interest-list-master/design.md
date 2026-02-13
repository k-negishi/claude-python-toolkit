# 設計書

## アーキテクチャ概要

SourceMasterと同様のパターンで、**InterestMaster**を実装し、関心プロファイルをYAMLファイルで管理する。

既存パターンの踏襲:
- 設定ファイル: `config/interests.yaml`
- モデル: `src/models/interest_profile.py` (InterestProfileデータクラス)
- リポジトリ: `src/repositories/interest_master.py` (InterestMasterクラス)
- 利用側: `src/services/llm_judge.py` (DI経由でInterestProfileを受け取る)

```mermaid
graph LR
    Config[config/interests.yaml] --> InterestMaster[InterestMaster]
    InterestMaster --> InterestProfile[InterestProfile]
    InterestProfile --> LlmJudge[LlmJudge]
    LlmJudge --> Prompt[動的プロンプト生成]
```

## コンポーネント設計

### 1. config/interests.yaml

**責務**:
- 関心プロファイルの定義
- 判定基準の説明
- 高関心・中関心・低優先度トピックのリスト管理

**YAML構造**:

```yaml
# 関心プロファイル設定
profile:
  # プロファイルの概要（プロンプトに含める）
  summary: |
    プリンシパルエンジニアとして、技術的な深さと実践的な価値を重視します。
    新しい技術トレンド、アーキテクチャ設計、パフォーマンス最適化に関心があります。

  # 高い関心を持つトピック（ACT_NOW / THINK に該当しやすい）
  high_interest:
    - AI/ML（大規模言語モデル、機械学習基盤、プロンプトエンジニアリング）
    - クラウドインフラ（AWS、マイクロサービス、コンテナオーケストレーション）
    - アーキテクチャ設計（DDD、クリーンアーキテクチャ、イベント駆動）
    - パフォーマンス最適化（データベース最適化、分散システム、スケーラビリティ）
    - 開発生産性向上（CI/CD、テスト自動化、開発ツール）
    - セキュリティ（認証認可、脆弱性対策、ゼロトラスト）

  # 中程度の関心を持つトピック（FYI に該当しやすい）
  medium_interest:
    - プログラミング言語の新機能・ベストプラクティス
    - データベース技術（PostgreSQL、NoSQL、NewSQL）
    - フロントエンド技術（React、TypeScript、Webパフォーマンス）
    - 技術マネジメント（エンジニアリング組織、技術戦略）
    - オブザーバビリティ（ログ、メトリクス、トレーシング）

  # 低優先度のトピック（IGNORE に該当しやすい）
  low_priority:
    - 初心者向けチュートリアル
    - 特定の言語・フレームワークの基礎文法
    - プロダクト発表のみで技術的詳細がない記事
    - ニュース速報のみで深い考察がない記事

# 判定基準の定義
criteria:
  act_now:
    label: "ACT_NOW"
    description: "今すぐ読むべき記事（緊急性・重要性が高い）"
    examples:
      - 重大なセキュリティ脆弱性の発見と対策
      - 使用中の技術スタックに直接影響する重要な変更
      - 業界に大きな影響を与える技術トレンド
      - すぐに適用できる実践的な問題解決手法

  think:
    label: "THINK"
    description: "設計判断に役立つ記事（アーキテクチャ・技術選定に有用）"
    examples:
      - アーキテクチャパターンの比較・選定ガイド
      - スケーラビリティ・パフォーマンス最適化の事例
      - 大規模システムの設計・運用ノウハウ
      - 技術選定の意思決定プロセス

  fyi:
    label: "FYI"
    description: "知っておくとよい記事（一般的な技術情報）"
    examples:
      - 新しい技術の概要・紹介
      - 技術トレンドの動向
      - ベストプラクティスの紹介
      - 開発プロセスの改善事例

  ignore:
    label: "IGNORE"
    description: "関心外の記事（上記に該当しない）"
    examples:
      - 関心分野外のトピック
      - 技術的深さがない記事
      - 実践的価値が低い記事
```

**実装の要点**:
- YAMLの構造は変更可能だが、`profile`と`criteria`のトップレベルキーは必須
- コメントを充実させ、編集しやすくする
- 既存のハードコードされた内容を全て移行

### 2. src/models/interest_profile.py

**責務**:
- 関心プロファイルのデータ構造定義
- YAMLからの読み込みとバリデーション
- プロンプト生成用の文字列整形

**実装内容**:

```python
"""関心プロファイルエンティティモジュール."""

from dataclasses import dataclass


@dataclass
class JudgmentCriterion:
    """判定基準の定義.

    Attributes:
        label: 判定ラベル（ACT_NOW/THINK/FYI/IGNORE）
        description: 判定基準の説明
        examples: 該当する記事の例
    """

    label: str
    description: str
    examples: list[str]


@dataclass
class InterestProfile:
    """関心プロファイル.

    Attributes:
        summary: プロファイルの概要
        high_interest: 高い関心を持つトピックのリスト
        medium_interest: 中程度の関心を持つトピックのリスト
        low_priority: 低優先度のトピックのリスト
        criteria: 判定基準の辞書（キー: act_now/think/fyi/ignore）
    """

    summary: str
    high_interest: list[str]
    medium_interest: list[str]
    low_priority: list[str]
    criteria: dict[str, JudgmentCriterion]

    def format_for_prompt(self) -> str:
        """プロンプト用に関心プロファイルを整形する.

        Returns:
            プロンプトに埋め込むための文字列
        """
        lines = [self.summary.strip(), ""]

        if self.high_interest:
            lines.append("**強い関心を持つトピック**:")
            for topic in self.high_interest:
                lines.append(f"- {topic}")
            lines.append("")

        if self.medium_interest:
            lines.append("**中程度の関心を持つトピック**:")
            for topic in self.medium_interest:
                lines.append(f"- {topic}")
            lines.append("")

        if self.low_priority:
            lines.append("**低優先度のトピック**:")
            for topic in self.low_priority:
                lines.append(f"- {topic}")
            lines.append("")

        return "\n".join(lines).strip()

    def format_criteria_for_prompt(self) -> str:
        """判定基準をプロンプト用に整形する.

        Returns:
            プロンプトに埋め込むための判定基準文字列
        """
        lines = []
        for key in ["act_now", "think", "fyi", "ignore"]:
            if key in self.criteria:
                criterion = self.criteria[key]
                lines.append(f"- **{criterion.label}**: {criterion.description}")
                if criterion.examples:
                    lines.append("  - 該当例:")
                    for example in criterion.examples:
                        lines.append(f"    - {example}")

        return "\n".join(lines)
```

**実装の要点**:
- dataclassを使用し、既存のモデルと統一
- `format_for_prompt()`メソッドでプロンプト生成用の文字列を返す
- 将来的な拡張（複数プロファイル対応）を考慮した設計

### 3. src/repositories/interest_master.py

**責務**:
- `config/interests.yaml`からInterestProfileを読み込む
- シングルトンパターンまたはキャッシュによる効率化
- SourceMasterと同様の設計パターンを踏襲

**実装内容**:

```python
"""関心マスタリポジトリモジュール."""

import yaml
from pathlib import Path

from src.models.interest_profile import InterestProfile, JudgmentCriterion
from src.shared.logging.logger import get_logger

logger = get_logger(__name__)


class InterestMaster:
    """関心マスタ.

    config/interests.yamlから関心プロファイルを読み込む.

    Attributes:
        _config_path: 設定ファイルパス
        _profile: 読み込んだプロファイル（キャッシュ）
    """

    def __init__(self, config_path: str | Path) -> None:
        """関心マスタを初期化する.

        Args:
            config_path: 設定ファイルパス（config/interests.yaml）
        """
        self._config_path = Path(config_path)
        self._profile: InterestProfile | None = None

    def get_profile(self) -> InterestProfile:
        """関心プロファイルを取得する.

        Returns:
            関心プロファイル

        Raises:
            FileNotFoundError: 設定ファイルが見つからない場合
            ValueError: YAML解析に失敗した場合
        """
        if self._profile is not None:
            return self._profile

        logger.info("interest_profile_load_start", config_path=str(self._config_path))

        if not self._config_path.exists():
            raise FileNotFoundError(f"Interest config file not found: {self._config_path}")

        with open(self._config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        # YAMLからInterestProfileを生成
        profile_data = data.get("profile", {})
        criteria_data = data.get("criteria", {})

        # 判定基準の辞書を作成
        criteria = {}
        for key, value in criteria_data.items():
            criteria[key] = JudgmentCriterion(
                label=value.get("label", ""),
                description=value.get("description", ""),
                examples=value.get("examples", []),
            )

        self._profile = InterestProfile(
            summary=profile_data.get("summary", ""),
            high_interest=profile_data.get("high_interest", []),
            medium_interest=profile_data.get("medium_interest", []),
            low_priority=profile_data.get("low_priority", []),
            criteria=criteria,
        )

        logger.info(
            "interest_profile_loaded",
            high_interest_count=len(self._profile.high_interest),
            medium_interest_count=len(self._profile.medium_interest),
            low_priority_count=len(self._profile.low_priority),
        )

        return self._profile
```

**実装の要点**:
- SourceMasterと同様のパターンを踏襲（キャッシュ、エラーハンドリング）
- YAMLの読み込みとバリデーションを実装
- ログ出力で設定の読み込みを追跡可能に

### 4. src/services/llm_judge.py の改修

**責務**:
- InterestProfileを受け取り、動的にプロンプトを生成
- ハードコードされた関心プロファイル文字列を削除

**変更箇所**:

```python
class LlmJudge:
    def __init__(
        self,
        bedrock_client: Any,
        cache_repository: CacheRepository | None,
        interest_profile: InterestProfile,  # 追加
        model_id: str,
        max_retries: int = 2,
        concurrency_limit: int = 5,
    ) -> None:
        """LLM判定サービスを初期化する.

        Args:
            bedrock_client: Bedrock Runtimeクライアント
            cache_repository: キャッシュリポジトリ
            interest_profile: 関心プロファイル  # 追加
            model_id: 使用するLLMモデルID
            max_retries: 最大リトライ回数
            concurrency_limit: 並列度制限
        """
        self._bedrock_client = bedrock_client
        self._cache_repository = cache_repository
        self._interest_profile = interest_profile  # 追加
        self._model_id = model_id
        self._max_retries = max_retries
        self._concurrency_limit = concurrency_limit

    def _build_prompt(self, article: Article) -> str:
        """判定プロンプトを生成する（動的生成に変更）.

        Args:
            article: 判定対象記事

        Returns:
            プロンプト文字列
        """
        # InterestProfileから動的に生成
        profile_text = self._interest_profile.format_for_prompt()
        criteria_text = self._interest_profile.format_criteria_for_prompt()

        return f"""以下の記事について、関心度と話題性を判定してください。

# 関心プロファイル
{profile_text}

# 記事情報
- タイトル: {article.title}
- URL: {article.url}
- 概要: {article.description}
- ソース: {article.source_name}

# 判定基準
**interest_label**（関心度）:
{criteria_text}

**buzz_label**（話題性）:
- HIGH: 非常に話題（多くのエンジニアが注目）
- MID: 中程度の話題
- LOW: 低い話題性

**confidence**（信頼度）: 0.0-1.0の範囲で判定の確信度を示す
**reason**（理由）: 判定理由を簡潔に説明（最大200文字）

# 出力形式
JSON形式で以下のキーを含めて出力してください:
{{
  "interest_label": "ACT_NOW" | "THINK" | "FYI" | "IGNORE",
  "buzz_label": "HIGH" | "MID" | "LOW",
  "confidence": 0.85,
  "reason": "判定理由の説明"
}}

JSON以外は出力しないでください。"""
```

**実装の要点**:
- `__init__`にInterestProfileを追加
- `_build_prompt`でハードコード部分を削除し、InterestProfileから動的生成
- 既存のロジックに影響を与えない

## データフロー

### 関心プロファイル読み込みフロー

```
1. Orchestratorの初期化時
   → InterestMaster(config_path="config/interests.yaml") を生成

2. InterestMaster.get_profile()を呼び出し
   → config/interests.yamlを読み込み
   → InterestProfileインスタンスを生成・キャッシュ

3. LlmJudgeの初期化
   → InterestProfileをDI経由で受け取る

4. LLM判定時
   → _build_prompt()でInterestProfile.format_for_prompt()を呼び出し
   → 動的にプロンプトを生成
```

## エラーハンドリング戦略

### カスタムエラークラス

既存のエラー体系に従い、新規のカスタムエラーは不要。ただし、以下のエラーケースを考慮:

- **FileNotFoundError**: `config/interests.yaml`が存在しない場合
  - InterestMaster.get_profile()で発生
  - 起動時に検知し、明確なエラーメッセージを出力

- **yaml.YAMLError**: YAML解析に失敗した場合
  - InterestMaster.get_profile()で発生
  - ValueError にラップして再スロー

- **KeyError/ValueError**: YAML内の必須フィールドが欠けている場合
  - InterestMaster.get_profile()で発生
  - 明確なエラーメッセージで通知

### エラーハンドリングパターン

```python
def get_profile(self) -> InterestProfile:
    try:
        with open(self._config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except FileNotFoundError:
        logger.error("interest_config_not_found", path=str(self._config_path))
        raise
    except yaml.YAMLError as e:
        logger.error("interest_config_parse_error", path=str(self._config_path), error=str(e))
        raise ValueError(f"Failed to parse interests.yaml: {e}") from e

    # 必須フィールドのバリデーション
    if "profile" not in data:
        raise ValueError("Missing 'profile' key in interests.yaml")
    if "criteria" not in data:
        raise ValueError("Missing 'criteria' key in interests.yaml")
```

## テスト戦略

### ユニットテスト

#### tests/unit/repositories/test_interest_master.py
- `config/interests.yaml`の正常読み込み
- ファイル不在時のFileNotFoundError
- YAML解析エラー時のValueError
- キャッシュが機能すること（2回目の呼び出しでファイル読み込みが発生しない）

#### tests/unit/models/test_interest_profile.py
- `format_for_prompt()`の出力形式検証
- `format_criteria_for_prompt()`の出力形式検証
- 空リストの場合の挙動

#### tests/unit/services/test_llm_judge.py（既存テストの更新）
- InterestProfileをモックして注入
- `_build_prompt()`の出力にInterestProfileの内容が含まれることを検証
- プロンプトスナップショットテストの追加（将来的な変更検知）

### 統合テスト

#### tests/integration/test_interest_master_integration.py
- 実際の`config/interests.yaml`を使用した読み込みテスト
- InterestMaster → LlmJudge のDI連携テスト

### E2Eテスト

#### tests/e2e/test_orchestrator_e2e.py（既存テストの更新）
- Orchestratorの初期化時にInterestMasterが正しく動作すること
- LLM判定が正常に実行されること（dry_runモード）

## 依存ライブラリ

新規追加なし。既存の依存ライブラリで対応:
- `pyyaml`: YAML読み込み（既に使用中）

## ディレクトリ構造

```
ai-curated-newsletter/
├── config/
│   ├── sources.yaml          # 既存
│   └── interests.yaml         # 新規追加
│
├── src/
│   ├── models/
│   │   ├── interest_profile.py  # 新規追加
│   │   └── ...
│   │
│   ├── repositories/
│   │   ├── interest_master.py   # 新規追加
│   │   ├── source_master.py     # 既存（参考）
│   │   └── ...
│   │
│   └── services/
│       ├── llm_judge.py         # 改修
│       └── ...
│
└── tests/
    ├── unit/
    │   ├── models/
    │   │   └── test_interest_profile.py  # 新規追加
    │   ├── repositories/
    │   │   └── test_interest_master.py   # 新規追加
    │   └── services/
    │       └── test_llm_judge.py          # 更新
    │
    ├── integration/
    │   └── test_interest_master_integration.py  # 新規追加
    │
    └── e2e/
        └── test_orchestrator_e2e.py       # 更新
```

## 実装の順序

1. **config/interests.yaml の作成**
   - 既存のハードコードされた内容を移行
   - YAML構造を設計通りに実装

2. **src/models/interest_profile.py の実装**
   - InterestProfile, JudgmentCriterion データクラスを定義
   - format_for_prompt(), format_criteria_for_prompt() を実装

3. **src/repositories/interest_master.py の実装**
   - InterestMaster クラスを実装
   - YAML読み込みとバリデーション

4. **src/services/llm_judge.py の改修**
   - `__init__`にInterestProfileを追加
   - `_build_prompt`を動的生成に変更
   - ハードコード削除

5. **Orchestratorの修正**
   - InterestMasterの初期化を追加
   - LlmJudgeへのDI設定

6. **テストの追加・更新**
   - ユニットテスト追加
   - 統合テスト追加
   - E2Eテスト更新

7. **品質チェック**
   - pytest, ruff, mypy 実行
   - dry_run実行で動作確認

## セキュリティ考慮事項

- **YAML Injection**: yaml.safe_load()を使用し、任意コード実行を防止
- **ファイルアクセス**: config/以下のファイルのみ読み込み、パストラバーサル対策は不要（固定パス）

## パフォーマンス考慮事項

- **キャッシュ**: InterestMaster.get_profile()で一度読み込んだプロファイルをキャッシュ
- **読み込みタイミング**: Lambda起動時に一度だけ読み込み、実行中は再読み込みしない
- **ファイルサイズ**: interests.yamlは数KB程度なので、読み込みオーバーヘッドは無視できる

## 将来の拡張性

### Phase 2以降の拡張方針

1. **複数プロファイル対応**
   - interests.yamlに複数のprofileセクションを定義
   - get_profile(profile_name: str)で特定プロファイルを取得

2. **DynamoDB管理への移行**
   - InterestMasterの実装を変更し、DynamoDBから読み込み
   - 動的なプロファイル更新が可能に

3. **フィードバック連携**
   - ユーザーフィードバックを元にプロファイルを自動調整
   - 機械学習による最適化

4. **マルチユーザー対応**
   - ユーザーごとに異なるプロファイルを管理
   - プロファイルIDをパラメータで指定

これらの拡張時も、今回実装するInterestProfile/InterestMasterの基本構造は変更不要。
