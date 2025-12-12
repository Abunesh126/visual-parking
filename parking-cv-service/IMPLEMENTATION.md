# Parking CV Service - Implementation Guide

## Table of Contents
1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [Workflow Details](#workflow-details)
4. [Component Details](#component-details)
5. [API Integration](#api-integration)
6. [Deployment Guide](#deployment-guide)
7. [Testing & Calibration](#testing--calibration)

---

## System Overview

### Project Vision
An AI-powered automatic parking management system for malls that uses computer vision to:
- Detect and track vehicles from entry to exit
- Assign parking slots automatically based on vehicle type
- Monitor slot occupancy in real-time
- Generate entry/exit receipts with timestamps
- Calculate parking duration and billing
- Provide real-time dashboard for administration

### System Specifications

**Parking Capacity:**
- **Floor A**: 20 car slots + 16 bike slots = 36 slots
- **Floor B**: 20 car slots + 16 bike slots = 36 slots
- **Total**: 72 parking slots

**Camera Infrastructure:**
- 1 Entry camera (detects vehicle type + license plate)
- 1 Exit camera (verifies vehicle + calculates duration)
- Floor A Indoor: 10 car cameras (4 slots each) + 4 bike cameras (8 slots each)
- Floor B Indoor: 10 car cameras (4 slots each) + 4 bike cameras (8 slots each)
- **Total**: 30 cameras

**Vehicle Types Supported:**
- Cars (including SUVs, sedans)
- Motorcycles/Bikes

---

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                    PARKING CV SERVICE                        │
│                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │   Entry      │    │   Indoor     │    │    Exit      │  │
│  │  Pipeline    │    │  Pipeline    │    │  Pipeline    │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│         │                    │                    │         │
│         ├────────────────────┴────────────────────┤         │
│         │                                         │         │
│  ┌──────▼─────────────────────────────────────────▼──────┐  │
│  │              CV Models (YOLOv8)                       │  │
│  │  • Vehicle Detector                                   │  │
│  │  • License Plate Detector                            │  │
│  │  • OCR Engine (EasyOCR)                              │  │
│  └──────────────────────────────────────────────────────┘  │
│                          │                                  │
└──────────────────────────┼──────────────────────────────────┘
                           │
                           │ REST API Calls
                           │
┌──────────────────────────▼──────────────────────────────────┐
│              BACKEND API (FastAPI/Django)                   │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Endpoints:                                            │ │
│  │  • POST /api/v1/entry-events                          │ │
│  │  • POST /api/v1/slot-occupancy                        │ │
│  │  • POST /api/v1/exit-events                           │ │
│  │  • GET  /api/v1/slots                                 │ │
│  └────────────────────────────────────────────────────────┘ │
│                          │                                  │
│  ┌────────────────────────▼────────────────────────────────┐ │
│  │              MySQL Database                            │ │
│  │  • floors, slots, cameras                             │ │
│  │  • tickets, events_log                                │ │
│  └────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                  ADMIN DASHBOARD (React)                     │
│                                                              │
│  • Real-time occupancy view                                 │
│  • Camera feeds                                             │
│  • Active vehicles list                                     │
│  • Revenue analytics                                        │
│  • Slot management                                          │
└──────────────────────────────────────────────────────────────┘
```

### Technology Stack

**CV Service (This Repository):**
- Python 3.8+
- PyTorch + YOLOv8 (Ultralytics)
- EasyOCR for license plate reading
- OpenCV for image processing
- Requests for API communication

**Backend (Separate Repository):**
- FastAPI or Django REST Framework
- MySQL/PostgreSQL database
- SQLAlchemy ORM
- Redis for caching (optional)

**Dashboard (Separate Repository):**
- React.js or Next.js
- Material-UI or Ant Design
- Recharts for analytics
- WebSocket for real-time updates

---

## Workflow Details

### 1. Vehicle Entry Process

**Step-by-Step Flow:**

1. **Vehicle Arrives at Entry Gate**
   - Entry camera continuously monitors the entry zone
   - Frame processing at configurable FPS (default: skip every 5 frames)

2. **Vehicle Detection**
   - YOLOv8 model detects vehicle in frame
   - Classifies vehicle type (car, motorcycle, bus, truck)
   - Extracts bounding box of largest vehicle (closest to camera)

3. **License Plate Detection**
   - Within vehicle ROI, detect license plate using specialized YOLOv8 model
   - Extract plate bounding box with confidence score

4. **OCR Processing**
   - Crop plate image from frame
   - Preprocess: grayscale, adaptive threshold, denoise, resize
   - EasyOCR extracts text with multiple attempts
   - Clean and validate plate format

5. **Backend Communication**
   ```python
   POST /api/v1/entry-events
   {
       "plate_number": "ABC1234",
       "vehicle_type": "car",
       "timestamp": "2025-12-12T10:30:00",
       "confidence": 0.85
   }
   ```

6. **Backend Response**
   ```json
   {
       "ticket_id": 12345,
       "slot_assigned": "A-C-05",
       "floor": "A",
       "entry_time": "2025-12-12T10:30:00",
       "status": "success"
   }
   ```

7. **Gate Opens**
   - Backend triggers gate controller
   - Driver receives digital ticket/QR code
   - Vehicle proceeds to assigned slot

**Entry Pipeline Code Flow:**
```
frame → vehicle_detector.detect()
      → plate_detector.detect_in_roi()
      → plate_ocr.read_with_multiple_attempts()
      → backend_client.register_entry()
      → result
```

### 2. Indoor Slot Monitoring Process

**Step-by-Step Flow:**

1. **Continuous Monitoring**
   - Each indoor camera monitors its assigned slots
   - Example: FLOOR_A_CAR_CAM_1 monitors slots A-C-01 to A-C-04

2. **Slot Occupancy Detection**
   - For each parking spot in camera view:
     - Extract ROI based on configured bounding box
     - Run vehicle detection on ROI
     - Calculate overlap between detection and slot area
     - If overlap > 30%, mark as occupied

3. **State Change Detection**
   - Compare current state with previous state
   - Detect transitions: FREE → OCCUPIED or OCCUPIED → FREE

4. **Backend Update**
   ```python
   POST /api/v1/slot-occupancy
   {
       "camera_id": "FLOOR_A_CAR_CAM_1",
       "timestamp": "2025-12-12T10:32:00",
       "changes": [
           {
               "slot_id": "A-C-05",
               "occupied": true,
               "timestamp": "2025-12-12T10:32:00"
           }
       ]
   }
   ```

5. **Misparking Detection (V2 Feature)**
   - If occupied slot has no matching ticket → unknown vehicle
   - If ticketed vehicle detected in wrong slot → mispark flag + fine

**Indoor Pipeline Code Flow:**
```
frame → for each slot:
            is_spot_occupied(frame, slot_bbox)
      → detect state changes
      → backend_client.update_parking_status()
```

### 3. Vehicle Exit Process (V3 Feature)

**Step-by-Step Flow:**

1. **Vehicle Approaches Exit**
   - Exit camera detects vehicle
   - Reads license plate using same process as entry

2. **Ticket Lookup**
   ```python
   GET /api/vehicles/{plate_number}
   ```
   Returns entry time, slot, vehicle type

3. **Duration Calculation**
   ```python
   duration = exit_time - entry_time
   # Calculate billing based on tariff
   ```

4. **Payment Processing**
   - Display amount on screen
   - Wait for payment confirmation
   - Update ticket status to CLOSED

5. **Gate Opens**
   - Record exit event
   - Update slot to FREE
   - Generate exit receipt

---

## Component Details

### 1. Vehicle Detector (`vehicle_detector.py`)

**Purpose:** Detect vehicles and classify their type

**Key Features:**
- Uses YOLOv8 for object detection
- Filters for vehicle classes: car (2), motorcycle (3), bus (5), truck (7)
- Confidence threshold: 0.5 (configurable)
- Returns largest vehicle (closest to camera)

**Methods:**
```python
detect(image) → List[dict]
    # Returns: [{'bbox': [x1,y1,x2,y2], 'confidence': 0.85, 
    #           'class_id': 2, 'class_name': 'car'}]

get_largest_vehicle(detections) → dict
    # Returns detection with largest bounding box area

draw_detections(image, detections) → np.ndarray
    # Visualize detections on image
```

### 2. Plate Detector (`plate_detector.py`)

**Purpose:** Detect license plates in vehicle images

**Key Features:**
- YOLOv8 model trained on license plate dataset
- Confidence threshold: 0.6
- Can detect in full image or ROI

**Methods:**
```python
detect(image) → List[dict]
    # Returns: [{'bbox': [x1,y1,x2,y2], 'confidence': 0.92}]

detect_in_roi(image, roi_bbox) → List[dict]
    # Detect plates within vehicle bounding box

get_best_plate(detections) → dict
    # Returns plate with highest confidence

crop_plate(image, bbox, padding=5) → np.ndarray
    # Extract plate image with padding
```

### 3. Plate OCR (`plate_ocr.py`)

**Purpose:** Extract text from license plate images

**Key Features:**
- EasyOCR engine with GPU support
- Preprocessing: grayscale, threshold, denoise, resize
- Multiple attempt strategy for better accuracy
- Text cleaning and validation

**Methods:**
```python
preprocess_plate(plate_image) → np.ndarray
    # Enhance image for better OCR

read_text(plate_image, preprocess=True) → str
    # Extract text from plate image

read_with_multiple_attempts(plate_image) → str
    # Try multiple preprocessing strategies

validate_plate_format(text, pattern=None) → bool
    # Validate against expected format
```

### 4. Entry Pipeline (`entry_pipeline.py`)

**Purpose:** Orchestrate entry processing workflow

**Process:**
1. Read frame from entry camera
2. Detect vehicle → detect plate → OCR
3. Validate and deduplicate
4. Send to backend
5. Display results (optional)

**Key Features:**
- Frame skipping for performance
- Duplicate detection (10-second window)
- Error handling and retry logic
- Visual display with annotations

### 5. Indoor Pipeline (`indoor_pipeline.py`)

**Purpose:** Monitor parking slot occupancy

**Process:**
1. Read frame from indoor camera
2. Check each configured parking spot
3. Detect occupancy changes
4. Update backend
5. Display occupancy map (optional)

**Key Features:**
- Multi-slot monitoring per camera
- State change detection
- Color-coded visualization (green=free, red=occupied)
- Occupancy statistics

### 6. Backend Client (`backend_client.py`)

**Purpose:** Communicate with backend API

**Endpoints:**
```python
register_entry(plate, type, timestamp, confidence)
    → POST /api/entries

register_exit(plate, timestamp, duration)
    → POST /api/exits

update_parking_status(total, occupied, available, changes)
    → POST /api/parking-status

get_vehicle_info(plate_number)
    → GET /api/vehicles/{plate}

get_parking_availability()
    → GET /api/parking-status

health_check()
    → GET /api/health
```

---

## API Integration

### Backend API Specification (V1)

#### 1. Entry Event

**Endpoint:** `POST /api/v1/entry-events`

**Request:**
```json
{
  "plate_number": "ABC1234",
  "vehicle_type": "car",
  "timestamp": "2025-12-12T10:30:00Z",
  "confidence": 0.85,
  "image": "base64_encoded_image" // optional
}
```

**Response:**
```json
{
  "success": true,
  "ticket_id": 12345,
  "slot_assigned": "A-C-05",
  "floor": "A",
  "entry_time": "2025-12-12T10:30:00Z",
  "message": "Entry registered successfully"
}
```

#### 2. Slot Occupancy Update

**Endpoint:** `POST /api/v1/slot-occupancy`

**Request:**
```json
{
  "camera_id": "FLOOR_A_CAR_CAM_1",
  "timestamp": "2025-12-12T10:32:00Z",
  "total_spots": 4,
  "occupied_spots": 1,
  "available_spots": 3,
  "changes": [
    {
      "slot_id": "A-C-05",
      "occupied": true,
      "timestamp": "2025-12-12T10:32:00Z"
    }
  ]
}
```

**Response:**
```json
{
  "success": true,
  "updated_slots": ["A-C-05"],
  "total_occupied": 15,
  "total_available": 57
}
```

#### 3. Get Slots Status

**Endpoint:** `GET /api/v1/slots?floor=A`

**Response:**
```json
{
  "floor": "A",
  "total_slots": 36,
  "car_slots": {
    "total": 20,
    "occupied": 8,
    "available": 12
  },
  "bike_slots": {
    "total": 16,
    "occupied": 5,
    "available": 11
  },
  "slots": [
    {
      "id": "A-C-01",
      "type": "car",
      "status": "FREE",
      "current_plate": null
    },
    {
      "id": "A-C-05",
      "type": "car",
      "status": "OCCUPIED",
      "current_plate": "ABC1234"
    }
  ]
}
```

---

## Deployment Guide

### Prerequisites

1. **Hardware Requirements:**
   - GPU: NVIDIA GPU with 4GB+ VRAM (recommended for real-time processing)
   - CPU: 8+ cores (if running without GPU)
   - RAM: 16GB+ (for all 30 camera streams)
   - Storage: 100GB+ for logs, models, recordings

2. **Software Requirements:**
   - Python 3.8 or higher
   - CUDA 11.0+ (for GPU acceleration)
   - MySQL 8.0+ (backend database)

### Installation Steps

1. **Clone Repository:**
   ```bash
   git clone <repository-url>
   cd parking-cv-service
   ```

2. **Create Virtual Environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Download YOLOv8 Models:**
   ```bash
   mkdir models
   # Option 1: Use pretrained COCO model
   wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt -O models/vehicle_yolov8n.pt
   
   # Option 2: Train custom plate detection model
   # See training guide in docs/training.md
   ```

5. **Configure Environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

6. **Configure Parking Spots:**
   ```bash
   # Edit parking_spots.json
   # Calibrate bounding boxes for each camera
   python tools/calibrate_spots.py --camera FLOOR_A_CAR_CAM_1
   ```

### Running Services

**Entry Monitoring:**
```bash
python src/main_entry.py --camera rtsp://192.168.1.100/entry
```

**Indoor Monitoring (Floor A, Camera 1):**
```bash
python src/main_indoor.py \
    --camera rtsp://192.168.1.110/floor_a_car_1 \
    --spots-config parking_spots_floor_a_car_1.json
```

**Run All Services with Docker:**
```bash
docker-compose up -d
```

### Production Deployment

**Using Docker Compose:**
```yaml
# See docker-compose.yml
services:
  - cv-entry
  - cv-indoor-a-car-1 through cv-indoor-a-car-10
  - cv-indoor-a-bike-1 through cv-indoor-a-bike-4
  - cv-indoor-b-car-1 through cv-indoor-b-car-10
  - cv-indoor-b-bike-1 through cv-indoor-b-bike-4
```

**Scaling Considerations:**
- Deploy each camera service as separate container
- Use load balancer for API calls
- Implement message queue (RabbitMQ/Redis) for async processing
- Set up monitoring with Prometheus + Grafana

---

## Testing & Calibration

### Unit Testing

```bash
pytest tests/
pytest tests/test_vehicle_detector.py -v
pytest tests/test_plate_ocr.py -v
```

### Camera Calibration

**Calibrate Parking Spot ROIs:**
```bash
python tools/calibrate_spots.py \
    --camera rtsp://192.168.1.110/floor_a_car_1 \
    --output parking_spots_floor_a_car_1.json
```

This opens an interactive window where you can:
1. Click to define parking spot corners
2. Label each spot (A-C-01, A-C-02, etc.)
3. Save configuration to JSON

### Performance Testing

**Test Detection Accuracy:**
```bash
python tools/test_accuracy.py \
    --images test_images/ \
    --ground-truth annotations.json
```

**Test API Performance:**
```bash
python tools/load_test.py \
    --endpoint http://localhost:8000/api/v1/entry-events \
    --requests 1000 \
    --concurrent 10
```

### Live Testing Checklist

- [ ] Entry camera detects all vehicle types
- [ ] Plate detection works in day and night conditions
- [ ] OCR accuracy > 95% for standard plates
- [ ] Backend receives events within 1 second
- [ ] Indoor cameras detect occupancy changes
- [ ] No false positives for empty spots
- [ ] Dashboard updates in real-time
- [ ] System handles camera disconnections gracefully

---

## Troubleshooting

### Common Issues

**1. Low Detection Accuracy**
- Check camera positioning and lighting
- Adjust confidence thresholds
- Retrain models with local dataset

**2. High CPU/GPU Usage**
- Increase FRAME_SKIP value
- Reduce camera resolution
- Use smaller YOLO model (yolov8n instead of yolov8x)

**3. API Timeouts**
- Check network connectivity
- Increase MAX_RETRY_ATTEMPTS
- Implement request queue

**4. OCR Reading Wrong Characters**
- Improve plate preprocessing
- Add region-specific character validation
- Use multiple OCR engines (Tesseract + EasyOCR)

---

## Future Enhancements

### V2 Features (Misparking Detection)
- License plate tracking across cameras
- Mispark detection and fine calculation
- Real-time alerts for violations

### V3 Features (Exit & Billing)
- Exit pipeline implementation
- Duration calculation and billing
- Payment gateway integration
- Receipt generation

### V4 Features (Admin Dashboard)
- Real-time occupancy visualization
- Camera feed streaming
- Revenue analytics
- User management

### Advanced Features
- Predictive analytics for peak hours
- EV charging slot management
- Reserved parking slots
- Mobile app integration
- License plate recognition for VIP/blacklist

---

## References

- YOLOv8 Documentation: https://docs.ultralytics.com/
- EasyOCR: https://github.com/JaidedAI/EasyOCR
- FastAPI: https://fastapi.tiangolo.com/
- OpenCV Python: https://docs.opencv.org/

---

**Last Updated:** December 12, 2025  
**Version:** 1.0  
**Maintainer:** Parking CV Team
