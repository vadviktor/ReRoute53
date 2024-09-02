#!/usr/bin/env python3

import argparse
import sys
from os import getenv
from typing import Optional

import requests
from boto3.session import Session
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from mypy_boto3_route53.client import Route53Client
from mypy_boto3_route53.type_defs import ListResourceRecordSetsResponseTypeDef
from sentry_sdk import capture_exception
from sentry_sdk import init as sentry_init


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="""
        AWS Route53 updater
        -------------------
        The default action is to update the IP address for the given record name.

        Required ENV vars:
            - AWS_ACCESS_KEY_ID
            - AWS_SECRET_ACCESS_KEY
            - AWS_HOSTED_ZONE_ID
            - AWS_RECORD_NAME
            - SENTRY_DSN
        """,
    )

    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("whats_my_ip", help="Check my real IP address and exit")
    subparsers.add_parser(
        "registered_ip", help="Check the IP address for record-name and exit"
    )

    args = parser.parse_args()

    env_vars_result = check_env_vars()
    if env_vars_result:
        print(env_vars_result)
        parser.print_help()
        sys.exit(1)

    sentry_init(getenv("SENTRY_DSN"))

    if args.command == "whats_my_ip":
        print(f"My current IP address is {public_ip()}")
        sys.exit(0)

    if args.command == "registered_ip":
        ip = registered_ip(
            getenv("AWS_HOSTED_ZONE_ID"),
            getenv("AWS_RECORD_NAME"),
            getenv("AWS_ACCESS_KEY_ID"),
            getenv("AWS_SECRET_ACCESS_KEY"),
        )
        print(f"Registered IP address is {ip}")
        sys.exit(0)

    _update_ip(
        getenv("AWS_HOSTED_ZONE_ID"),
        getenv("AWS_RECORD_NAME"),
        getenv("AWS_ACCESS_KEY_ID"),
        getenv("AWS_SECRET_ACCESS_KEY"),
    )


def _update_ip(hosted_zone_id, record_name, key, secret):
    try:
        pub_ip = public_ip()
        reg_ip = registered_ip(hosted_zone_id, record_name, key, secret)
        _report_healthcheck()

        if pub_ip == reg_ip:
            print("IP is already updated")
            sys.exit(0)

        _route53_client(key, secret).change_resource_record_sets(
            HostedZoneId=hosted_zone_id,
            ChangeBatch={
                "Changes": [
                    {
                        "Action": "UPSERT",
                        "ResourceRecordSet": {
                            "Name": record_name,
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
        healthcheck_url = getenv("HEALTHCHECK_URL")
        if healthcheck_url is None:
            raise ValueError("HEALTHCHECK_URL environment variable is not set.")

        requests.get(healthcheck_url).raise_for_status()
    except (requests.RequestException, ValueError) as e:
        capture_exception(e)
        sys.exit(1)


def registered_ip(hosted_zone_id, record_name, key, secret) -> Optional[str]:
    try:
        response: ListResourceRecordSetsResponseTypeDef = _route53_client(
            key, secret
        ).list_resource_record_sets(
            HostedZoneId=hosted_zone_id,
            StartRecordName=record_name,
            MaxItems="1",
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
        response = requests.get("http://checkip.amazonaws.com/")
        response.raise_for_status()
        return response.text.strip()
    except requests.RequestException as e:
        capture_exception(e)
        sys.exit(1)


def _route53_client(key: str, secret: str) -> Route53Client:
    return Session().client(
        "route53",
        aws_access_key_id=key,
        aws_secret_access_key=secret,
        region_name=getenv("AWS_REGION"),
    )


def check_env_vars() -> str | None:
    """
    Check that all required environment variables are set.

    Returns:
        None if all required environment variables are set, otherwise the list of the missing variables.
    """

    required_env_vars: list[str] = [
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "AWS_HOSTED_ZONE_ID",
        "AWS_RECORD_NAME",
        "SENTRY_DSN",
    ]

    missing_env_vars: list[str] = [
        var for var in required_env_vars if getenv(var) is None
    ]

    if missing_env_vars:
        return f"Error: Missing required environment variables: {', '.join(missing_env_vars)}"

    return None


if __name__ == "__main__":
    main()
