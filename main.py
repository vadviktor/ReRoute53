#!/usr/bin/env python3

import argparse
import sys
from pathlib import Path
from typing import Optional

import httpx
from boto3.session import Session
from botocore.exceptions import ClientError
from mypy_boto3_route53.client import Route53Client
from mypy_boto3_route53.type_defs import ListResourceRecordSetsResponseTypeDef
from pydantic import Field, HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict
from sentry_sdk import capture_exception
from sentry_sdk import init as sentry_init


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).parent / ".env", env_file_encoding="utf-8"
    )

    aws_access_key_id: str = Field(min_length=16)
    aws_secret_access_key: str = Field(min_length=16)
    aws_hosted_zone_id: str = Field(min_length=16)
    aws_record_name: str = Field(min_length=5)
    aws_region: str = Field(min_length=5)
    sentry_dsn: HttpUrl
    healthcheck_url: HttpUrl


def main():
    sentry_init(str(settings.sentry_dsn))

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="""
        AWS Route53 updater
        -------------------
        The default action is to update the IP address for the given record name.
        """,
    )
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("whats_my_ip", help="Check my real IP address and exit")
    subparsers.add_parser(
        "registered_ip", help="Check the IP address for record-name and exit"
    )
    args = parser.parse_args()

    if args.command == "whats_my_ip":
        print(f"My current IP address is {public_ip()}")
        sys.exit(0)

    if args.command == "registered_ip":
        ip = registered_ip()
        print(f"Registered IP address is {ip}")
        sys.exit(0)

    _update_ip()


def _update_ip():
    try:
        pub_ip = public_ip()
        reg_ip = registered_ip()
        _report_healthcheck()

        if pub_ip == reg_ip:
            print("IP is already updated")
            sys.exit(0)

        _route53_client().change_resource_record_sets(
            HostedZoneId=settings.aws_hosted_zone_id,
            ChangeBatch={
                "Changes": [
                    {
                        "Action": "UPSERT",
                        "ResourceRecordSet": {
                            "Name": settings.aws_record_name,
                            "Type": "A",
                            "TTL": 3600,
                            "ResourceRecords": [{"Value": pub_ip}],
                        },
                    }
                ]
            },
        )
    except ClientError as e:
        capture_exception(e)
        print(f"Error: {e}")
        sys.exit(1)


def _report_healthcheck():
    try:
        httpx.get(str(settings.healthcheck_url)).raise_for_status()
    except httpx.HTTPStatusError as e:
        capture_exception(e)
        sys.exit(1)


def registered_ip() -> Optional[str]:
    try:
        response: ListResourceRecordSetsResponseTypeDef = (
            _route53_client().list_resource_record_sets(
                HostedZoneId=settings.aws_hosted_zone_id,
                StartRecordName=settings.aws_record_name,
                MaxItems="1",
            )
        )

        return (
            response.get("ResourceRecordSets", [])[0]
            .get("ResourceRecords", [])[0]
            .get("Value")
        )
    except ClientError as e:
        capture_exception(e)
        sys.exit(1)


def public_ip():
    try:
        response = httpx.get("http://checkip.amazonaws.com/")
        response.raise_for_status()
        return response.text.strip()
    except httpx.HTTPStatusError as e:
        capture_exception(e)
        sys.exit(1)


def _route53_client() -> Route53Client:
    return Session().client(
        "route53",
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
        region_name=settings.aws_region,
    )


if __name__ == "__main__":
    settings = Settings()  # type: ignore
    main()
