"""Lambda関数をローカルで直接実行するテストスクリプト.

Usage:
    python test_lambda_local.py              # 本番モード（メール送信あり）
    python test_lambda_local.py --dry-run    # dry_runモード（メール送信なし）
"""

import argparse
import json
import sys
from pathlib import Path
from dotenv import load_dotenv

# .env読み込み
load_dotenv()

# srcモジュールをパスに追加
sys.path.insert(0, str(Path(__file__).parent))

from src.handler import lambda_handler

def main():
    """Lambda関数を直接実行する."""
    # コマンドライン引数の解析
    parser = argparse.ArgumentParser(description="Lambda関数をローカルで実行")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="dry_runモードで実行（メール送信なし、LLM判定は実行）",
    )
    args = parser.parse_args()

    mode = "dry_run" if args.dry_run else "本番"
    print(f"🚀 Lambda関数をローカルで実行します（{mode}モード）...")
    print()

    # イベントデータ
    event = {"dry_run": args.dry_run}

    # Lambda実行
    try:
        response = lambda_handler(event, None)

        print()
        print("✅ Lambda実行完了")
        print(f"ステータスコード: {response['statusCode']}")
        print()
        print("レスポンスボディ:")
        body = json.loads(response['body'])
        print(json.dumps(body, indent=2, ensure_ascii=False))

        return 0
    except Exception as e:
        print()
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
