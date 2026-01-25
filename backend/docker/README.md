# Docker Images

## Download Data Task Images

For the download data task, use one of these minimal images instead of the full ML image:

### Option 1: Dockerfile.download (~200MB)
Python 3.10 slim base with Google Cloud SDK and gsutil.

```bash
docker build -f docker/Dockerfile.download -t download-data:latest .
```

### Option 2: Dockerfile.download-minimal (~150MB)
Uses official Google Cloud SDK slim image. Smallest option.

```bash
docker build -f docker/Dockerfile.download-minimal -t download-data:minimal .
```

## Usage

```bash
# Run with GCS credentials
docker run -v /path/to/credentials.json:/credentials.json \
  -e GOOGLE_APPLICATION_CREDENTIALS=/credentials.json \
  download-data:latest gsutil cp -r gs://bucket/path /local/path

# Or with Python
docker run -v /path/to/credentials.json:/credentials.json \
  -e GOOGLE_APPLICATION_CREDENTIALS=/credentials.json \
  download-data:latest python -c "
from google.cloud import storage
client = storage.Client()
# ... download logic
"
```

## Size Comparison

| Image | Size | Use Case |
|-------|------|----------|
| nvidia/cuda + MS3D (full) | ~15GB+ | ML inference tasks |
| download-data:latest | ~200MB | Download/upload tasks |
| download-data:minimal | ~150MB | Download/upload tasks |
