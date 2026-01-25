"""
Data Structure Validator for Auto-Annotation Platform.

Validates uploaded data against expected structures for 2D and 3D pipelines.
Provides detailed feedback to help users fix data structure issues.
"""

import os
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import json
import zipfile
import tempfile
import shutil


# Expected structure for 3D LiDAR data (CaliperGT format)
EXPECTED_3D_STRUCTURE = {
    "expected_format": {
        "pointcloud/": "Directory containing LiDAR point cloud files (.pcd)",
        "related_images/": "Directory containing camera images organized by frame",
    },
    "custom_format": {
        "lidar/": "Directory containing LiDAR .pcd files",
        "calibration.json": "Sensor calibration data",
        "ego_poses/poses.json": "Vehicle ego poses for each frame",
        "cameras/": "Optional: Camera images organized by view (front_left, front, etc.)",
    }
}

# Expected structure for 2D image data
EXPECTED_2D_STRUCTURE = {
    "images/": "Directory containing image files (.jpg, .png, .jpeg)",
    "or": "A flat folder with image files directly"
}

# Supported file extensions
SUPPORTED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp'}
SUPPORTED_POINTCLOUD_EXTENSIONS = {'.pcd', '.bin', '.ply'}
SUPPORTED_ARCHIVE_EXTENSIONS = {'.zip'}


class MissingFileInfo:
    """Information about a missing required file."""

    def __init__(self, file_type: str, expected_names: List[str], description: str, required: bool = True):
        self.file_type = file_type  # 'poses', 'calibration', etc.
        self.expected_names = expected_names  # Expected file names/paths
        self.description = description  # Human-readable description
        self.required = required  # Is this file required?
        self.user_provided_path: Optional[str] = None  # User can specify custom path

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_type": self.file_type,
            "expected_names": self.expected_names,
            "description": self.description,
            "required": self.required
        }


class DataValidationResult:
    """Result of data validation."""

    def __init__(self):
        self.is_valid: bool = False
        self.format_detected: str = "unknown"  # 'expected', 'custom', '2d', 'unknown'
        self.pipeline_type: str = "unknown"  # '2d' or '3d'
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.suggestions: List[str] = []
        self.structure_found: Dict[str, Any] = {}
        self.file_counts: Dict[str, int] = {}
        self.missing_files: List[MissingFileInfo] = []  # Files that need user input
        self.found_candidates: Dict[str, List[str]] = {}  # Potential matches for missing files

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "format_detected": self.format_detected,
            "pipeline_type": self.pipeline_type,
            "errors": self.errors,
            "warnings": self.warnings,
            "suggestions": self.suggestions,
            "structure_found": self.structure_found,
            "file_counts": self.file_counts,
            "missing_files": [mf.to_dict() for mf in self.missing_files],
            "found_candidates": self.found_candidates
        }


def validate_3d_expected_format(data_path: Path) -> DataValidationResult:
    """Validate data against CaliperGT expected format."""
    result = DataValidationResult()
    result.pipeline_type = "3d"

    pointcloud_dir = data_path / "pointcloud"
    related_images_dir = data_path / "related_images"

    # Check required directories
    if not pointcloud_dir.exists():
        result.errors.append("Missing 'pointcloud/' directory")
        result.suggestions.append("Create a 'pointcloud/' directory with your .pcd files")
    else:
        # Count point cloud files
        pcd_files = list(pointcloud_dir.glob("*.pcd"))
        bin_files = list(pointcloud_dir.glob("*.bin"))
        result.file_counts["pointcloud_files"] = len(pcd_files) + len(bin_files)
        result.structure_found["pointcloud"] = True

        if len(pcd_files) + len(bin_files) == 0:
            result.errors.append("No point cloud files found in 'pointcloud/' directory")
            result.suggestions.append("Add .pcd or .bin point cloud files to 'pointcloud/' directory")

    if not related_images_dir.exists():
        result.warnings.append("Missing 'related_images/' directory (optional for LiDAR-only)")
    else:
        result.structure_found["related_images"] = True
        # Count frame directories
        frame_dirs = [d for d in related_images_dir.iterdir() if d.is_dir()]
        result.file_counts["frame_directories"] = len(frame_dirs)

    # Check for calibration in related_images
    if related_images_dir.exists():
        frame_dirs = [d for d in related_images_dir.iterdir() if d.is_dir()]
        if frame_dirs:
            sample_frame = frame_dirs[0]
            calib_file = sample_frame / "sensor_calibrations.json"
            if not calib_file.exists():
                result.warnings.append("No sensor_calibrations.json found in frame directories")

    if not result.errors:
        result.is_valid = True
        result.format_detected = "expected"

    return result


