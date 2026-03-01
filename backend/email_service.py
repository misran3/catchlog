# backend/email_service.py
"""AWS SES email service for compliance alerts."""

import os
import boto3
from botocore.exceptions import ClientError


def send_email(to: str, subject: str, body: str) -> bool:
    """
    Send email via AWS SES.

    Returns True if sent successfully, False otherwise.
    """
    from_email = os.getenv("SES_FROM_EMAIL")
    region = os.getenv("AWS_REGION", "us-east-1")

    if not from_email:
        print(f"[EMAIL] SES_FROM_EMAIL not set. Would send to {to}:")
        print(f"[EMAIL] Subject: {subject}")
        print(f"[EMAIL] Body: {body[:200]}...")
        return False

    try:
        client = boto3.client("ses", region_name=region)

        response = client.send_email(
            Source=from_email,
            Destination={"ToAddresses": [to]},
            Message={
                "Subject": {"Data": subject, "Charset": "UTF-8"},
                "Body": {"Text": {"Data": body, "Charset": "UTF-8"}},
            },
        )

        print(f"[EMAIL] Sent successfully. MessageId: {response['MessageId']}")
        return True

    except ClientError as e:
        print(f"[EMAIL] Failed to send: {e.response['Error']['Message']}")
        return False
