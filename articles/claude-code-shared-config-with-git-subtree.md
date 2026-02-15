---
title: "Claude Codeの.claude設定を複数プロジェクトで使い回す構成を考えた"
emoji: "🔧"
type: "tech"
topics: ["claudecode", "git", "開発環境"]
published: false
---

## 問題: .claudeがプロジェクトごとにコピペで増殖する

Claude Codeを複数プロジェクトで使っていると、`.claude/`の中身がプロジェクトごとにコピペで散らばる。コマンドやスキルを改善したら、同じ修正を全プロジェクトで繰り返す。設定ファイルの管理としてはかなりつらい状態になる。

一方で、`settings.json`やプロジェクト固有のコマンドなど、プロジェクトごとに違って当然のものもある。全部を共通化すればいいという話ではない。

やりたいことを整理するとこうなる。

- 共通のコマンド・スキル・エージェントは1箇所で管理したい
- プロジェクト固有の設定はプロジェクト側に置きたい
- 両者が自然に共存してほしい

## 考え方: 「共有リポ」と「プロジェクトの.claude/」を分ける

結論として、**共通設定を独立したGitリポジトリに切り出し**、各プロジェクトにはGit Subtreeで取り込む構成にした。

```
プロジェクト/
├── .claude-shared/              # 共有リポをSubtreeで配置
│   ├── commands/
│   ├── skills/
│   └── agents/
├── .claude/                     # Claude Codeが見るディレクトリ
│   ├── commands/
│   │   ├── spec-plan.md         # <- symlink（共通から）
│   │   └── my-deploy.md         # <- 実ファイル（このプロジェクト固有）
│   ├── skills/
│   │   ├── git-commit/          # <- symlink（共通から）
│   │   └── local-qa/            # <- 実ファイル（このプロジェクト固有）
│   └── settings.json            # プロジェクト固有
└── Makefile
```

ポイントは2つある。

**1. Claude Codeが見る`.claude/`と、共有リポの実体`.claude-shared/`を分離する。** Claude Codeは`.claude/`しか見ない。共有リポの実体は`.claude-shared/`に入れて、`.claude/`からはsymlinkで参照する。symlinkか実ファイルかはClaude Codeもgitも区別しないので、透過的に動く。

**2. 「既にファイルがあればsymlinkを張らない」というルールで、共通と固有を共存させる。** symlinkの作成時に同名ファイルの存在チェックを入れるだけで、プロジェクト固有のファイルが共通設定に上書きされることがなくなる。共通のコマンドを特定のプロジェクトだけ差し替えたい場合も、`.claude/`に同名の実ファイルを置けばそちらが優先される。

## 他の方法との比較

共有設定を複数プロジェクトに配る方法は他にもある。Git Subtreeを選ぶ前に検討したものを挙げておく。

### symlinkだけで共有する

一番シンプルなのは、共有リポをローカルの適当な場所にcloneしておいて、各プロジェクトの`.claude/`からsymlinkを張る方法。

```bash
# 共有リポを ~/claude-shared にclone
git clone https://github.com/yourname/claude-shared-config.git ~/claude-shared

# プロジェクトから絶対パスでsymlink
ln -s ~/claude-shared/commands/spec-plan.md .claude/commands/spec-plan.md
```

手軽だが、問題がいくつかある。symlinkが絶対パスになるので、他の開発者が同じパスにcloneしていないと壊れる。`.claude/`の中身をgit管理しようとしても、symlinkの参照先がリポジトリ外なのでチームで共有できない。結局「各自のローカル環境に依存する」構成になってしまう。

個人で1台のマシンだけで使うなら十分だが、チーム開発やCI環境まで考えると厳しい。

### Git Submodule

Git Submoduleは「参照を持つ」方式で、`.claude-shared/`に共有リポのコミットハッシュだけを記録する。cloneした後に`git submodule update --init`が必要で、CIでも追加のステップが要る。`.claude/`のような設定ファイル群でこの手間は割に合わないと感じた。