def find_json_files_recursive(data_path: Path, max_depth: int = 3) -> List[Path]:
    """Find all JSON files in directory up to max_depth."""
    json_files = []
    queue = [(data_path, 0)]

    while queue:
        current, depth = queue.pop(0)
        if depth > max_depth:
            continue

        try:
            for item in current.iterdir():
                if item.is_file() and item.suffix.lower() == '.json':
                    json_files.append(item)
                elif item.is_dir() and depth < max_depth:
                    queue.append((item, depth + 1))
        except PermissionError:
            pass

    return json_files


def find_poses_candidates(data_path: Path) -> Tuple[Optional[Path], List[Path]]:
    """
    Find poses file - check known locations and search for candidates.
    Returns (found_path, candidate_paths)
    """
    # Known locations to check
    known_locations = [
        data_path / "ego_poses" / "poses.json",
        data_path / "poses.json",
        data_path / "ego_poses.json",
        data_path / "poses" / "poses.json",
        data_path / "ego_pose" / "poses.json",
        data_path / "pose" / "poses.json",
    ]

    for loc in known_locations:
        if loc.exists():
            return loc, []

    # Search for candidate files
    candidates = []
    json_files = find_json_files_recursive(data_path)

    for jf in json_files:
        name_lower = jf.name.lower()
        # Look for files with 'pose' in the name
        if 'pose' in name_lower or 'ego' in name_lower or 'trajectory' in name_lower:
            candidates.append(jf)

        # Also check content for pose-like structure
        try:
            with open(jf) as f:
                content = json.load(f)
            if isinstance(content, dict):
                if 'frames' in content or 'poses' in content or 'trajectory' in content:
                    if jf not in candidates:
                        candidates.append(jf)
            elif isinstance(content, list) and len(content) > 0:
                first = content[0]
                if isinstance(first, dict) and ('position' in first or 'translation' in first or 'rotation' in first):
                    if jf not in candidates:
                        candidates.append(jf)
        except:
            pass

    return None, candidates


def find_calibration_candidates(data_path: Path) -> Tuple[Optional[Path], List[Path]]:
    """
    Find calibration file - check known locations and search for candidates.
    Returns (found_path, candidate_paths)
    """
    known_locations = [
        data_path / "calibration.json",
        data_path / "calib.json",
        data_path / "sensor_calibration.json",
        data_path / "calibrations.json",
    ]

    for loc in known_locations:
        if loc.exists():
            return loc, []

    # Search for candidate files
    candidates = []
    json_files = find_json_files_recursive(data_path)

    for jf in json_files:
        name_lower = jf.name.lower()
        if 'calib' in name_lower or 'sensor' in name_lower or 'extrinsic' in name_lower or 'intrinsic' in name_lower:
            candidates.append(jf)

        # Check content for calibration-like structure
        try:
            with open(jf) as f:
                content = json.load(f)
            if isinstance(content, dict):
                if any(k in content for k in ['ego_to_lidar', 'lidar_to_camera', 'extrinsic', 'intrinsic', 'camera_matrix']):
                    if jf not in candidates:
                        candidates.append(jf)
        except:
            pass

    return None, candidates


