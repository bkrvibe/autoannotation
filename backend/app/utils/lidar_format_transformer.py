
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

        # Debug logging
        try:
            subdirs = [d.name for d in current.iterdir() if d.is_dir()]
            files = [f.name for f in current.iterdir() if f.is_file()]
            print(f"[detect_format] Checking {current} (depth={depth})")
            print(f"  Subdirs: {subdirs[:10]}")
            print(f"  Files: {files[:10]}")
        except Exception as e:
            print(f"[detect_format] Error listing {current}: {e}")

        # --- Case 1: Already transformed (CaliperGT) ---
        if (
            (current / "pointcloud").is_dir()
            and (current / "related_images").is_dir()
        ):
            print(f"[detect_format] Found 'expected' format at {current}")
            return "expected", str(current)

        # --- Case 2: Custom raw format ---
        has_lidar = (current / "lidar").is_dir()
        has_calibration = (current / "calibration.json").exists() or (current / "calib.json").exists()

        # Check for poses in many different locations and names
        poses_locations = [
            current / "ego_poses" / "poses.json",
            current / "ego_poses" / "ego_poses.json",
            current / "poses.json",
            current / "ego_poses.json",
            current / "poses" / "poses.json",
            current / "ego_pose" / "poses.json",
        ]

        # Also check for any JSON file inside ego_poses directory
        ego_poses_dir = current / "ego_poses"
        if ego_poses_dir.is_dir():
            for json_file in ego_poses_dir.glob("*.json"):
                if json_file not in poses_locations:
                    poses_locations.append(json_file)

        found_poses_file = None
        for p in poses_locations:
            if p.exists():
                found_poses_file = p
                break

        has_poses = found_poses_file is not None

        if has_lidar and has_calibration and has_poses:
            print(f"[detect_format] Found 'custom' format at {current}")
            print(f"  Poses file: {found_poses_file}")
            return "custom", str(current)

        # --- Case 3: Has lidar but missing some files - report what's missing ---
        if has_lidar:
            pcd_files = list((current / "lidar").glob("*.pcd"))
            bin_files = list((current / "lidar").glob("*.bin"))
            print(f"[detect_format] Found lidar dir with {len(pcd_files)} .pcd files, {len(bin_files)} .bin files")

            if not has_calibration:
                print(f"  MISSING: calibration.json (checked: calibration.json, calib.json)")
            else:
                print(f"  FOUND: calibration file")

            if not has_poses:
                print(f"  MISSING: poses file (checked: {[str(p.relative_to(current)) for p in poses_locations[:4]]})")
                # List what's actually in ego_poses if it exists
                if ego_poses_dir.is_dir():
                    ego_contents = list(ego_poses_dir.iterdir())
                    print(f"  Contents of ego_poses/: {[f.name for f in ego_contents]}")
            else:
                print(f"  FOUND: poses file at {found_poses_file}")

        # Traverse children
        try:
            for child in current.iterdir():
                if child.is_dir():
                    queue.append((child, depth + 1))
        except PermissionError:
            pass

    print(f"[detect_format] No format detected, returning 'unknown'")
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

def find_poses_file(input_path: Path) -> Tuple[Optional[Path], Optional[list]]:
    """Find and load poses file from various possible locations."""
    poses_locations = [
        input_path / "ego_poses" / "poses.json",
        input_path / "ego_poses" / "ego_poses.json",  # Added this!
        input_path / "poses.json",
        input_path / "ego_poses.json",
        input_path / "poses" / "poses.json",
        input_path / "ego_pose" / "poses.json",
    ]

    for loc in poses_locations:
        if loc.exists():
            try:
                data = json.load(open(loc))
                # Handle different formats
                if isinstance(data, dict) and "frames" in data:
                    return loc, data["frames"]
                elif isinstance(data, list):
                    return loc, data
                elif isinstance(data, dict) and "poses" in data:
                    return loc, data["poses"]
            except Exception as e:
                print(f"Error loading {loc}: {e}")
                continue

    # Search for any JSON file that looks like poses
    for json_file in input_path.rglob("*.json"):
        if json_file.name.lower() in ['calibration.json', 'calib.json']:
            continue
        try:
            data = json.load(open(json_file))
            if isinstance(data, dict) and "frames" in data:
                print(f"Found poses in {json_file}")
                return json_file, data["frames"]
            elif isinstance(data, list) and len(data) > 0:
                first = data[0]
                if isinstance(first, dict) and any(k in first for k in ['position', 'translation', 'rotation', 'timestamp']):
                    print(f"Found poses list in {json_file}")
                    return json_file, data
        except:
            continue

    return None, None


