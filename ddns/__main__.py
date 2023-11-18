#!/usr/bin/env python3

import argparse
import sys
from os import getenv
from typing import Union

import boto3
import requests
from botocore.exceptions import ClientError
from sentry_sdk import capture_exception
from sentry_sdk import init as sentry_init
from sentry_sdk.crons import monitor

AWS_REGION = "eu-west-1"


def main():
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

    update_ip(
        getenv("AWS_HOSTED_ZONE_ID"),
        getenv("AWS_RECORD_NAME"),
        getenv("AWS_ACCESS_KEY_ID"),
        getenv("AWS_SECRET_ACCESS_KEY"),
    )


@monitor(monitor_slug="router")
def update_ip(hosted_zone_id, record_name, key, secret):
    try:
        pub_ip = public_ip()
        reg_ip = registered_ip(hosted_zone_id, record_name, key, secret)

        if pub_ip == reg_ip:
            print("IP is already updated")
            sys.exit(0)

        route53_client(key, secret).change_resource_record_sets(
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


def registered_ip(hosted_zone_id, record_name, key, secret):
    try:
        response = route53_client(key, secret).list_resource_record_sets(
            HostedZoneId=hosted_zone_id,
            StartRecordName=record_name,
            MaxItems="1",
        )

        return response["ResourceRecordSets"][0]["ResourceRecords"][0]["Value"]
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


def route53_client(key, secret):
    return boto3.client(
        "route53",
        aws_access_key_id=key,
        aws_secret_access_key=secret,
        region_name=AWS_REGION,
    )


def check_env_vars() -> Union[str, None]:
    """
    Check that all required environment variables are set.

    Returns:
        None if all required environment variables are set, otherwise the list of the missing variables.
    """

    required_env_vars = [
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "AWS_HOSTED_ZONE_ID",
        "AWS_RECORD_NAME",
        "SENTRY_DSN",
    ]

    missing_env_vars = [var for var in required_env_vars if getenv(var) is None]

    if missing_env_vars:
        return f"Error: Missing required environment variables: {', '.join(missing_env_vars)}"


if __name__ == "__main__":
    main()
