#!/bin/bash
# Lambda関数をローカルで実行するスクリプト

set -e

echo "=================================================="
echo "Lambda関数 ローカル実行スクリプト"
echo "=================================================="
echo ""

# .envファイルの存在確認
if [ ! -f ".env" ]; then
    echo "❌ エラー: .envファイルが見つかりません"
    exit 1
fi

# 仮想環境の確認
if [ ! -d ".venv" ]; then
    echo "❌ エラー: .venvディレクトリが見つかりません"
    echo "仮想環境を作成してください: python -m venv .venv"
    exit 1
fi

# 実行モードの選択
echo "実行モードを選択してください:"
echo "1) 本番モード（メール送信あり）"
echo "2) dry_runモード（メール送信なし、LLM判定は実行）"
echo ""
read -p "選択 (1 or 2): " choice

case $choice in
    1)
        echo ""
        echo "本番モードで実行します..."
        .venv/bin/python test_lambda_local.py
        ;;
    2)
        echo ""
        echo "dry_runモードで実行します..."
        .venv/bin/python test_lambda_local.py --dry-run
        ;;
    *)
        echo "❌ 無効な選択です"
        exit 1
        ;;
esac