def find_calibration_file(input_path: Path) -> Tuple[Optional[Path], Optional[dict]]:
    """Find and load calibration file from various possible locations."""
    calib_locations = [
        input_path / "calibration.json",
        input_path / "calib.json",
        input_path / "sensor_calibration.json",
        input_path / "calibrations.json",
    ]

    for loc in calib_locations:
        if loc.exists():
            try:
                data = json.load(open(loc))
                return loc, data
            except Exception as e:
                print(f"Error loading {loc}: {e}")
                continue

    # Search for any JSON file that looks like calibration
    for json_file in input_path.rglob("*.json"):
        try:
            data = json.load(open(json_file))
            if isinstance(data, dict) and any(k in data for k in ['ego_to_lidar', 'lidar_to_camera', 'extrinsic', 'intrinsic']):
                print(f"Found calibration in {json_file}")
                return json_file, data
        except:
            continue

    return None, None


def transform_custom_to_expected(input_path: str, output_path: str) -> Tuple[bool, str]:
    input_path = Path(input_path)
    output_path = Path(output_path)

    pc_dir = output_path / "pointcloud"
    ri_dir = output_path / "related_images"
    cam_dir = output_path / "cameras"

    pc_dir.mkdir(parents=True, exist_ok=True)
    ri_dir.mkdir(parents=True, exist_ok=True)
    cam_dir.mkdir(parents=True, exist_ok=True)

    # Find and load calibration
    calib_path, calib = find_calibration_file(input_path)
    if not calib:
        return False, "Could not find calibration file. Expected calibration.json with ego_to_lidar transform."

    print(f"Using calibration from: {calib_path}")

    # Find and load poses
    poses_path, poses = find_poses_file(input_path)
    if not poses:
        return False, "Could not find poses file. Expected ego_poses/poses.json or poses.json with frames array."

    print(f"Using poses from: {poses_path}, found {len(poses)} frames")

    # Normalize pose data to standard format
    def get_pose_field(pose: dict, field_names: list, default=None):
        """Get field from pose dict, trying multiple possible names."""
        for name in field_names:
            if name in pose:
                return pose[name]
        return default

    def normalize_pose(pose: dict, idx: int) -> dict:
        """Normalize pose to standard format with timestamp, rotation, position."""
        # Try different field names for timestamp
        ts = get_pose_field(pose, ['timestamp', 'time', 'ts', 't'])
        if ts is None:
            ts = idx  # Use index as fallback

        # Try different field names for position/translation
        pos = get_pose_field(pose, ['position', 'translation', 'trans', 'xyz', 'location'])
        if pos is None and 'transform' in pose:
            # Extract from transform matrix
            pos = [0, 0, 0]

        # Try different field names for rotation
        rot = get_pose_field(pose, ['rotation', 'quaternion', 'quat', 'orientation'])
        if rot is None and 'transform' in pose:
            rot = [1, 0, 0, 0]  # Identity quaternion

        return {
            'timestamp': ts,
            'position': pos if pos else [0, 0, 0],
            'rotation': rot if rot else [1, 0, 0, 0]
        }

    # Normalize all poses
    normalized_poses = [normalize_pose(p, i) for i, p in enumerate(poses)]

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
        if idx >= len(normalized_poses):
            print(f"Warning: More lidar files ({len(lidar_files)}) than poses ({len(normalized_poses)})")
            break

        pose = normalized_poses[idx]
        ts_us = int(float(pose["timestamp"]) * 1_000_000)

        shutil.copy2(lidar, pc_dir / f"lidar__{ts_us}.pcd")

        frame_dir = ri_dir / f"lidar__{ts_us}_pcd"
        frame_dir.mkdir(exist_ok=True)

        frame_calib = {
            "LIDAR_TOP": {
                "sensor_calibration": lidar_sensor_calib,
                "ego_pose": {
                    "rotation": pose["rotation"],
                    "translation": pose["position"]
                }
            },
            "ego_pose": {
                "rotation": pose["rotation"],
                "translation": pose["position"]
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