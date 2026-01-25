"""
LiDAR Data Preprocessing for 3D Auto-Labeling

Handles format detection and transformation for 3D auto-labeling pipelines.
"""

import os
import tempfile
import shutil
from pathlib import Path
from typing import Tuple, Optional
from google.cloud import storage

from app.utils.lidar_format_transformer import (
    detect_format,
    transform_custom_to_expected,
    normalize_dataset_root,
    cleanup_transformed_data
)


def analyze_unknown_format(data_path: str) -> str:
    """
    Analyze why format detection failed and return helpful error message.
    """
    path = Path(data_path)
    issues = []
    found = []

    # Check for lidar directory
    lidar_dir = path / "lidar"
    pointcloud_dir = path / "pointcloud"

    if lidar_dir.is_dir():
        pcd_count = len(list(lidar_dir.glob("*.pcd")))
        bin_count = len(list(lidar_dir.glob("*.bin")))
        found.append(f"lidar/ directory ({pcd_count} .pcd, {bin_count} .bin files)")
    elif pointcloud_dir.is_dir():
        pcd_count = len(list(pointcloud_dir.glob("*.pcd")))
        found.append(f"pointcloud/ directory ({pcd_count} .pcd files)")
    else:
        issues.append("Missing 'lidar/' or 'pointcloud/' directory with point cloud files (.pcd or .bin)")

    # Check for calibration
    calib_file = path / "calibration.json"
    calib_alt = path / "calib.json"
    if calib_file.exists():
        found.append("calibration.json")
    elif calib_alt.exists():
        found.append("calib.json")
    else:
        # Search for any calibration-like file
        calib_candidates = list(path.glob("*calib*.json"))
        if calib_candidates:
            issues.append(f"Missing 'calibration.json'. Found similar: {[f.name for f in calib_candidates]}")
        else:
            issues.append("Missing 'calibration.json' with sensor calibration data")

    # Check for poses
    poses_locations = [
        path / "ego_poses" / "poses.json",
        path / "poses.json",
        path / "ego_poses.json",
    ]

    poses_found = False
    for loc in poses_locations:
        if loc.exists():
            found.append(str(loc.relative_to(path)))
            poses_found = True
            break

    if not poses_found:
        ego_poses_dir = path / "ego_poses"
        if ego_poses_dir.is_dir():
            contents = list(ego_poses_dir.iterdir())
            if contents:
                issues.append(f"Missing 'ego_poses/poses.json'. Found in ego_poses/: {[f.name for f in contents[:5]]}")
            else:
                issues.append("ego_poses/ directory is empty - needs poses.json with vehicle pose data")
        else:
            issues.append("Missing 'ego_poses/poses.json' with vehicle pose data (position/rotation per frame)")

    # Build message
    msg_parts = []
    if found:
        msg_parts.append(f"Found: {', '.join(found)}.")
    if issues:
        msg_parts.append("Missing: " + "; ".join(issues))

    # Add expected format hint
    msg_parts.append(
        "Expected structure: lidar/ (with .pcd files), calibration.json, ego_poses/poses.json"
    )

    return " ".join(msg_parts)


def download_from_gcs(gcs_path: str, local_path: str) -> bool:
    """
    Download data from GCS to local path.

    Args:
        gcs_path: GCS path (gs://bucket/path/to/data)
        local_path: Local directory path

    Returns:
        True if successful, False otherwise
    """
    try:
        # Parse GCS path
        if not gcs_path.startswith('gs://'):
            return False

        path_parts = gcs_path[5:].split('/', 1)
        bucket_name = path_parts[0]
        prefix = path_parts[1] if len(path_parts) > 1 else ''

        # Remove trailing slash from prefix
        prefix = prefix.rstrip('/')

        # Initialize GCS client
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)

        # List all blobs with the prefix
        blobs = list(bucket.list_blobs(prefix=prefix))

        if not blobs:
            print(f"No files found at {gcs_path}")
            return False

        # Download all files
        downloaded_count = 0
        for blob in blobs:
            # Get relative path
            rel_path = blob.name[len(prefix):].lstrip('/')

            # If rel_path is empty, this might be a single file
            # Use the blob's basename as the filename
            if not rel_path:
                rel_path = os.path.basename(blob.name)

            if not rel_path:  # Still empty? Skip
                continue

            # Create local file path
            local_file_path = os.path.join(local_path, rel_path)

            # Create parent directories
            os.makedirs(os.path.dirname(local_file_path), exist_ok=True)

            # Download file
            blob.download_to_filename(local_file_path)
            downloaded_count += 1

        print(f"Downloaded {downloaded_count} file(s) from {gcs_path} to {local_path}")
        return downloaded_count > 0

    except Exception as e:
        print(f"Error downloading from GCS: {e}")
        return False


