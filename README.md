# 🚗 Automatic Mall Car Parking System

> An AI-powered automatic parking system for malls that uses computer vision to detect vehicles, assign slots, generate entry/exit receipts, monitor occupancy, manage fines, and automate payment through a connected admin dashboard.

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18+-61DAFB.svg)](https://reactjs.org/)
[![YOLOv8](https://img.shields.io/badge/YOLOv8-Ultralytics-purple.svg)](https://docs.ultralytics.com/)

---

## 📋 Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [System Objectives](#system-objectives)
- [Tech Stack](#tech-stack)
- [System Architecture](#system-architecture)
- [Process Flow](#process-flow)
- [Database Schema](#database-schema)
- [Project Structure](#project-structure)
- [Installation & Setup](#installation--setup)
- [API Endpoints](#api-endpoints)
- [Development Roadmap](#development-roadmap)
- [Expected Accuracy](#expected-accuracy)
- [Contributing](#contributing)

---

## 🎯 Overview

The **Automatic Mall Car Parking System** is a comprehensive solution that automates the entire parking management process—from vehicle entry to exit—while providing real-time insights to mall administration. The system leverages computer vision technology to detect vehicles, recognize license plates, monitor parking slots, and automate toll gate operations.

### Project Scope

- **Parking Capacity**: 2 floors (Floor A & Floor B)
  - Floor A: 20 car slots + 16 bike slots
  - Floor B: 20 car slots + 16 bike slots
  - **Total**: 40 car slots + 32 bike slots

- **Camera Setup**:
  - 1 Entry camera
  - 1 Exit camera
  - 14 Indoor cameras (10 for car slots, 4 for bike slots)

---

## ✨ Key Features

### Core Functionality

✅ **Automated Vehicle Entry**
- Real-time vehicle type detection (Car/Bike)
- License plate recognition (ANPR)
- Automatic slot assignment
- Digital parking receipt generation
- Toll gate automation

✅ **Smart Slot Monitoring**
- Real-time occupancy detection
- Misparking identification
- Dynamic slot reassignment
- License plate verification

✅ **Automated Exit & Billing**
- Vehicle identification via plate recognition
- Parking duration calculation
- Automated billing system
- Payment processing
- Toll gate control

✅ **Admin Dashboard**
- Live camera feeds
- Real-time slot occupancy
- Vehicle tracking
- Revenue analytics
- Misparking alerts
- Historical data & reports

---

## 🎯 System Objectives

The system satisfies **5 out of 6** camera-based vehicle analytics objectives:

| # | Objective | Status | Implementation |
|---|-----------|--------|----------------|
| 1 | **Detect vehicles** | ✅ Satisfied | Entry/exit/indoor cameras with YOLOv8 |
| 2 | **Track each vehicle** | ✅ Satisfied | License plate recognition across lifecycle |
| 3 | **Display insights in dashboard** | ✅ Satisfied | Real-time admin dashboard with analytics |
| 4 | **Identify vehicle type** | ✅ Satisfied | YOLOv8 classification (car/bike) |
| 5 | **Measure dwell time** | ✅ Satisfied | Entry-to-exit duration tracking |
| 6 | **Forecast traffic patterns** | ⏳ Future | Predictive analytics module (v2+) |

---

## 🛠 Tech Stack

### Computer Vision & AI
- **Framework**: PyTorch
- **Object Detection**: Ultralytics YOLOv8 (yolov8n/yolov8s)
- **OCR**: EasyOCR / Tesseract
- **Image Processing**: OpenCV
- **Numerical Computing**: NumPy

### Backend Services
- **API Framework**: FastAPI
- **Database**: MySQL
- **ORM**: SQLAlchemy
- **Caching**: Redis (optional)
- **HTTP Client**: httpx/requests

### Frontend Dashboard
- **Framework**: React (TypeScript)
- **Build Tool**: Vite
- **UI Library**: Material-UI (MUI)
- **Charting**: Recharts / Chart.js
- **State Management**: React Query

### Deployment & Infrastructure
- **Containerization**: Docker
- **Reverse Proxy**: Nginx / Traefik
- **Camera Protocol**: RTSP streams
- **IoT Integration**: MQTT / HTTP for toll gates

---

## 🏗 System Architecture

The system consists of three main services:

```
┌─────────────────────────────────────────────────────────────┐
│                     PARKING SYSTEM                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐      ┌──────────────┐    ┌────────────┐ │
│  │  CV Service  │─────▶│ Backend API  │◀───│ Dashboard  │ │
│  │   (Python)   │      │  (FastAPI)   │    │  (React)   │ │
│  └──────────────┘      └──────────────┘    └────────────┘ │
│         │                     │                            │
│         │                     │                            │
│    ┌────▼─────┐         ┌────▼────┐                       │
│    │ Cameras  │         │  MySQL  │                       │
│    │  (RTSP)  │         │Database │                       │
│    └──────────┘         └─────────┘                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Service Communication Flow

1. **CV Service** → Consumes RTSP camera streams
2. **CV Service** → POSTs detection data to Backend API
3. **Backend API** → Manages database, business logic, slot allocation
4. **Dashboard** → Fetches data from Backend API via REST
5. **Backend API** → Controls toll gate via IoT interface

---

## 🔄 Process Flow

### 1️⃣ Vehicle Entry

```
Camera Detection → YOLOv8 Detection → License Plate OCR
                                            ↓
                                    Backend API Call
                                            ↓
                        Slot Allocation ← Database Check
                                            ↓
                                  Receipt Generation
                                            ↓
                                   Toll Gate Opens
```

**JSON Payload (Entry Event)**:
```json
{
  "camera_code": "ENTRY_1",
  "plate_number": "TN09AB1234",
  "vehicle_type": "CAR",
  "confidence": 0.93,
  "captured_at": "2025-12-12T03:58:00Z"
}
```

### 2️⃣ Slot Monitoring

```
Indoor Camera → YOLOv8 Detection → ROI Overlap Check
                                          ↓
                              Multi-frame Persistence
                                          ↓
                                 Occupancy Update
                                          ↓
                              Misparking Detection
```

**JSON Payload (Slot Occupancy)**:
```json
{
  "camera_code": "A_CAR_01",
  "floor": "A",
  "detections": [
    {
      "slot_code": "A-C-01",
      "occupied": true,
      "plate_number": "TN09AB1234"
    },
    {
      "slot_code": "A-C-02",
      "occupied": false,
      "plate_number": null
    }
  ],
  "captured_at": "2025-12-12T03:58:10Z"
}
```

### 3️⃣ Vehicle Exit

```
Exit Camera → Plate Recognition → Ticket Lookup
                                        ↓
                            Duration Calculation
                                        ↓
                              Billing & Payment
                                        ↓
                             Toll Gate Opens
```

---

## 🗄 Database Schema

### Core Tables

#### `floors`
```sql
CREATE TABLE floors (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(10) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### `slots`
```sql
CREATE TABLE slots (
    id INT PRIMARY KEY AUTO_INCREMENT,
    floor_id INT NOT NULL,
    slot_code VARCHAR(20) UNIQUE NOT NULL,
    slot_type ENUM('CAR', 'BIKE') NOT NULL,
    status ENUM('FREE', 'OCCUPIED', 'RESERVED', 'DISABLED') DEFAULT 'FREE',
    current_plate VARCHAR(20) NULL,
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (floor_id) REFERENCES floors(id)
);
```

#### `cameras`
```sql
CREATE TABLE cameras (
    id INT PRIMARY KEY AUTO_INCREMENT,
    camera_code VARCHAR(20) UNIQUE NOT NULL,
    role ENUM('ENTRY', 'EXIT', 'INDOOR') NOT NULL,
    floor_id INT NULL,
    rtsp_url VARCHAR(255) NOT NULL,
    description VARCHAR(100),
    FOREIGN KEY (floor_id) REFERENCES floors(id)
);
```

#### `tickets`
```sql
CREATE TABLE tickets (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    plate_number VARCHAR(20) NOT NULL,
    vehicle_type ENUM('CAR', 'BIKE') NOT NULL,
    slot_id INT NOT NULL,
    entry_time DATETIME NOT NULL,
    exit_time DATETIME NULL,
    status ENUM('ACTIVE', 'CLOSED', 'CANCELLED') DEFAULT 'ACTIVE',
    amount_paid DECIMAL(10,2) NULL,
    FOREIGN KEY (slot_id) REFERENCES slots(id)
);
```

#### `events_log`
```sql
CREATE TABLE events_log (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    ticket_id BIGINT NULL,
    camera_id INT NOT NULL,
    event_type ENUM('ENTRY_DETECTED', 'EXIT_DETECTED', 'SLOT_OCCUPIED', 'SLOT_FREED') NOT NULL,
    payload_json JSON,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ticket_id) REFERENCES tickets(id),
    FOREIGN KEY (camera_id) REFERENCES cameras(id)
);
```

---

## 📁 Project Structure

### Backend (FastAPI + MySQL)

```
parking-backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI entrypoint
│   ├── core/
│   │   ├── config.py           # Settings & DB URL
│   │   └── database.py         # DB engine & session
│   ├── models/                 # SQLAlchemy models
│   │   ├── floor.py
│   │   ├── slot.py
│   │   ├── camera.py
│   │   ├── ticket.py
│   │   └── event_log.py
│   ├── schemas/                # Pydantic schemas
│   │   ├── ticket.py
│   │   ├── slot.py
│   │   └── entry_event.py
│   ├── services/
│   │   └── allocation_service.py
│   └── routers/
│       └── v1/
│           ├── entry.py        # POST /api/v1/entry-events
│           ├── occupancy.py    # POST /api/v1/slot-occupancy
│           ├── slots.py        # GET /api/v1/slots
│           └── health.py
├── alembic/                    # DB migrations
├── requirements.txt
└── .env
```

### CV Service (Python + YOLOv8)

```
parking-cv-service/
├── src/
│   ├── config.py               # Camera URLs, backend URL
│   ├── models/
│   │   ├── vehicle_detector.py
│   │   ├── plate_detector.py
│   │   └── plate_ocr.py
│   ├── pipelines/
│   │   ├── entry_pipeline.py
│   │   └── indoor_pipeline.py
│   ├── clients/
│   │   └── backend_client.py
│   ├── main_entry.py
│   └── main_indoor.py
├── requirements.txt
└── README.md
```

### Dashboard (React + TypeScript)

```
parking-dashboard/
├── src/
│   ├── components/
│   │   ├── SlotGrid.tsx
│   │   ├── CameraFeed.tsx
│   │   └── RevenueChart.tsx
│   ├── pages/
│   │   ├── Dashboard.tsx
│   │   └── Reports.tsx
│   ├── services/
│   │   └── api.ts
│   ├── App.tsx
│   └── main.tsx
├── package.json
└── vite.config.ts
```

---

## 🚀 Installation & Setup

### Prerequisites

- Python 3.8+
- Node.js 16+
- MySQL 8.0+
- Docker (optional)
- GPU with CUDA (recommended for CV service)

### Backend Setup

```bash
# Clone repository
git clone <repo-url>
cd parking-backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup database
# Create .env file with DB credentials
echo "DATABASE_URL=mysql://user:pass@localhost/parking_db" > .env

# Run migrations
alembic upgrade head

# Seed initial data
python scripts/seed_data.py

# Start server
uvicorn app.main:app --reload --port 8000
```

### CV Service Setup

```bash
cd parking-cv-service

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Download YOLOv8 models
python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"

# Configure cameras in src/config.py
# Update RTSP URLs and backend API endpoint

# Start entry pipeline
python src/main_entry.py

# Start indoor monitoring (separate terminal)
python src/main_indoor.py
```

### Dashboard Setup

```bash
cd parking-dashboard

# Install dependencies
npm install

# Configure API endpoint in .env
echo "VITE_API_URL=http://localhost:8000" > .env

# Start development server
npm run dev
```

---

## 🔌 API Endpoints

### Entry Management

```http
POST /api/v1/entry-events
Content-Type: application/json

{
  "camera_code": "ENTRY_1",
  "plate_number": "TN09AB1234",
  "vehicle_type": "CAR",
  "confidence": 0.93,
  "captured_at": "2025-12-12T03:58:00Z"
}
```

**Response:**
```json
{
  "ticket_id": 12345,
  "slot_assigned": "A-C-05",
  "entry_time": "2025-12-12T03:58:00Z",
  "message": "Gate opened"
}
```

### Slot Occupancy

```http
POST /api/v1/slot-occupancy
Content-Type: application/json

{
  "camera_code": "A_CAR_01",
  "floor": "A",
  "detections": [...]
}
```

### Get Slots

```http
GET /api/v1/slots?floor=A&status=OCCUPIED
```

### Exit Vehicle

```http
POST /api/v1/exit-events
Content-Type: application/json

{
  "camera_code": "EXIT_1",
  "plate_number": "TN09AB1234"
}
```

---

## 🗺 Development Roadmap

### Phase 1 (v1) - MVP ✅
- [x] Vehicle entry with plate + type detection
- [x] Automatic slot assignment
- [x] Indoor slot occupancy detection
- [x] Database schema & backend API
- [x] Basic receipt generation

### Phase 2 (v2) - Advanced Features
- [ ] Misparking detection + fine flag
- [ ] Exit + billing based on time
- [ ] Payment gateway integration
- [ ] Admin dashboard with occupancy view
- [ ] Live camera feed integration

### Phase 3 (v3) - Analytics & Optimization
- [ ] Revenue analytics & reports
- [ ] Historical data visualization
- [ ] Performance optimization
- [ ] Multi-tenancy support

### Phase 4 (v4) - AI Enhancements
- [ ] Traffic pattern forecasting
- [ ] Peak hour prediction
- [ ] Dynamic pricing
- [ ] Vehicle behavior analysis

---

## 📊 Expected Accuracy

| Task | Expected Accuracy |
|------|-------------------|
| Vehicle Detection | 95–97% |
| Vehicle Type Classification | 94–96% |
| License Plate Detection | 96–98% |
| OCR Reading | 90–95% |
| Slot Occupancy | 96–99% |

### Performance Characteristics

- **Processing Speed**: 15-30 FPS (YOLOv8n)
- **Latency**: < 200ms per frame
- **Concurrent Cameras**: 10+ streams
- **Database Response**: < 50ms

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Code Style

- **Python**: Follow PEP 8, use `black` formatter
- **TypeScript**: ESLint + Prettier
- **Commits**: Conventional Commits format

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👥 Team

- **Project Lead**: [Your Name]
- **CV Engineer**: [Name]
- **Backend Developer**: [Name]
- **Frontend Developer**: [Name]

---

## 📞 Contact

For questions or support:
- Email: support@parkingsystem.com
- Issues: [GitHub Issues](https://github.com/yourrepo/issues)

---

## 🙏 Acknowledgments

- [Ultralytics YOLOv8](https://github.com/ultralytics/ultralytics)
- [FastAPI](https://fastapi.tiangolo.com/)
- [EasyOCR](https://github.com/JaidedAI/EasyOCR)
- [Material-UI](https://mui.com/)

---

**Built with ❤️ for smarter parking solutions**