def validate_3d_custom_format(data_path: Path) -> DataValidationResult:
    """Validate data against custom input format (will be transformed)."""
    result = DataValidationResult()
    result.pipeline_type = "3d"
    result.format_detected = "3d_incomplete"

    lidar_dir = data_path / "lidar"
    cameras_dir = data_path / "cameras"

    # Check for lidar directory
    if not lidar_dir.exists():
        result.errors.append("Missing 'lidar/' directory")
        result.missing_files.append(MissingFileInfo(
            file_type="lidar_directory",
            expected_names=["lidar/"],
            description="Directory containing LiDAR point cloud files (.pcd)",
            required=True
        ))
    else:
        pcd_files = list(lidar_dir.glob("*.pcd"))
        bin_files = list(lidar_dir.glob("*.bin"))
        total_pc = len(pcd_files) + len(bin_files)
        result.file_counts["lidar_files"] = total_pc
        result.structure_found["lidar"] = True

        if total_pc == 0:
            result.errors.append("No point cloud files (.pcd or .bin) found in 'lidar/' directory")

    # Check for calibration file
    calib_path, calib_candidates = find_calibration_candidates(data_path)

    if calib_path:
        result.structure_found["calibration"] = True
        result.structure_found["calibration_path"] = str(calib_path.relative_to(data_path))
        try:
            with open(calib_path) as f:
                calib_data = json.load(f)
            if "ego_to_lidar" not in calib_data:
                result.warnings.append("calibration.json missing 'ego_to_lidar' transform")
        except json.JSONDecodeError:
            result.errors.append(f"{calib_path.name} is not valid JSON")
    else:
        result.errors.append("Missing calibration file")
        if calib_candidates:
            result.found_candidates["calibration"] = [str(c.relative_to(data_path)) for c in calib_candidates]
            result.suggestions.append(
                f"Found potential calibration files: {', '.join(result.found_candidates['calibration'])}. "
                "Please confirm which one to use."
            )
        result.missing_files.append(MissingFileInfo(
            file_type="calibration",
            expected_names=["calibration.json", "calib.json", "sensor_calibration.json"],
            description="Sensor calibration data with ego_to_lidar and lidar_to_cameras transforms",
            required=True
        ))

    # Check for poses file
    poses_path, poses_candidates = find_poses_candidates(data_path)

    if poses_path:
        result.structure_found["ego_poses"] = True
        result.structure_found["poses_path"] = str(poses_path.relative_to(data_path))
        try:
            with open(poses_path) as f:
                poses_data = json.load(f)
            # Handle different pose formats
            if "frames" in poses_data:
                result.file_counts["pose_frames"] = len(poses_data["frames"])
            elif isinstance(poses_data, list):
                result.file_counts["pose_frames"] = len(poses_data)
            else:
                result.warnings.append("Pose file format not recognized, expected 'frames' array or list")
        except json.JSONDecodeError:
            result.errors.append(f"{poses_path.name} is not valid JSON")
    else:
        result.errors.append("Missing poses/ego_poses file")
        if poses_candidates:
            result.found_candidates["poses"] = [str(c.relative_to(data_path)) for c in poses_candidates]
            result.suggestions.append(
                f"Found potential pose files: {', '.join(result.found_candidates['poses'])}. "
                "Please confirm which one to use."
            )
        result.missing_files.append(MissingFileInfo(
            file_type="poses",
            expected_names=["ego_poses/poses.json", "poses.json", "ego_poses.json"],
            description="Vehicle ego poses with position and rotation for each frame",
            required=True
        ))

    # Optional: Check cameras
    if cameras_dir.exists():
        result.structure_found["cameras"] = True
        cam_subdirs = [d for d in cameras_dir.iterdir() if d.is_dir()]
        result.file_counts["camera_views"] = len(cam_subdirs)

    # Determine if valid
    if not result.errors:
        result.is_valid = True
        result.format_detected = "custom"
    elif result.structure_found.get("lidar") and (result.found_candidates.get("calibration") or result.found_candidates.get("poses")):
        # Partial - we found lidar and some candidates, user can help
        result.format_detected = "3d_needs_confirmation"

    return result


