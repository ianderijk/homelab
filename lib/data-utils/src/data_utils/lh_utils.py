import functools
import io
import os
from collections.abc import Callable
from contextvars import ContextVar
from typing import Any, Literal

import boto3
import polars as pl

s3_var: ContextVar[Any] = ContextVar("_s3", default=None)
buckets_var: ContextVar[list[str] | None] = ContextVar("_buckets", default=None)


def get_s3() -> Any:
    if s3_var.get() is None:
        access_key = os.getenv("RUSTFS_ROOT_USER")
        secret_key = os.getenv("RUSTFS_ROOT_PASSWORD")
        endpoint = os.getenv("RUSTFS_ENDPOINT", "http://127.0.0.1:9000")

        s3_var.set(
            boto3.client(
                "s3",
                endpoint_url=endpoint,
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
            )
        )
    return s3_var.get()


def _get_buckets_list(s3_client=None) -> list[str]:
    client = s3_client or get_s3()
    cached = buckets_var.get()

    if cached is None:
        buckets_data = client.list_buckets()
        cached = [x["Name"] for x in buckets_data.get("Buckets", [])]
        buckets_var.set(cached)

    return cached


def bucket_handler(func: Callable):

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        s3_client = kwargs.get("s3") or get_s3()
        bucket_name = kwargs.get("bucket_name", "default-bucket").replace("_", "-")
        kwargs["bucket_name"] = bucket_name

        existing_buckets = _get_buckets_list(s3_client)

        if bucket_name not in existing_buckets:
            s3_client.create_bucket(Bucket=bucket_name)
            existing_buckets.append(bucket_name)

        return func(*args, **kwargs)

    return wrapper


@bucket_handler
def send_to_bucket(
    bucket_name: str,
    partition_name: str,
    bytes_: bytes,
    filename: str,
    filetype: str,
    s3=None,
) -> None:
    client = s3 or get_s3()
    ext = filetype if filetype.startswith(".") else f".{filetype}"

    client.put_object(
        Bucket=bucket_name,
        Key=f"{partition_name}/{filename}{ext}",
        Body=bytes_,
        ContentType="application/octet-stream",
    )


def list_files(
    bucket_name: str,
    partitions: str | None = None,
    *,
    s3=None,
    max_files: int | None = None,
) -> list[str]:
    client = s3 or get_s3()
    prefix = f"{partitions}/" if partitions else ""
    paginator = client.get_paginator("list_objects_v2")
    pages = paginator.paginate(Bucket=bucket_name, Prefix=prefix)

    files = []
    for page in pages:
        for obj in page.get("Contents", []):
            files.append(obj["Key"])
            if max_files and len(files) >= max_files:
                return files[:max_files]

    return files


def read_file(bucket_name: str, key: str, s3=None) -> bytes:
    client = s3 or get_s3()
    response = client.get_object(Bucket=bucket_name, Key=key)
    return response["Body"].read()


def write_df_to_parquet(
    df: pl.DataFrame,
    bucket_name: str,
    partition_name: str,
    filename: str,
    s3=None,
) -> None:
    client = s3 or get_s3()

    filename = filename.removesuffix(".parquet")

    buffer = io.BytesIO()
    df.write_parquet(buffer)

    send_to_bucket(
        bucket_name=bucket_name,
        partition_name=partition_name,
        bytes_=buffer.getvalue(),
        filename=filename,
        filetype=".parquet",
        s3=client,
    )


@bucket_handler
def write_delta(
    df: pl.DataFrame,
    bucket_name: str,
    table_name: str,
    mode: Literal[
        "error",
        "append",
        "overwrite",
        "ignore",
    ] = "overwrite",
) -> None:
    storage_options = {
        "AWS_ENDPOINT_URL": os.getenv("RUSTFS_ENDPOINT", "http://127.0.0.1:9000"),
        "AWS_ACCESS_KEY_ID": os.getenv("RUSTFS_ROOT_USER", "rustfsadmin"),
        "AWS_SECRET_ACCESS_KEY": os.getenv("RUSTFS_ROOT_PASSWORD", "rustfsadmin"),
        "AWS_REGION": "us-east-1",
        "AWS_ALLOW_HTTP": "true",
        "AWS_S3_ALLOW_UNSAFE_RENAME": "true",
    }
    table_name = table_name.replace(" ", "_").replace("-", "_").lower()
    s3_path = f"s3://{bucket_name}/{table_name}"

    df.write_delta(
        target=s3_path,
        mode=mode,
        storage_options=storage_options,
        delta_write_options={"schema_mode": "overwrite"},
    )