### Git Subtree

Subtreeは「ファイルをそのまま取り込む」方式で、cloneするだけで全ファイルが揃う。プロジェクト側でローカルに修正してコミットもできるし、その修正を共有リポに還元することもできる。

まとめるとこうなる。

| 方法 | clone直後に動く | チームで共有できる | CI対応 |
|------|:---:|:---:|:---:|
| symlinkだけ | ローカル依存 | 難しい | 難しい |
| Submodule | 追加コマンドが必要 | できる | 追加ステップが必要 |
| **Subtree** | **そのまま動く** | **できる** | **追加ステップ不要** |

設定ファイルの共有にはSubtreeが一番素直だと感じた。

## Makefileで操作をまとめる

Subtreeのコマンドは長いし、symlinkの作成もそれなりに手順がある。これを毎回手で打つのは現実的ではないので、Makefileにまとめた。

```makefile
REPO_URL = https://github.com/yourname/claude-shared-config.git
BRANCH = main

# 初回セットアップ: Subtree追加 + symlink作成
claude-init:
	git subtree add --prefix=.claude-shared $(REPO_URL) $(BRANCH) --squash
	$(MAKE) claude-link

# 共有リポの更新を取り込み + symlink再作成
claude-update:
	git subtree pull --prefix=.claude-shared $(REPO_URL) $(BRANCH) --squash
	$(MAKE) claude-link

# symlink作成（既存ファイルはスキップ）
claude-link:
	@mkdir -p .claude/commands .claude/skills .claude/agents
	@for item in .claude-shared/commands/*; do \
	  name=$$(basename "$$item"); \
	  [ ! -e ".claude/commands/$$name" ] && \
	    ln -s "../../.claude-shared/commands/$$name" ".claude/commands/$$name" || true; \
	done
	# skills, agents も同様の処理
```

覚えるのは3つだけ。

| コマンド | やること |
|---------|--------|
| `make claude-init` | 初回セットアップ |
| `make claude-update` | 共有リポの更新を反映 |
| `make claude-link` | symlinkだけ再作成 |

Makefileの中身を意識する必要はなくて、この3つを叩くだけで運用できる。

`claude-link`の「既存ファイルがあればスキップ」が重要で、これがあるからプロジェクト固有ファイルと共有ファイルが衝突しない。`make claude-update`した後も、プロジェクト固有のファイルはそのまま残る。

## 運用してみて

この構成で複数のPythonプロジェクトを回してみた所感を書いておく。

**修正が1回で済む。** 共有コマンドにバグがあったとき、共有リポで直して各プロジェクトで`make claude-update`するだけ。以前は同じ修正を3つも4つもプロジェクトで繰り返していたのが嘘のように楽になった。

**共通と固有が混ざらない。** `ls -la .claude/commands/`すればsymlinkには`->`が表示されるので、どれが共通でどれが固有かすぐわかる。頭の中で管理する必要がない。

**新規プロジェクトの立ち上げが速い。** `make claude-init`の一発で共有設定が入る。あとは`settings.json`とプロジェクト固有のファイルを足すだけで開発を始められる。

## 注意点

- symlinkはWindowsだと扱いが異なる。チーム全員がmacOS/Linuxなら問題ないが、Windowsユーザーがいる場合は事前に確認が必要
- Subtreeのコミット履歴はプロジェクト側のgit logに混ざる。`--squash`で1コミットにまとめてはいるが、気になる人は気になるかもしれない
- 共有リポの`.gitignore`がプロジェクトと競合することがあるので、`.claude-shared/.gitignore`はプロジェクトの`.gitignore`で除外しておくとよい

## まとめ

Claude Codeの`.claude/`設定を複数プロジェクトで共有するために、共有リポ + Git Subtree + symlinkという構成を採った。考え方はシンプルで、共有したいものは別リポに、プロジェクト固有のものは`.claude/`に直接置く。Makefileで操作をまとめれば、日常の運用は`make claude-update`だけで回る。
