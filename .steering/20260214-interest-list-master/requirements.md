# 要求内容

## 概要

LLM判定で使用する「関心プロファイル」をコード内のハードコードから外部設定ファイル（YAML）に切り出し、判定アルゴリズムをより柔軟で管理しやすくする。

## 背景

### 現状の課題

現在、LLM判定サービス（`src/services/llm_judge.py`）の`_build_prompt`メソッド内で、関心プロファイルがハードコードされている:

```python
def _build_prompt(self, article: Article) -> str:
    return f"""以下の記事について、関心度と話題性を判定してください。

# 関心プロファイル
- プリンシパルエンジニアとして、技術的な深さと実践的な価値を重視
- 新しい技術トレンド、アーキテクチャ設計、パフォーマンス最適化に関心
- AI/ML、クラウドインフラ、開発生産性向上のトピックに注目
...
```

この実装の問題点:
1. **保守性**: 関心の変更ごとにコード修正が必要
2. **テスト困難性**: プロファイルを切り替えたテストが難しい
3. **一貫性**: 収集元（sources.yaml）はマスタ化されているのに、関心プロファイルはハードコード
4. **拡張性**: 複数ユーザー対応（将来）や複数プロファイル切り替えが困難

### なぜ今実装するか

- **収集元マスタとの一貫性**: 既にsources.yamlで収集元をマスタ管理しているため、関心プロファイルも同様に外部化すべき
- **スペック駆動開発の実践**: PRD（product-requirements.md）には「関心プロファイル更新はコード変更不要（設定ファイル or DynamoDB管理）」と明記されている（342行目）
- **Phase 2への準備**: 将来のフィードバック機能やプロファイル自動最適化に向けた基盤整備

## 実装対象の機能

### 1. 関心プロファイルのマスタ化

- `config/interests.yaml`を新規作成し、関心プロファイルを外部定義
- 以下の情報を管理:
  - **強い関心（high_interest）**: ACT_NOW/THINKに該当しやすいトピック
  - **中程度の関心（medium_interest）**: FYIに該当しやすいトピック
  - **低優先度（low_priority）**: IGNOREに該当しやすいトピック
  - **判定基準の説明**: 各ラベル（ACT_NOW/THINK/FYI/IGNORE）の意味

### 2. InterestProfile エンティティの追加

- `src/models/interest_profile.py`を新規作成
- 関心プロファイルを表現するデータクラスを定義
- YAMLからの読み込み機能を実装

### 3. InterestMaster の追加

- `src/repositories/interest_master.py`を新規作成
- SourceMasterと同様に、設定ファイルから関心プロファイルを読み込む責務を持つ
- シングルトンパターンまたはDI経由で利用

### 4. LlmJudge の改修

- `_build_prompt`メソッドを改修し、InterestProfileから動的にプロンプトを生成
- ハードコードされた関心プロファイル文字列を削除
- InterestMasterまたはInterestProfileインスタンスをDI経由で受け取る

## 受け入れ条件

### 関心プロファイルのマスタ化
- [ ] `config/interests.yaml`が作成され、関心プロファイルが定義されている
- [ ] YAML内に`high_interest`, `medium_interest`, `low_priority`, `criteria`のセクションが存在する
- [ ] 既存のハードコードされた関心内容が全てYAMLに移行されている

### InterestProfile エンティティ
- [ ] `src/models/interest_profile.py`が作成されている
- [ ] `InterestProfile`データクラスが定義されている
- [ ] YAMLからInterestProfileインスタンスを生成できる

### InterestMaster の追加
- [ ] `src/repositories/interest_master.py`が作成されている
- [ ] `InterestMaster`クラスが実装されている
- [ ] `get_profile()`メソッドでInterestProfileを取得できる
- [ ] SourceMasterと同様の設計パターンを踏襲している

### LlmJudge の改修
- [ ] `__init__`メソッドでInterestProfileまたはInterestMasterを受け取る
- [ ] `_build_prompt`メソッドが動的にプロンプトを生成する
- [ ] ハードコードされた関心プロファイル文字列が削除されている
- [ ] 既存の判定ロジックに影響がない（同等の判定結果が得られる）

### テスト
- [ ] InterestMasterのユニットテストが追加されている
- [ ] InterestProfileのインスタンス生成テストが追加されている
- [ ] LlmJudgeの統合テストがInterestProfileを使用するよう更新されている
- [ ] プロンプト生成のスナップショットテストが追加されている（将来的な変更検知のため）

## 成功指標

### 定量的目標
- **コード変更なし**: 関心プロファイルの変更時、Pythonコードを修正せずにYAML編集のみで対応可能
- **テストカバレッジ維持**: 既存のテストが全て通過し、カバレッジが80%以上を維持
- **判定精度維持**: 既存の判定結果と同等の精度を保つ（dry_run実行での確認）

### 定性的目標
- **保守性向上**: 関心の追加・削除・変更がYAML編集のみで完結
- **一貫性向上**: 収集元マスタと関心マスタで設計パターンが統一
- **拡張性向上**: 複数プロファイルへの対応が容易になる基盤

## スコープ外

以下はこのフェーズでは実装しません:

- **複数プロファイルの切り替え機能**: 単一プロファイルのみ対応（Phase 2以降）
- **DynamoDB管理への移行**: まずは設定ファイル（YAML）での管理を実装（PRDのPhase 1方針に従う）
- **プロファイルの動的更新**: Lambda実行中のプロファイル変更は未対応
- **フィードバック機能との連携**: Phase 2の機能であり、今回は基盤整備のみ
- **プロファイル自動最適化**: 将来的な拡張機能

## 参照ドキュメント

- `docs/product-requirements.md` - プロダクト要求定義書（特に342行目「関心プロファイル更新はコード変更不要」）
- `docs/functional-design.md` - 機能設計書（LlmJudgeとSourceMasterの設計パターン）
- `docs/architecture.md` - アーキテクチャ設計書
- `config/sources.yaml` - 収集元マスタの実装例（同様のパターンを踏襲）
- `src/services/llm_judge.py` - 現在の実装（ハードコード箇所の確認）
