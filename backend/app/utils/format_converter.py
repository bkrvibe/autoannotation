"""
Format converter utilities for annotation data.
Converts between CaliperGT and COCO formats.
"""
import json
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
