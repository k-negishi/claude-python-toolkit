"""`.env` を SSM Parameter Store に同期するCLI."""

from __future__ import annotations

import argparse
import os

import boto3


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Sync .env values into SSM Parameter Store as SecureString"
    )
    parser.add_argument("--env-file", default=".env", help="Path to .env file")
    parser.add_argument(
        "--parameter-name",
        default="/ai-curated-newsletter/dotenv",
        help="SSM parameter name for dotenv content",
    )
    parser.add_argument("--region", default=None, help="AWS region")
    return parser.parse_args()


def _read_env_file(env_file: str) -> str:
    if not os.path.exists(env_file):
        raise FileNotFoundError(f".env file not found: {env_file}")

    with open(env_file, encoding="utf-8") as f:
        content = f.read()

    if content.strip() == "":
        raise ValueError(f".env file is empty: {env_file}")

    return content


def sync_env_to_ssm(dotenv_content: str, *, parameter_name: str, region: str) -> str:
    ssm = boto3.client("ssm", region_name=region)

    ssm.put_parameter(
        Name=parameter_name,
        Type="SecureString",
        Value=dotenv_content,
        Overwrite=True,
    )
    print(f"uploaded: {parameter_name}")

    return parameter_name


def main() -> int:
    args = _parse_args()
    region = args.region or os.getenv("AWS_REGION", "ap-northeast-1")

    dotenv_content = _read_env_file(args.env_file)
    parameter_name = sync_env_to_ssm(
        dotenv_content,
        parameter_name=args.parameter_name,
        region=region,
    )
    print(f"completed: uploaded 1 parameter ({parameter_name})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
