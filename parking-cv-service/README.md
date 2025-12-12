# Parking CV Service

Computer Vision service for parking management system using YOLOv8 and OCR.

## Features

- **Entry Pipeline**: Vehicle and license plate detection at parking entry points
- **Indoor Pipeline**: Real-time parking spot occupancy monitoring
- **Vehicle Detection**: YOLOv8-based vehicle detection (cars, motorcycles, buses, trucks)
- **License Plate Recognition**: Automatic plate detection and OCR
- **Backend Integration**: RESTful API integration with parking management backend

## Project Structure

```
parking-cv-service/
│
├── src/
│   ├── config.py                 # Configuration management
│   ├── models/
│   │   ├── vehicle_detector.py  # Vehicle detection using YOLOv8
│   │   ├── plate_detector.py    # License plate detection
│   │   └── plate_ocr.py         # OCR for license plates
│   ├── pipelines/
│   │   ├── entry_pipeline.py    # Entry processing pipeline
│   │   └── indoor_pipeline.py   # Indoor monitoring pipeline
│   ├── clients/
│   │   └── backend_client.py    # Backend API client
│   ├── main_entry.py            # Entry service entry point
│   └── main_indoor.py           # Indoor service entry point
│
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment variables template
└── README.md                    # This file
```

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd parking-cv-service
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Download YOLOv8 models:
```bash
# Create models directory
mkdir models

# Download models (you'll need to train or obtain these)
# Place vehicle detection model: models/vehicle_yolov8n.pt
# Place plate detection model: models/plate_yolov8n.pt
```

5. Configure environment:
```bash
cp .env.example .env
# Edit .env with your settings
```

## Configuration

Edit `.env` file to configure:

- **Backend API**: URL and authentication
- **Model Paths**: Paths to YOLOv8 model weights
- **Detection Thresholds**: Confidence thresholds for detections
- **Camera Sources**: Camera URLs or device indices
- **Processing Settings**: Frame skip rate, retry attempts
- **Logging**: Log level configuration

## Usage

### Entry Monitoring Service

Monitor vehicle entries and perform license plate recognition:

```bash
python src/main_entry.py
```

Options:
- `--camera <source>`: Specify camera source (URL or device index)
- `--no-display`: Run without video display
- `--log-level <level>`: Set logging level (DEBUG, INFO, WARNING, ERROR)

Example:
```bash
python src/main_entry.py --camera 0 --log-level DEBUG
```

### Indoor Monitoring Service

Monitor parking spot occupancy:

```bash
python src/main_indoor.py --spots-config parking_spots.json
```

Options:
- `--camera <source>`: Specify camera source
- `--spots-config <file>`: Path to parking spots configuration
- `--no-display`: Run without video display
- `--log-level <level>`: Set logging level

Example parking spots configuration (`parking_spots.json`):
```json
{
  "parking_spots": [
    {"id": "A1", "bbox": [100, 200, 300, 400]},
    {"id": "A2", "bbox": [350, 200, 550, 400]},
    {"id": "B1", "bbox": [100, 450, 300, 650]}
  ]
}
```

## API Integration

The service communicates with the backend API:

### Entry Registration
```
POST /api/entries
{
  "plate_number": "ABC123",
  "vehicle_type": "car",
  "timestamp": "2025-12-12T10:30:00",
  "confidence": 0.95
}
```

### Parking Status Update
```
POST /api/parking-status
{
  "total_spots": 50,
  "occupied_spots": 32,
  "available_spots": 18,
  "changes": [
    {"spot_id": "A1", "occupied": true, "timestamp": "2025-12-12T10:30:00"}
  ]
}
```

## Models

### Vehicle Detection
- Uses YOLOv8 for detecting cars, motorcycles, buses, and trucks
- Configurable confidence threshold
- Supports real-time inference

### License Plate Detection
- Custom YOLOv8 model trained for license plates
- Region-based detection within vehicle bounding boxes
- High accuracy plate localization

### OCR
- EasyOCR for text extraction
- Multi-language support
- Preprocessing pipeline for improved accuracy
- Text validation and cleaning

## Development

### Adding New Features

1. **Custom Vehicle Classes**: Modify `vehicle_classes` in `VehicleDetector`
2. **Plate Format Validation**: Update `validate_plate_format` in `PlateOCR`
3. **Backend Endpoints**: Add methods to `BackendClient`

### Testing

Run components individually:

```python
from src.models import VehicleDetector, PlateDetector, PlateOCR
from src.config import Config

# Test vehicle detection
detector = VehicleDetector(Config.VEHICLE_MODEL_PATH)
detections = detector.detect(image)

# Test plate OCR
ocr = PlateOCR()
text = ocr.read_text(plate_image)
```

## Troubleshooting

### Camera Issues
- Verify camera source is correct (0 for default webcam, URL for IP cameras)
- Check camera permissions
- Test camera with: `cv2.VideoCapture(0).isOpened()`

### Model Loading Errors
- Ensure model files exist in specified paths
- Check CUDA availability for GPU inference
- Verify model compatibility with ultralytics version

### OCR Accuracy
- Improve lighting conditions
- Adjust `OCR_CONFIDENCE_THRESHOLD`
- Use `read_with_multiple_attempts` for difficult cases

### Backend Connection
- Verify `BACKEND_URL` is correct
- Check API key authentication
- Test with `BackendClient.health_check()`

## Performance Optimization

- Adjust `FRAME_SKIP` to balance accuracy and performance
- Use GPU acceleration for YOLOv8 inference
- Optimize parking spot ROIs to minimize processing area
- Consider model quantization for edge deployment

## License

[Your License Here]

## Contributing

[Contributing Guidelines Here]
