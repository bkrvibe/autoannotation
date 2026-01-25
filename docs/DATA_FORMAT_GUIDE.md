# Data Format Guide - Auto-Annotation Platform

This guide describes the expected data formats for the Auto-Annotation Platform (CaliperGT).

## Table of Contents
1. [2D Image Annotation](#2d-image-annotation)
2. [3D LiDAR Annotation](#3d-lidar-annotation)
3. [Annotation Output Formats](#annotation-output-formats)
4. [Troubleshooting](#troubleshooting)

---

## 2D Image Annotation

### Supported Pipelines
- **2D Object Detection** - Detects vehicles, pedestrians, and other objects
- **2D Instance Segmentation** - Pixel-level object masks with bounding boxes
- **2D Semantic Segmentation** - Full scene segmentation (road, sidewalk, vehicles, etc.)
- **2D Object Tracking** - Multi-object tracking across video frames

### Input Data Structure

#### Standard Format (Recommended)
```
data/
  images/
    image001.jpg
    image002.jpg
    image003.png
    ...
```

#### Flat Format
```
data/
  image001.jpg
  image002.jpg
  image003.png
  ...
```

#### Video Frames Format
```
data/
  frame_0000.jpg
  frame_0001.jpg
  frame_0002.jpg
  ...
```

### Supported Image Formats
- `.jpg`, `.jpeg` - JPEG images
- `.png` - PNG images
- `.bmp` - Bitmap images
- `.gif` - GIF images
- `.tiff` - TIFF images
- `.webp` - WebP images

### Best Practices for 2D Data
1. **Consistent resolution** - All images should have the same resolution for best results
2. **Sequential naming** - Use sequential naming for video frames (e.g., `frame_0001.jpg`)
3. **No nested directories** - Keep images flat in one directory
4. **Clean filenames** - Avoid special characters in filenames

---

## 3D LiDAR Annotation

### Supported Pipeline
- **3D Object Detection & Tracking** - 3D bounding boxes for vehicles, pedestrians, cyclists

### Input Data Formats

The platform supports two input formats for 3D data:

#### CaliperGT Format (Ready to Use)

This is the processed format that can be used directly without transformation.

```
data/
  pointcloud/
    lidar__1234567890.pcd
    lidar__1234567891.pcd
    lidar__1234567892.pcd
    ...
  related_images/
    lidar__1234567890_pcd/
      sensor_calibrations.json
      01_CAM_FRONT_LEFT.jpg
      02_CAM_FRONT.jpg
      03_CAM_FRONT_RIGHT.jpg
      04_CAM_BACK_RIGHT.jpg
      05_CAM_BACK.jpg
      06_CAM_BACK_LEFT.jpg
    lidar__1234567891_pcd/
      sensor_calibrations.json
      01_CAM_FRONT_LEFT.jpg
      ...
  cameras/ (optional)
    01_CAM_FRONT_LEFT/
      lidar__1234567890.jpg
      lidar__1234567891.jpg
      ...
    02_CAM_FRONT/
      lidar__1234567890.jpg
      ...
```

##### sensor_calibrations.json Structure
```json
{
  "LIDAR_TOP": {
    "sensor_calibration": {
      "rotation": [1.0, 0.0, 0.0, 0.0],
      "translation": [0.0, 0.0, 0.0]
    },
    "ego_pose": {
      "rotation": [w, x, y, z],
      "translation": [x, y, z]
    }
  },
  "ego_pose": {
    "rotation": [w, x, y, z],
    "translation": [x, y, z]
  },
  "01_CAM_FRONT_LEFT": {
    "transformation_matrix": [[4x4 matrix]],
    "camera_intrinsic": [[3x3 matrix]]
  }
}
```

#### Custom Format (Auto-Transformed)

This format will be automatically transformed to CaliperGT format during processing.

```
data/
  lidar/
    000000.pcd
    000001.pcd
    000002.pcd
    ...
  calibration.json
  ego_poses/
    poses.json
  cameras/  (optional)
    front_left/
      000000.jpg
      000001.jpg
      ...
    front/
      000000.jpg
      000001.jpg
      ...
    front_right/
      000000.jpg
      ...
    rear_left/
      000000.jpg
      ...
    rear/
      000000.jpg
      ...
    rear_right/
      000000.jpg
      ...
```

##### calibration.json Structure
```json
{
  "ego_to_lidar": {
    "rotation": [[3x3 rotation matrix]],
    "translation": [x, y, z]
  },
  "lidar_to_cameras": {
    "front_left": {
      "extrinsic": {
        "rotation": [[3x3 matrix]],
        "translation": [x, y, z]
      },
      "intrinsic": {
        "fx": 1000.0,
        "fy": 1000.0,
        "cx": 800.0,
        "cy": 450.0
      }
    },
    "front": {...},
    "front_right": {...},
    "rear_left": {...},
    "rear": {...},
    "rear_right": {...}
  }
}
```

##### poses.json Structure
```json
{
  "frames": [
    {
      "timestamp": 1234567890.123,
      "position": [x, y, z],
      "rotation": [w, x, y, z]
    },
    {
      "timestamp": 1234567890.223,
      "position": [x, y, z],
      "rotation": [w, x, y, z]
    }
  ]
}
```

### Camera View Naming Convention

The platform automatically maps camera folder names to standard views:

| Input Names | Mapped To |
|------------|-----------|
| `front_left`, `cam_front_left` | `01_CAM_FRONT_LEFT` |
| `front` | `02_CAM_FRONT` |
| `front_right`, `cam_front_right` | `03_CAM_FRONT_RIGHT` |
| `rear_right`, `back_right` | `04_CAM_BACK_RIGHT` |
| `rear`, `back` | `05_CAM_BACK` |
| `rear_left`, `back_left` | `06_CAM_BACK_LEFT` |

### Point Cloud Format
- **PCD files** (`.pcd`) - Point Cloud Data format (recommended)
- **BIN files** (`.bin`) - Binary point cloud format

---

## Annotation Output Formats

### CaliperGT Format (Native)

This is the internal annotation format used by the platform.

#### 2D Annotations (Detection/Tracking)
```json
{
  "categories": {
    "label": {
      "labels": [
        {"name": "car", "parent": "vehicle"},
        {"name": "pedestrian", "parent": "person"}
      ]
    }
  },
  "items": [
    {
      "id": "000000.jpg",
      "width": 1920,
      "height": 1080,
      "annotations": [
        {
          "type": "bbox",
          "bbox": [x, y, width, height],
          "label_id": 0,
          "attributes": {
            "track_id": "abc123..."
          }
        }
      ]
    }
  ]
}
```

#### 3D Annotations (Detection/Tracking)
```json
{
  "tracks": [
    {
      "frame": 0,
      "label": "car",
      "shapes": [
        {
          "type": "cuboid",
          "frame": 0,
          "points": [x, y, z, rx, ry, rz, width, length, height],
          "outside": false
        },
        {
          "type": "cuboid",
          "frame": 1,
          "points": [x, y, z, rx, ry, rz, width, length, height],
          "outside": false
        }
      ]
    }
  ]
}
```

### COCO Format (Export)

Standard COCO format for 2D annotations.

```json
{
  "info": {
    "description": "Auto-annotated dataset",
    "version": "1.0",
    "year": 2026
  },
  "images": [
    {"id": 1, "file_name": "000000.jpg", "width": 1600, "height": 900}
  ],
  "categories": [
    {"id": 1, "name": "car", "supercategory": "vehicle"}
  ],
  "annotations": [
    {
      "id": 1,
      "image_id": 1,
      "category_id": 1,
      "bbox": [x, y, width, height],
      "area": 12345.0,
      "iscrowd": 0,
      "track_id": "abc123..."
    }
  ]
}
```

### KITTI 3D Format (Export)

Standard KITTI format for 3D annotations.

```
# label_2/000000.txt
# Format: class truncated occluded alpha bbox(4) dimensions(3) location(3) rotation_y [score]

Car 0.00 0 0.00 0.00 0.00 0.00 0.00 1.67 1.93 4.92 -15.91 47.42 -0.37 -0.75 1.00
Pedestrian 0.00 0 0.00 0.00 0.00 0.00 0.00 1.80 0.60 0.80 5.12 10.23 -0.12 1.57 0.95
```

Field descriptions:
1. **class** - Object class (Car, Pedestrian, Cyclist, etc.)
2. **truncated** - Truncation level (0-1, or -1 for LiDAR-only)
3. **occluded** - Occlusion level (0-3, or -1 for unknown)
4. **alpha** - Observation angle (-10 for LiDAR-only)
5-8. **bbox** - 2D bounding box (left, top, right, bottom) or -1 for LiDAR-only
9-11. **dimensions** - Height, Width, Length in meters
12-14. **location** - 3D center (x, y, z) in camera coordinates
15. **rotation_y** - Rotation around Y-axis (yaw)
16. **score** - Confidence score (optional)

---

## Troubleshooting

### Common Issues

#### "No point cloud files found"
- Ensure `.pcd` files are in the `lidar/` or `pointcloud/` directory
- Check that files have the correct `.pcd` extension

#### "Missing calibration.json"
- The custom format requires a `calibration.json` file at the root
- Include `ego_to_lidar` transform at minimum

#### "Missing poses.json"
- Create `ego_poses/poses.json` with vehicle pose data
- Each frame needs a corresponding pose entry

#### "Could not detect 3D data structure"
- Ensure directory structure matches one of the supported formats
- Check that required files (calibration.json, poses.json) exist

#### "No image files found"
- Check that images use supported extensions (.jpg, .png, etc.)
- Ensure images are not in nested subdirectories (for 2D)

### Data Validation

The platform automatically validates your data structure upon upload and provides:
- **Errors** - Critical issues that must be fixed
- **Warnings** - Potential problems that may affect results
- **Suggestions** - Recommendations for optimal processing

### Getting Help

If you encounter issues not covered here:
1. Check the validation feedback in the UI
2. Review the expected structure in the "Show data structure" help
3. Contact support with the validation error messages