def validate_2d_format(data_path: Path) -> DataValidationResult:
    """Validate data for 2D image annotation pipelines."""
    result = DataValidationResult()
    result.pipeline_type = "2d"

    # Check for images directory or flat image files
    images_dir = data_path / "images"

    def count_images_in_dir(directory: Path) -> int:
        count = 0
        for ext in SUPPORTED_IMAGE_EXTENSIONS:
            count += len(list(directory.glob(f"*{ext}")))
            count += len(list(directory.glob(f"*{ext.upper()}")))
        return count

    if images_dir.exists():
        result.structure_found["images_directory"] = True
        img_count = count_images_in_dir(images_dir)
        result.file_counts["images"] = img_count

        if img_count == 0:
            result.errors.append("No image files found in 'images/' directory")
            result.suggestions.append(
                f"Add image files ({', '.join(SUPPORTED_IMAGE_EXTENSIONS)}) to 'images/' directory"
            )
    else:
        # Check for flat image files in root
        img_count = count_images_in_dir(data_path)
        result.file_counts["images"] = img_count

        if img_count > 0:
            result.structure_found["flat_images"] = True
        else:
            # Check subdirectories for images
            for subdir in data_path.iterdir():
                if subdir.is_dir():
                    sub_count = count_images_in_dir(subdir)
                    if sub_count > 0:
                        result.structure_found[f"images_in_{subdir.name}"] = True
                        result.file_counts["images"] = result.file_counts.get("images", 0) + sub_count

            if result.file_counts.get("images", 0) == 0:
                result.errors.append("No image files found")
                result.suggestions.append(
                    f"Add image files ({', '.join(SUPPORTED_IMAGE_EXTENSIONS)}) to your data folder"
                )

    if not result.errors:
        result.is_valid = True
        result.format_detected = "2d"

    return result


def detect_and_validate_data(
    data_path: str,
    pipeline_type: Optional[str] = None
) -> DataValidationResult:
    """
    Detect data format and validate against expected structure.

    Args:
        data_path: Path to the data directory
        pipeline_type: Optional pipeline type hint ('2d' or '3d')

    Returns:
        DataValidationResult with validation details
    """
    path = Path(data_path)

    if not path.exists():
        result = DataValidationResult()
        result.errors.append(f"Path does not exist: {data_path}")
        return result

    if not path.is_dir():
        result = DataValidationResult()
        result.errors.append(f"Path is not a directory: {data_path}")
        return result

    # List root contents for diagnostics
    root_contents = list(path.iterdir())

    # Detect format based on directory structure
    has_pointcloud = (path / "pointcloud").exists()
    has_related_images = (path / "related_images").exists()
    has_lidar = (path / "lidar").exists()
    has_calibration = (path / "calibration.json").exists()
    has_ego_poses = (path / "ego_poses" / "poses.json").exists()

    # 3D Expected Format (CaliperGT)
    if has_pointcloud and has_related_images:
        return validate_3d_expected_format(path)

    # 3D Custom Format (needs transformation)
    if has_lidar and has_calibration and has_ego_poses:
        return validate_3d_custom_format(path)

    # If pipeline type is specified as 3D, validate accordingly
    if pipeline_type == "3d" or pipeline_type == "auto_annotation_pipeline_dynamic":
        # Check which format is closer
        if has_pointcloud or has_lidar:
            if has_pointcloud:
                return validate_3d_expected_format(path)
            else:
                return validate_3d_custom_format(path)
        else:
            # Neither format detected
            result = DataValidationResult()
            result.pipeline_type = "3d"
            result.errors.append("Could not detect 3D data structure")
            result.suggestions.append(
                "For CaliperGT format: Create 'pointcloud/' and 'related_images/' directories"
            )
            result.suggestions.append(
                "For custom format: Create 'lidar/', 'calibration.json', and 'ego_poses/poses.json'"
            )
            return result

    # Default to 2D validation
    return validate_2d_format(path)