def upload_to_gcs(local_path: str, gcs_bucket: str, gcs_prefix: str) -> Optional[str]:
    """
    Upload directory to GCS.

    Args:
        local_path: Local directory path
        gcs_bucket: GCS bucket name
        gcs_prefix: GCS prefix/path

    Returns:
        Full GCS path if successful, None otherwise
    """
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(gcs_bucket)

        # Remove trailing slash
        gcs_prefix = gcs_prefix.rstrip('/')

        # Upload all files
        local_path = Path(local_path)
        uploaded_count = 0

        for file_path in local_path.rglob('*'):
            if file_path.is_file():
                # Get relative path
                rel_path = file_path.relative_to(local_path)

                # Create GCS blob path
                blob_name = f"{gcs_prefix}/{rel_path}"

                # Upload file
                blob = bucket.blob(blob_name)
                blob.upload_from_filename(str(file_path))
                uploaded_count += 1

        gcs_path = f"gs://{gcs_bucket}/{gcs_prefix}"
        print(f"Uploaded {uploaded_count} files to {gcs_path}")
        return gcs_path

    except Exception as e:
        print(f"Error uploading to GCS: {e}")
        return None


def find_data_directory(root_path: Path, max_depth: int = 5) -> Optional[Path]:
    """
    Recursively search for the actual data directory.
    Looks for directories containing 'lidar', 'pointcloud', or expected data files.

    Args:
        root_path: Root path to search from
        max_depth: Maximum depth to search

    Returns:
        Path to data directory or None
    """
    from collections import deque

    queue = deque([(root_path, 0)])

    while queue:
        current, depth = queue.popleft()

        if depth > max_depth:
            continue

        try:
            subdirs = [d.name.lower() for d in current.iterdir() if d.is_dir()]
            files = [f.name.lower() for f in current.iterdir() if f.is_file()]
        except PermissionError:
            continue

        print(f"[find_data_directory] Checking {current} (depth={depth})")
        print(f"  Subdirs: {subdirs[:5]}, Files: {files[:5]}")

        # Check for CaliperGT format (expected)
        if 'pointcloud' in subdirs and 'related_images' in subdirs:
            print(f"[find_data_directory] Found CaliperGT format at {current}")
            return current

        # Check for custom format
        if 'lidar' in subdirs:
            # Check if calibration and poses exist
            has_calibration = 'calibration.json' in files
            has_poses = (
                'poses.json' in files or
                'ego_poses.json' in files or
                'ego_poses' in subdirs
            )
            if has_calibration or has_poses:
                print(f"[find_data_directory] Found custom format at {current}")
                return current
            # Even just lidar folder is a candidate
            print(f"[find_data_directory] Found lidar folder at {current}")
            return current

        # Add subdirectories to queue
        for subdir in current.iterdir():
            if subdir.is_dir():
                queue.append((subdir, depth + 1))

    print(f"[find_data_directory] No data directory found")
    return None


def extract_zip_if_needed(directory: str) -> Tuple[str, bool]:
    """
    Check if directory contains a single zip file and extract it.

    Args:
        directory: Directory path to check

    Returns:
        Tuple of (path_to_check, was_extracted)
    """
    import zipfile

    dir_path = Path(directory)
    files = list(dir_path.iterdir())

    # Check if there's exactly one file and it's a zip
    if len(files) == 1 and files[0].is_file() and files[0].suffix.lower() == '.zip':
        zip_file = files[0]
        extract_dir = dir_path / 'extracted'
        extract_dir.mkdir(exist_ok=True)

        print(f"Extracting zip file: {zip_file.name}")

        try:
            with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)

            # Try to find the actual data directory
            data_dir = find_data_directory(extract_dir)

            if data_dir:
                print(f"Found data directory: {data_dir}")
                return str(data_dir), True
            else:
                # Fall back to the extraction directory
                print(f"Could not find specific data directory, using extraction root")
                return str(extract_dir), True

        except Exception as e:
            print(f"Failed to extract zip: {e}")
            return directory, False

    return directory, False


