
import json
import shutil
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
import numpy as np
import tempfile
import re
from scipy.spatial.transform import Rotation as R

# -------------------------------------------------
# Canonical camera IDs (authoritative, ordered)
# -------------------------------------------------
# Must match ANY folder containing these substrings
CAMERA_SUBSTRING_RULES = [
    (["front_left"], "01_CAM_FRONT_LEFT"),
    (["front_right"], "03_CAM_FRONT_RIGHT"),
    (["front"], "02_CAM_FRONT"),
    (["rear_left", "back_left"], "06_CAM_BACK_LEFT"),
    (["rear_right", "back_right"], "04_CAM_BACK_RIGHT"),
    (["rear", "back"], "05_CAM_BACK"),
]

# Canonical NuScenes / CaliperGT output filenames
NUSCENES_CAMERA_OUTPUT = [
    ("CAM_FRONT_LEFT",  "01_CAM_FRONT_LEFT.jpg"),
    ("CAM_FRONT",       "02_CAM_FRONT.jpg"),
    ("CAM_FRONT_RIGHT", "03_CAM_FRONT_RIGHT.jpg"),
    ("CAM_BACK_RIGHT",  "04_CAM_BACK_RIGHT.jpg"),
    ("CAM_BACK",        "05_CAM_BACK.jpg"),
]

def rt_to_homogeneous(rotation, translation):
    """
    rotation: 3x3 list
    translation: length-3 list
    returns: 4x4 list
    """
    T = np.eye(4, dtype=float)
    T[:3, :3] = np.array(rotation, dtype=float)
    T[:3, 3] = np.array(translation, dtype=float)
    return T.tolist()

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

CAMERA_SUBSTRING_RULES = [
    (["front_left"], "01_CAM_FRONT_LEFT"),
    (["front_right"], "03_CAM_FRONT_RIGHT"),
    (["front"], "02_CAM_FRONT"),
    (["rear_left", "back_left"], "06_CAM_BACK_LEFT"),
    (["rear_right", "back_right"], "04_CAM_BACK_RIGHT"),
    (["rear", "back"], "05_CAM_BACK"),
]

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

def _match_camera_id(name: str) -> Optional[str]:
    lname = name.lower()
    lname = re.sub(r'_?cameras?_?', '', lname)
    for substrings, cid in CAMERA_SUBSTRING_RULES:
        if any(s in lname for s in substrings):
            return cid
    return None

def intrinsic_to_matrix(intrinsic: dict):
    K = np.array([
        [intrinsic["fx"], 0.0, intrinsic["cx"]],
        [0.0, intrinsic["fy"], intrinsic["cy"]],
        [0.0, 0.0, 1.0]
    ], dtype=float)

    return K

def transform_custom_to_expected(input_path: str, output_path: str) -> Tuple[bool, str]:
    input_path = Path(input_path)
    output_path = Path(output_path)

    pc_dir = output_path / "pointcloud"
    ri_dir = output_path / "related_images"
    cam_dir = output_path / "cameras"

    pc_dir.mkdir(parents=True, exist_ok=True)
    ri_dir.mkdir(parents=True, exist_ok=True)
    cam_dir.mkdir(parents=True, exist_ok=True)

    # Load calibration and poses
    calib = json.load(open(input_path / "calibration.json"))
    poses = json.load(open(input_path / "ego_poses/poses.json"))["frames"]

    # LiDAR calibration
    lidar_sensor_calib = invert_transform(
        calib["ego_to_lidar"]["rotation"],
        calib["ego_to_lidar"]["translation"]
    )

    # Camera calibrations using substring match (same logic as camera folders)
    camera_calibs = {}
    for cam_name, cam_data in calib.get("lidar_to_cameras", {}).items():
        cid = _match_camera_id(cam_name)
        if not cid:
            continue
        camera_calibs[cid] = {
            "transformation_matrix": rt_to_homogeneous(
                cam_data["extrinsic"]["rotation"],
                cam_data["extrinsic"]["translation"],
            ),
            "camera_intrinsic": intrinsic_to_matrix(cam_data["intrinsic"]).tolist()
        }

    lidar_files = sorted((input_path / "lidar").glob("*.pcd"))
    if not lidar_files:
        return False, "No LiDAR files found"

    # Load camera images strictly by index (same substring logic)
    camera_images = {}
    cameras_root = input_path / "cameras"

    for cam_folder in cameras_root.iterdir():
        if not cam_folder.is_dir():
            continue
        cid = _match_camera_id(cam_folder.name)
        if not cid:
            continue

        imgs = sorted(cam_folder.glob("*.jpg"))
        camera_images[cid] = imgs
        (cam_dir / cid).mkdir(exist_ok=True)

    # Process frames
    for idx, lidar in enumerate(lidar_files):
        ts_us = int(float(poses[idx]["timestamp"]) * 1_000_000)

        shutil.copy2(lidar, pc_dir / f"lidar__{ts_us}.pcd")

        frame_dir = ri_dir / f"lidar__{ts_us}_pcd"
        frame_dir.mkdir(exist_ok=True)

        frame_calib = {
            "LIDAR_TOP": {
                "sensor_calibration": lidar_sensor_calib,
            "ego_pose": {
                "rotation": poses[idx]["rotation"],
                "translation": poses[idx]["position"]
            }
            },
            "ego_pose": {
                "rotation": poses[idx]["rotation"],
                "translation": poses[idx]["position"]
            }}

        # Inject camera calibrations (matched names)
        for cid, cam_cal in camera_calibs.items():
            frame_calib[cid] = cam_cal

        with open(frame_dir / "sensor_calibrations.json", "w") as f:
            json.dump(frame_calib, f, indent=2)

        # Copy camera images by index
        for cid, imgs in camera_images.items():
            if idx < len(imgs):
                shutil.copy2(
                    imgs[idx],
                    cam_dir / cid / f"lidar__{ts_us}.jpg"
                )

    return True, f"Transformed {len(lidar_files)} frames"


def cleanup_transformed_data(path: str) -> None:
    if path.startswith(tempfile.gettempdir()):
        shutil.rmtree(path, ignore_errors=True)