def validate_zip_structure(zip_path: str, pipeline_type: Optional[str] = None) -> DataValidationResult:
    """Validate the structure inside a zip file without fully extracting."""
    result = DataValidationResult()

    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            namelist = zf.namelist()

            # Analyze structure
            has_pointcloud = any('/pointcloud/' in n or n.startswith('pointcloud/') for n in namelist)
            has_related_images = any('/related_images/' in n or n.startswith('related_images/') for n in namelist)
            has_lidar = any('/lidar/' in n or n.startswith('lidar/') for n in namelist)
            has_calibration = any(n.endswith('calibration.json') for n in namelist)

            # Count files by type
            image_count = sum(1 for n in namelist if any(n.lower().endswith(ext) for ext in SUPPORTED_IMAGE_EXTENSIONS))
            pcd_count = sum(1 for n in namelist if n.lower().endswith('.pcd'))

            result.file_counts["images"] = image_count
            result.file_counts["pointcloud_files"] = pcd_count

            if has_pointcloud and has_related_images:
                result.format_detected = "expected"
                result.pipeline_type = "3d"
                result.is_valid = True
            elif has_lidar and has_calibration:
                result.format_detected = "custom"
                result.pipeline_type = "3d"
                result.is_valid = True
            elif image_count > 0:
                result.format_detected = "2d"
                result.pipeline_type = "2d"
                result.is_valid = True
            else:
                result.errors.append("Could not detect valid data structure in zip file")

    except zipfile.BadZipFile:
        result.errors.append("Invalid zip file")
    except Exception as e:
        result.errors.append(f"Error reading zip file: {str(e)}")

    return result


def get_structure_help_message(pipeline_type: str) -> Dict[str, Any]:
    """Get help message for expected data structure."""
    if pipeline_type == "3d" or pipeline_type == "auto_annotation_pipeline_dynamic":
        return {
            "pipeline": "3D Object Detection & Tracking",
            "formats": {
                "CaliperGT Format (Ready to Use)": {
                    "structure": [
                        "data/",
                        "  pointcloud/",
                        "    lidar__1234567890.pcd",
                        "    lidar__1234567891.pcd",
                        "    ...",
                        "  related_images/",
                        "    lidar__1234567890_pcd/",
                        "      sensor_calibrations.json",
                        "      01_CAM_FRONT_LEFT.jpg",
                        "      02_CAM_FRONT.jpg",
                        "      ...",
                    ],
                    "description": "Data already processed for annotation pipeline"
                },
                "Custom Format (Auto-Transformed)": {
                    "structure": [
                        "data/",
                        "  lidar/",
                        "    000000.pcd",
                        "    000001.pcd",
                        "    ...",
                        "  calibration.json",
                        "  ego_poses/",
                        "    poses.json",
                        "  cameras/  (optional)",
                        "    front_left/",
                        "    front/",
                        "    ...",
                    ],
                    "description": "Raw sensor data that will be automatically transformed"
                }
            }
        }
    else:
        return {
            "pipeline": "2D Image Annotation",
            "formats": {
                "Standard Format": {
                    "structure": [
                        "data/",
                        "  images/",
                        "    image001.jpg",
                        "    image002.jpg",
                        "    ...",
                    ],
                    "description": "Images in a single directory"
                },
                "Flat Format": {
                    "structure": [
                        "data/",
                        "  image001.jpg",
                        "  image002.jpg",
                        "  ...",
                    ],
                    "description": "Images directly in root folder"
                }
            },
            "supported_formats": list(SUPPORTED_IMAGE_EXTENSIONS)
        }
