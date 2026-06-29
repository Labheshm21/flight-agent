import json
import os
import time
from datetime import datetime, timezone
from functools import lru_cache
from typing import Any

from dotenv import load_dotenv

load_dotenv()


def _load_boto3():
    try:
        import boto3
        from botocore.exceptions import ClientError
    except ImportError:
        return None, None
    return boto3, ClientError


def _aws_region() -> str:
    return os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION") or "us-east-1"


def _trim(value: str, limit: int = 50000) -> str:
    if len(value) <= limit:
        return value
    return value[:limit] + "\n\n[truncated]"


@lru_cache(maxsize=1)
def _dynamodb_resource():
    boto3, _ = _load_boto3()
    if boto3 is None:
        return None
    return boto3.resource("dynamodb", region_name=_aws_region())


@lru_cache(maxsize=1)
def _logs_client():
    boto3, _ = _load_boto3()
    if boto3 is None:
        return None
    return boto3.client("logs", region_name=_aws_region())


def aws_enabled() -> bool:
    boto3, _ = _load_boto3()
    return boto3 is not None and bool(os.getenv("TRAVEL_PLANS_TABLE"))


def save_travel_plan_record(
    *,
    plan_id: str,
    user_id: str,
    query: str,
    filename: str,
    file_content: str,
    collected: dict[str, Any],
) -> tuple[bool, str]:
    table_name = os.getenv("TRAVEL_PLANS_TABLE")
    dynamodb = _dynamodb_resource()

    if not table_name:
        return False, "TRAVEL_PLANS_TABLE is not configured."
    if dynamodb is None:
        return False, "boto3 is not installed."

    item = {
        "plan_id": plan_id,
        "user_id": user_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "query": query,
        "filename": filename,
        "llm_calls": int(collected.get("llm_calls", 0)),
        "flight_results": _trim(collected.get("flight_results", "")),
        "hotel_results": _trim(collected.get("hotel_results", "")),
        "itinerary": _trim(collected.get("itinerary", "")),
        "final_response": _trim(collected.get("final_response", "")),
        "plan_markdown": _trim(file_content, limit=100000),
    }

    try:
        table = dynamodb.Table(table_name)
        table.put_item(Item=item)
    except Exception as exc:
        return False, f"DynamoDB save failed: {exc}"

    return True, f"Saved to DynamoDB table {table_name}."


def log_travel_event(event_name: str, payload: dict[str, Any]) -> tuple[bool, str]:
    log_group = os.getenv("CLOUDWATCH_LOG_GROUP", "/ai-travel-booking")
    log_stream = os.getenv("CLOUDWATCH_LOG_STREAM", "streamlit-app")
    logs = _logs_client()
    _, ClientError = _load_boto3()

    if logs is None or ClientError is None:
        return False, "boto3 is not installed."

    try:
        _ensure_log_destination(logs, ClientError, log_group, log_stream)
        kwargs: dict[str, Any] = {
            "logGroupName": log_group,
            "logStreamName": log_stream,
            "logEvents": [
                {
                    "timestamp": int(time.time() * 1000),
                    "message": json.dumps(
                        {
                            "event": event_name,
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            **payload,
                        },
                        default=str,
                    ),
                }
            ],
        }

        token = _sequence_token(logs, log_group, log_stream)
        if token:
            kwargs["sequenceToken"] = token

        logs.put_log_events(**kwargs)
    except ClientError as exc:
        error = exc.response.get("Error", {})
        if error.get("Code") == "InvalidSequenceTokenException":
            message = error.get("Message", "")
            token = message.rsplit(" ", 1)[-1] if " " in message else None
            if token:
                kwargs["sequenceToken"] = token
                logs.put_log_events(**kwargs)
                return True, f"Logged to CloudWatch group {log_group}."
        return False, f"CloudWatch log failed: {exc}"
    except Exception as exc:
        return False, f"CloudWatch log failed: {exc}"

    return True, f"Logged to CloudWatch group {log_group}."


def _ensure_log_destination(logs, ClientError, log_group: str, log_stream: str) -> None:
    try:
        logs.create_log_group(logGroupName=log_group)
    except ClientError as exc:
        if exc.response.get("Error", {}).get("Code") != "ResourceAlreadyExistsException":
            raise

    try:
        logs.create_log_stream(logGroupName=log_group, logStreamName=log_stream)
    except ClientError as exc:
        if exc.response.get("Error", {}).get("Code") != "ResourceAlreadyExistsException":
            raise


def _sequence_token(logs, log_group: str, log_stream: str) -> str | None:
    response = logs.describe_log_streams(
        logGroupName=log_group,
        logStreamNamePrefix=log_stream,
        limit=1,
    )
    streams = response.get("logStreams", [])
    if not streams:
        return None
    return streams[0].get("uploadSequenceToken")
