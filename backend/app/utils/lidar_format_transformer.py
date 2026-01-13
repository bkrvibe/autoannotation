
import json
import shutil
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
import numpy as np
import tempfile
from scipy.spatial.transform import Rotation as R

# -------------------------------------------------
# Camera substring rules (authoritative)
# -------------------------------------------------
# Must match ANY folder containing these substrings
CAMERA_SUBSTRING_RULES = [
    (["front_left"], "CAM_FRONT_LEFT"),
    (["front_right"], "CAM_FRONT_RIGHT"),
    (["front"], "CAM_FRONT"),
    (["rear_left", "back_left"], "CAM_BACK_LEFT"),
    (["rear_right", "back_right"], "CAM_BACK_RIGHT"),
    (["rear", "back"], "CAM_BACK"),
]

# Canonical NuScenes / CaliperGT output filenames
NUSCENES_CAMERA_OUTPUT = [
    ("CAM_FRONT_LEFT",  "01_CAM_FRONT_LEFT.jpg"),
    ("CAM_FRONT",       "02_CAM_FRONT.jpg"),
    ("CAM_FRONT_RIGHT", "03_CAM_FRONT_RIGHT.jpg"),
    ("CAM_BACK_RIGHT",  "04_CAM_BACK_RIGHT.jpg"),
    ("CAM_BACK",        "05_CAM_BACK.jpg"),
]


def normalize_dataset_root(input_path: str, detected_root: str) -> str:
    """
    If the detected dataset root is nested inside input_path,
    flatten it so downstream always sees a clean structure.

    Returns:
        Path to normalized dataset root
    """
    input_path = Path(input_path).resolve()
    detected_root = Path(detected_root).resolve()

    # Already clean
    if detected_root == input_path:
        return str(input_path)

    # Move detected_root contents into input_path
    temp_backup = input_path / "__backup__"
    temp_backup.mkdir(exist_ok=True)

    # Move everything in input_path to backup
    for item in input_path.iterdir():
        if item.name != "__backup__":
            shutil.move(str(item), temp_backup / item.name)

    # Move detected_root contents to input_path
    for item in detected_root.iterdir():
        shutil.move(str(item), input_path / item.name)

    # Cleanup backup
    shutil.rmtree(temp_backup, ignore_errors=True)

    return str(input_path)


def detect_format(data_path: str, max_depth: int = 3) -> Tuple[str, Optional[str]]:
    """
    Recursively detect input data format.

    Returns:
        (format, root_path)

        format:
          - 'expected' : CaliperGT-ready format
          - 'custom'   : raw input format (needs transform)
          - 'unknown'  : unsupported

        root_path:
          - path to the directory that actually matches the format
          - None if unknown
    """
    base = Path(data_path).resolve()

    # BFS traversal up to max_depth
    queue = [(base, 0)]

    while queue:
        current, depth = queue.pop(0)
        if depth > max_depth:
            continue

        # --- Case 1: Already transformed (CaliperGT) ---
        if (
            (current / "pointcloud").is_dir()
            and (current / "related_images").is_dir()
        ):
            return "expected", str(current)

        # --- Case 2: Custom raw format ---
        if (
            (current / "lidar").is_dir()
            and (current / "ego_poses" / "poses.json").exists()
            and (current / "calibration.json").exists()
        ):
            return "custom", str(current)

        # Traverse children
        try:
            for child in current.iterdir():
                if child.is_dir():
                    queue.append((child, depth + 1))
        except PermissionError:
            pass

    return "unknown", None


def identity_calibration() -> Dict[str, Any]:
    return {
        "rotation": [1.0, 0.0, 0.0, 0.0],
        "translation": [0.0, 0.0, 0.0]
    }

def invert_transform(rotation_matrix, translation):
    Rm = np.array(rotation_matrix)
    t = np.array(translation)
    R_inv = Rm.T
    t_inv = -R_inv @ t
    quat = R.from_matrix(R_inv).as_quat()  # x,y,z,w
    return {
        "rotation": [quat[3], quat[0], quat[1], quat[2]],
        "translation": t_inv.tolist()
    }

def create_sensor_calibrations(ego_pose, sensor_calibration):
    return {
        "LIDAR_TOP": {
            "sensor_calibration": sensor_calibration,
            "ego_pose": ego_pose
        },
        "ego_pose": ego_pose
    }

def find_closest_image(ts_us: int, image_paths):
    best = None
    best_dt = float("inf")
    for p in image_paths:
        try:
            img_ts = int(p.stem)
        except ValueError:
            continue
        dt = abs(img_ts - ts_us)
        if dt < best_dt:
            best_dt = dt
            best = p
    return best

def normalize_camera_folders(cameras_root: Path):
    camera_images = {}

    for cam_dir in cameras_root.iterdir():
        if not cam_dir.is_dir():
            continue

        name = cam_dir.name.lower()

        cam_id = None
        for substrings, cid in CAMERA_SUBSTRING_RULES:
            if any(s in name for s in substrings):
                cam_id = cid
                break

        if not cam_id:
            continue

        images = sorted(
            list(cam_dir.glob("*.jpg")) + list(cam_dir.glob("*.png"))
        )

        if images:
            camera_images.setdefault(cam_id, []).extend(images)

    # sort images per camera by timestamp
    for cam_id in camera_images:
        camera_images[cam_id] = sorted(
            camera_images[cam_id],
            key=lambda p: int(p.stem)
        )

    return camera_images

def transform_custom_to_expected(input_path: str, output_path: str) -> Tuple[bool, str]:
    input_path = Path(input_path)
    output_path = Path(output_path)

    pc_dir = output_path / "pointcloud"
    ri_dir = output_path / "related_images"
    pc_dir.mkdir(parents=True, exist_ok=True)
    ri_dir.mkdir(parents=True, exist_ok=True)

    calib = json.load(open(input_path / "calibration.json"))
    sensor_calib = invert_transform(
        calib["ego_to_lidar"]["rotation"],
        calib["ego_to_lidar"]["translation"]
    )

    poses = json.load(open(input_path / "ego_poses/poses.json"))["frames"]

    camera_images = normalize_camera_folders(input_path / "cameras")

    lidar_files = sorted((input_path / "lidar").glob("*.pcd"))
    if not lidar_files:
        return False, "No LiDAR files found"

    for idx, lidar in enumerate(lidar_files):
        ts_us = int(float(poses[idx]["timestamp"]) * 1_000_000)
        ego_pose = {
            "rotation": poses[idx]["rotation"],
            "translation": poses[idx]["position"]
        }

        shutil.copy2(lidar, pc_dir / f"lidar__{ts_us}.pcd")

        frame_dir = ri_dir / f"lidar__{ts_us}_pcd"
        frame_dir.mkdir(exist_ok=True)

        for cam_key, out_name in NUSCENES_CAMERA_OUTPUT:
            imgs = camera_images.get(cam_key)
            if not imgs:
                continue
            img = find_closest_image(ts_us, imgs)
            if img:
                shutil.copy2(img, frame_dir / out_name)

        with open(frame_dir / "sensor_calibrations.json", "w") as f:
            json.dump(
                create_sensor_calibrations(ego_pose, sensor_calib),
                f,
                indent=2
            )

    return True, f"Transformed {len(lidar_files)} frames"

def cleanup_transformed_data(path: str) -> None: 
    """Clean up transformed data directory if it's a temp directory.""" 
    if path.startswith(tempfile.gettempdir()): 
        shutil.rmtree(path, ignore_errors=True)