#!/usr/bin/env python3
"""SES メール送信テスト（.env のみ版）."""

import boto3
from dotenv import load_dotenv
import os

# .env 読み込み
load_dotenv()

def main():
    print("=" * 60)
    print("📧 SES メール送信テスト（最小構成）")
    print("=" * 60)

    # 環境変数から直接取得
    aws_region = os.getenv("AWS_REGION", "ap-northeast-1")
    from_address = os.getenv("FROM_ADDRESS")
    to_address = os.getenv("TO_ADDRESS")

    print(f"\n✅ AWS Region: {aws_region}")
    print(f"✅ From: {from_address}")
    print(f"✅ To: {to_address}")

    if not from_address or not to_address:
        print("\n❌ エラー: FROM_ADDRESS または TO_ADDRESS が .env に設定されていません")
        return

    # SES でメール送信
    print("\n📧 SES でメール送信中...")
    ses_client = boto3.client("ses", region_name=aws_region)

    response = ses_client.send_email(
        Source=from_address,
        Destination={"ToAddresses": [to_address]},
        Message={
            "Subject": {"Data": "🎉 Test Email - 最小構成版"},
            "Body": {
                "Text": {
                    "Data": f"""
こんにちは！

これは最小構成でのテストメールです。

送信元: {from_address}
送信先: {to_address}

✅ .env ファイルのみ
✅ Secrets Manager 不要
✅ SSM 不要

---
シンプル！
                    """
                }
            }
        }
    )

    message_id = response.get("MessageId")
    print(f"\n✅ メール送信成功！")
    print(f"   Message ID: {message_id}")
    print(f"\n📬 {to_address} を確認してください。")
    print("=" * 60)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ エラー: {e}")
        import traceback
        traceback.print_exc()