def preprocess_3d_data(
    input_gcs_path: str,
    tenant_id: str,
    job_id: Optional[int] = None
) -> Tuple[str, bool, str]:
    """
    Preprocess 3D LiDAR data by detecting format and transforming if needed.

    Args:
        input_gcs_path: Input GCS path (gs://bucket/path/to/data)
        tenant_id: Tenant ID for organizing output
        job_id: Optional job ID for unique output path

    Returns:
        Tuple of (output_gcs_path, was_transformed, message)
    """
    temp_download_dir = None
    temp_transform_dir = None

    try:
        # Create temporary directories
        temp_download_dir = tempfile.mkdtemp(prefix='lidar_download_')

        print(f"Downloading data from {input_gcs_path}...")

        # Download data from GCS
        if not download_from_gcs(input_gcs_path, temp_download_dir):
            return input_gcs_path, False, "Failed to download data from GCS"

        # Debug: Check what was downloaded
        download_contents = list(Path(temp_download_dir).iterdir())
        print(f"Download directory contains {len(download_contents)} item(s): {[f.name for f in download_contents]}")

        # Check if we downloaded a zip file and extract it
        data_dir, was_extracted = extract_zip_if_needed(temp_download_dir)
        if was_extracted:
            print(f"✓ Extracted zip file, checking format in: {data_dir}")
        else:
            print(f"No zip extraction needed, using: {data_dir}")
            data_dir = temp_download_dir

        # Detect format
        format_type, data_root = detect_format(data_dir)
        print(f"Detected format: {format_type}, data_root: {data_root}")

        # Debug: List what's in the directory
        try:
            import os
            contents = os.listdir(data_dir)
            print(f"Directory contents at {data_dir}: {contents}")
        except Exception as e:
            print(f"Could not list directory: {e}")

        if format_type == 'unknown':
            print(f"Check removing redundant folders: {data_root}")
            # Normalize structure (remove redundant folders)
            if data_root:
                normalized_root = normalize_dataset_root(data_dir, data_root)
            else:
                normalized_root = data_dir
            print(f"Normalized root: {normalized_root}")
            # Re-detect (now guaranteed flat)
            format_type, data_root = detect_format(normalized_root)
            print(f"Format after removing redundant folders: {format_type}")
            if format_type != 'unknown':
                data_dir = data_root if data_root else normalized_root
        if format_type == 'expected':
            # Already in correct format, but if we extracted from zip, we need to upload
            if was_extracted:
                # Need to upload the extracted data
                if not input_gcs_path.startswith('gs://'):
                    return input_gcs_path, False, "Invalid GCS path"

                path_parts = input_gcs_path[5:].split('/', 1)
                bucket_name = path_parts[0]

                import time
                timestamp = int(time.time())
                job_suffix = f"_job{job_id}" if job_id else ""
                output_prefix = f"tenants/{tenant_id}/extracted/lidar_{timestamp}{job_suffix}"

                print(f"Uploading extracted data to GCS...")
                output_gcs_path = upload_to_gcs(
                    data_dir,
                    bucket_name,
                    output_prefix
                )

                if not output_gcs_path:
                    return input_gcs_path, False, "Failed to upload extracted data to GCS"

                return output_gcs_path, True, "Extracted zip and uploaded data in expected format"
            else:
                return input_gcs_path, False, "Data already in expected format"

        elif format_type == 'custom':
            # Need to transform
            temp_transform_dir = tempfile.mkdtemp(prefix='lidar_transform_')

            print(f"Transforming data format...")
            success, message = transform_custom_to_expected(
                data_dir,
                temp_transform_dir
            )

            if not success:
                return input_gcs_path, False, f"Transformation failed: {message}"

            # Upload transformed data back to GCS
            # Parse original GCS path to get bucket
            if not input_gcs_path.startswith('gs://'):
                return input_gcs_path, False, "Invalid GCS path"

            path_parts = input_gcs_path[5:].split('/', 1)
            bucket_name = path_parts[0]

            # Create unique output path
            import time
            timestamp = int(time.time())
            job_suffix = f"_job{job_id}" if job_id else ""
            output_prefix = f"tenants/{tenant_id}/transformed/lidar_{timestamp}{job_suffix}"

            print(f"Uploading transformed data to GCS...")
            output_gcs_path = upload_to_gcs(
                temp_transform_dir,
                bucket_name,
                output_prefix
            )

            if not output_gcs_path:
                return input_gcs_path, False, "Failed to upload transformed data to GCS"

            return output_gcs_path, True, f"Successfully transformed and uploaded data. {message}"

        else:
            # Unknown format - FAIL with detailed error message
            error_details = analyze_unknown_format(data_dir)
            error_msg = f"Invalid data format. {error_details}"
            print(f"ERROR: {error_msg}")
            raise ValueError(error_msg)

    except Exception as e:
        print(f"Error in preprocess_3d_data: {e}")
        import traceback
        traceback.print_exc()
        return input_gcs_path, False, f"Preprocessing error: {str(e)}"

    finally:
        # Clean up temporary directories
        if temp_download_dir:
            shutil.rmtree(temp_download_dir, ignore_errors=True)
        if temp_transform_dir:
            shutil.rmtree(temp_transform_dir, ignore_errors=True)
