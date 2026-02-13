"""東京リージョンでBedrockモデルをテストする."""

import json
import boto3
from dotenv import load_dotenv

def main():
    load_dotenv()

    # 東京リージョンでBedrockクライアント作成
    bedrock_client = boto3.client("bedrock-runtime", region_name="ap-northeast-1")

    # モデルID（推論プロファイルではなく基礎モデルID）
    model_id = "anthropic.claude-3-5-sonnet-20240620-v1:0"

    # リクエストボディ
    request_body = {
        "anthropic_version": "bedrock-2023-05-31",
        "messages": [
            {
                "role": "user",
                "content": "Hello, can you respond with 'Tokyo region test successful'?"
            }
        ],
        "max_tokens": 100
    }

    print(f"Testing Bedrock model: {model_id}")
    print(f"Region: ap-northeast-1")
    print()

    try:
        response = bedrock_client.invoke_model(
            modelId=model_id,
            body=json.dumps(request_body)
        )

        response_body = json.loads(response["body"].read())
        content = response_body["content"][0]["text"]

        print("✅ Success!")
        print(f"Response: {content}")
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
