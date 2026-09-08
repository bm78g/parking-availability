#!/usr/bin/env python3
"""
Uploads the most recent calibrated parking spot bounds JSON to DynamoDB.

Usage:
    python upload_bounds.py [--folder <path_to_bounds_folder>] [--table-name <name>] [--dry-run]

Conventions:
    - By default, the DynamoDB table name is inferred from the parent folder (e.g., sample/ -> 'sample').
    - Automatically finds and uploads the highest/latest version file (e.g., 0002.json over 0000.json).
    - Uses put_item under partition key 'camera_id', replacing any pre-existing data in that table.
"""

import argparse
from datetime import datetime, timezone
from decimal import Decimal
import json
import os
from pathlib import Path
import sys


def get_latest_bounds_file(folder: Path) -> Path:
    """Finds the most recent bounds JSON file in the given folder."""
    if not folder.exists():
        raise FileNotFoundError(f"Bounds directory not found: {folder}")
    if not folder.is_dir():
        raise NotADirectoryError(f"Provided path is not a directory: {folder}")

    json_files = [f for f in folder.glob("*.json") if f.is_file()]
    if not json_files:
        raise FileNotFoundError(f"No .json files found in directory: {folder}")

    # Sort numerically by stem if digits (e.g. 0000, 0001, 0002), otherwise alphabetically
    def sort_key(f: Path):
        stem = f.stem
        return (0, int(stem)) if stem.isdigit() else (1, f.name)

    json_files.sort(key=sort_key)
    return json_files[-1]


def load_and_validate_bounds(file_path: Path) -> list:
    """Loads and validates the parking spot bounds from a JSON file."""
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f, parse_float=Decimal)

    if not isinstance(data, list):
        raise ValueError(
            f"Expected JSON file to contain a list of spot objects, got {type(data).__name__}"
        )

    if not data:
        raise ValueError(f"Bounds file {file_path} contains an empty list.")

    for idx, spot in enumerate(data):
        if not isinstance(spot, dict):
            raise ValueError(f"Spot at index {idx} is not an object: {spot}")
        if "id" not in spot:
            raise ValueError(f"Spot at index {idx} missing 'id': {spot}")
        if "vertices" not in spot:
            raise ValueError(f"Spot at index {idx} missing 'vertices': {spot}")
        if "center" not in spot:
            raise ValueError(f"Spot at index {idx} missing 'center': {spot}")

    return data


def upload_bounds(
    folder_path: Path,
    table_name: str = None,
    camera_id: str = None,
    region: str = "us-east-1",
    dry_run: bool = False,
) -> dict:
    """Discovers the latest bounds file, derives the table name, and uploads to DynamoDB."""
    resolved_folder = folder_path.resolve()
    latest_file = get_latest_bounds_file(resolved_folder)
    parent_folder_name = resolved_folder.name

    # Inferred defaults based on parent folder
    target_table = table_name or parent_folder_name
    target_camera_id = camera_id or parent_folder_name

    print(f"Directory:    {resolved_folder}")
    print(f"Parent Name:  {parent_folder_name}")
    print(f"Latest File:  {latest_file.name} ({latest_file})")
    print(f"Target Table: {target_table}")
    print(f"Camera ID:    {target_camera_id}")

    spots = load_and_validate_bounds(latest_file)
    print(f"Loaded {len(spots)} valid parking spot definitions.")

    item = {
        "camera_id": target_camera_id,
        "spots": spots,
        "source_file": latest_file.name,
        "total_spots": len(spots),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    if dry_run:
        print("[DRY-RUN] Validation passed. Skipping write to DynamoDB.")
        return item

    try:
        import boto3
        from botocore.exceptions import ClientError
    except ImportError:
        print(
            "Error: 'boto3' is required to upload to DynamoDB. Install it via 'pip install boto3'.",
            file=sys.stderr,
        )
        sys.exit(1)

    dynamodb = boto3.resource("dynamodb", region_name=region)
    table = dynamodb.Table(target_table)

    try:
        print(f"Uploading item to DynamoDB table '{target_table}'...")
        table.put_item(Item=item)
        print(
            f"Successfully saved {len(spots)} spots from '{latest_file.name}' "
            f"into table '{target_table}' (camera_id='{target_camera_id}')."
        )
        print("Existing data in the table was replaced.")
    except ClientError as e:
        print(f"AWS ClientError uploading to DynamoDB: {e.response['Error']['Message']}", file=sys.stderr)
        raise

    return item


def main():
    default_folder = (
        Path(__file__).resolve().parent.parent / "data" / "bounds" / "sample"
    )
    default_region = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")

    parser = argparse.ArgumentParser(
        description="Upload latest calibrated spot bounds to DynamoDB."
    )
    parser.add_argument(
        "--folder",
        "-f",
        type=Path,
        default=default_folder,
        help=f"Path to bounds folder (default: {default_folder})",
    )
    parser.add_argument(
        "--table-name",
        "-t",
        type=str,
        default=None,
        help="Target DynamoDB table name (defaults to folder basename)",
    )
    parser.add_argument(
        "--camera-id",
        "-c",
        type=str,
        default=None,
        help="Camera ID partition key (defaults to folder basename)",
    )
    parser.add_argument(
        "--region",
        "-r",
        type=str,
        default=default_region,
        help=f"AWS Region (default: {default_region})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate directory and JSON files without writing to DynamoDB",
    )

    args = parser.parse_args()

    try:
        upload_bounds(
            folder_path=args.folder,
            table_name=args.table_name,
            camera_id=args.camera_id,
            region=args.region,
            dry_run=args.dry_run,
        )
    except Exception as err:
        print(f"Error: {err}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
