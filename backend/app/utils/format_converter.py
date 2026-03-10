"""
Format converter utilities for annotation data.
Converts between CaliperGT, COCO, and KITTI 3D formats.
"""
import io
import json
import math
import zipfile
from collections import defaultdict
from typing import Dict, List, Any, Tuple
from datetime import datetime


def calipergt_to_coco(calipergt_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert CaliperGT format annotations to COCO format.
    
    CaliperGT format has:
    - categories.label.labels: list of label definitions
    - items: list of images/frames with annotations
    
    COCO format has:
    - info: dataset metadata
    - images: list of image info
    - annotations: flat list of all annotations
    - categories: list of category definitions
    """
    
    # Initialize COCO structure
    coco_data = {
        "info": {
            "description": "Auto-annotated dataset converted from CaliperGT format",
            "url": "",
            "version": "1.0",
            "year": datetime.now().year,
            "contributor": "CaliperAI AutoAnnotation",
            "date_created": datetime.now().isoformat()
        },
        "licenses": [],
        "images": [],
        "annotations": [],
        "categories": []
    }
    
    # Extract categories from CaliperGT
    if "categories" in calipergt_data and "label" in calipergt_data["categories"]:
        labels = calipergt_data["categories"]["label"].get("labels", [])
        for idx, label in enumerate(labels):
            coco_data["categories"].append({
                "id": idx + 1,  # COCO category IDs start from 1
                "name": label.get("name", f"category_{idx}"),
                "supercategory": label.get("parent", "")
            })
    
    # Create label name to category ID mapping
    label_name_to_id = {cat["name"]: cat["id"] for cat in coco_data["categories"]}
    
    # Process items (images/frames)
    annotation_id = 1
    items = calipergt_data.get("items", [])
    
    for image_idx, item in enumerate(items):
        image_id = image_idx + 1
        
        # Extract image info
        image_info = {
            "id": image_id,
            "file_name": item.get("id", f"image_{image_id}"),
            "width": item.get("width", 1920),  # Default if not specified
            "height": item.get("height", 1080),  # Default if not specified
        }
        coco_data["images"].append(image_info)
        
        # Process annotations for this image
        annotations = item.get("annotations", [])
        for ann in annotations:
            ann_type = ann.get("type", "")
            
            # Handle bounding boxes
            if ann_type == "bbox" and "bbox" in ann:
                bbox = ann["bbox"]  # [x, y, width, height] in CaliperGT
                
                # Get category from label_id
                label_id = ann.get("label_id", 0)
                category_name = None
                if label_id < len(coco_data["categories"]):
                    category_name = coco_data["categories"][label_id]["name"]
                    category_id = coco_data["categories"][label_id]["id"]
                else:
                    category_id = 1  # Default to first category
                
                # Calculate area
                area = bbox[2] * bbox[3]
                
                coco_annotation = {
                    "id": annotation_id,
                    "image_id": image_id,
                    "category_id": category_id,
                    "bbox": bbox,  # [x, y, width, height]
                    "area": area,
                    "iscrowd": 0,
                    "segmentation": []  # Empty for bbox-only detections
                }
                
                # Add tracking information if available
                if "track_id" in ann.get("attributes", {}):
                    coco_annotation["track_id"] = ann["attributes"]["track_id"]
                
                coco_data["annotations"].append(coco_annotation)
                annotation_id += 1
            
            # Handle polygon segmentation
            elif ann_type == "polygon" and "points" in ann:
                points = ann["points"]
                
                # Check if points are already flattened or nested
                if isinstance(points, list) and len(points) > 0:
                    if isinstance(points[0], (list, tuple)):
                        # Points are nested: [[x1, y1], [x2, y2], ...]
                        # Flatten to COCO format: [x1, y1, x2, y2, ...]
                        segmentation = []
                        for point in points:
                            segmentation.extend(point)
                        xs = [p[0] for p in points]
                        ys = [p[1] for p in points]
                    else:
                        # Points are already flattened: [x1, y1, x2, y2, ...]
                        segmentation = points
                        xs = [points[i] for i in range(0, len(points), 2)]
                        ys = [points[i] for i in range(1, len(points), 2)]
                else:
                    continue  # Skip if points are malformed
                
                # Calculate bbox from polygon
                x_min, x_max = min(xs), max(xs)
                y_min, y_max = min(ys), max(ys)
                bbox = [x_min, y_min, x_max - x_min, y_max - y_min]
                area = (x_max - x_min) * (y_max - y_min)
                
                label_id = ann.get("label_id", 0)
                if label_id < len(coco_data["categories"]):
                    category_id = coco_data["categories"][label_id]["id"]
                else:
                    category_id = 1
                
                coco_annotation = {
                    "id": annotation_id,
                    "image_id": image_id,
                    "category_id": category_id,
                    "bbox": bbox,
                    "area": area,
                    "iscrowd": 0,
                    "segmentation": [segmentation]
                }
                
                if "track_id" in ann.get("attributes", {}):
                    coco_annotation["track_id"] = ann["attributes"]["track_id"]
                
                coco_data["annotations"].append(coco_annotation)
                annotation_id += 1
    
    return coco_data


def get_pipeline_type(pipeline_id: str) -> str:
    """Determine annotation type from pipeline ID."""
    if "tracking" in pipeline_id.lower():
        return "tracking"
    elif "semantic_segmentation" in pipeline_id.lower():
        return "semantic_segmentation"
    elif "segmentation" in pipeline_id.lower():
        return "instance_segmentation"
    elif "2d" in pipeline_id.lower():
        return "detection"
    return "detection"


def calipergt_to_kitti3d(calipergt_data: Dict[str, Any]) -> bytes:
    """
    Convert CaliperGT 3D annotations to KITTI 3D tracking format.

    CaliperGT 3D format has:
    - tracks: list of track objects, each with:
      - id: track identifier
      - frame: starting frame number
      - label: class name (e.g., "pedestrian")
      - shapes: list of cuboid shapes with:
        - type: "cuboid"
        - frame: frame number
        - points: [x, y, z, rx, ry, rz, width, length, height, ...]
        - outside: boolean (if true, track ends/not visible)

    KITTI 3D tracking format (per line in .txt file):
    <frame> <track_id> <class> <truncated> <occluded> <alpha> <left> <top> <right> <bottom> <height> <width> <length> <x> <y> <z> <rotation_y>

    For LiDAR-only data (no camera):
    - truncated: -1 (unknown)
    - occluded: -1 (unknown)
    - alpha: -10 (unknown)
    - bbox 2D: -1, -1, -1, -1 (not available)

    Returns:
        bytes: ZIP archive containing one .txt file per frame in label_2/ folder
    """
    # Group annotations by frame number
    frames_annotations: Dict[int, List[str]] = defaultdict(list)

    tracks = calipergt_data.get("tracks", [])

    for track_idx, track in enumerate(tracks):
        # Use track index as track_id since CaliperGT format doesn't include track IDs
        track_id = track_idx
        label = track.get("label", "unknown")
        # Capitalize first letter for KITTI format
        label = label.capitalize()
        shapes = track.get("shapes", [])

        for shape in shapes:
            # Skip shapes marked as "outside" (track not visible in this frame)
            if shape.get("outside", False):
                continue

            if shape.get("type") != "cuboid":
                continue

            frame_num = shape.get("frame", 0)
            points = shape.get("points", [])

            if len(points) < 9:
                continue  # Invalid cuboid data

            # Extract cuboid parameters from CaliperGT format
            # points: [x, y, z, rx, ry, rz, width, length, height, ...]
            x = points[0]
            y = points[1]
            z = points[2]
            # rx, ry are typically 0 for ground vehicles
            rz = points[5]  # yaw rotation
            width = points[6]
            length = points[7]
            height = points[8]

            # KITTI format values for LiDAR-only data
            truncated = -1  # Unknown
            occluded = -1   # Unknown
            alpha = -10     # Unknown (observation angle)
            # 2D bbox not available for LiDAR-only
            left, top, right, bottom = -1, -1, -1, -1

            # rotation_y in KITTI is the rotation around Y-axis (yaw)
            # Add pi/2 to convert from ego frame (along +X) to output frame (along +Y)
            rotation_y = rz + math.pi / 2

            # Format KITTI tracking label line
            # KITTI tracking format: frame track_id class truncated occluded alpha bbox(4) dimensions(3) location(3) rotation_y
            kitti_line = f"{frame_num} {track_id} {label} {truncated} {occluded} {alpha:.2f} {left} {top} {right} {bottom} {height:.2f} {width:.2f} {length:.2f} {x:.2f} {y:.2f} {z:.2f} {rotation_y:.2f}"

            frames_annotations[frame_num].append(kitti_line)

    # Create ZIP archive with one .txt file per frame
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Sort frames and create label files
        for frame_num in sorted(frames_annotations.keys()):
            annotations = frames_annotations[frame_num]
            # KITTI uses 6-digit zero-padded frame numbers
            filename = f"{frame_num:06d}.txt"
            content = "\n".join(annotations)
            zip_file.writestr(f"label_2/{filename}", content)

    zip_buffer.seek(0)
    return zip_buffer.read()


def transform_lidar_orientation(calipergt_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform CaliperGT 3D annotations to add pi/2 to orientation.

    Converts boxes from ego frame orientation (along +X) to output frame (along +Y).

    Args:
        calipergt_data: CaliperGT format annotations with tracks containing cuboid shapes

    Returns:
        Modified copy of calipergt_data with orientations adjusted by pi/2
    """
    import copy

    # Deep copy to avoid modifying original data
    result = copy.deepcopy(calipergt_data)

    tracks = result.get("tracks", [])

    for track in tracks:
        shapes = track.get("shapes", [])

        for shape in shapes:
            if shape.get("type") != "cuboid":
                continue

            points = shape.get("points", [])

            if len(points) >= 6:
                # points format: [x, y, z, rx, ry, rz, width, length, height, ...]
                # rz (yaw) is at index 5
                # Add pi/2 to convert from ego frame (along +X) to output frame (along +Y)
                points[5] = points[5] + math.pi / 2

    return result
