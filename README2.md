# 🚗 Visual Park - AI-Powered Parking & Traffic Intelligence System

**Real-time Smart Parking Automation + Vehicle Intelligence + Traffic Analytics**

An end-to-end intelligent parking and traffic management platform combining Computer Vision, AI Agents, and IoT for automated vehicle entry, parking allocation, tracking, and congestion prediction.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [System Architecture](#system-architecture)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Quick Start](#quick-start)
- [API Documentation](#api-documentation)
- [Use Cases](#use-cases)
- [Deployment](#deployment)
- [Contributing](#contributing)
- [License](#license)

---

## 🎯 Overview

Visual Park is a comprehensive solution that eliminates manual parking management through:

- **Automatic Number Plate Recognition (ANPR/LPR)** - Real-time vehicle identification
- **AI-Powered Entry Agents** - LangChain-based autonomous decision making
- **Smart Slot Allocation** - Dynamic parking assignment with real-time updates
- **Traffic Analytics** - Queue measurement, congestion prediction, and flow analysis
- **OTP-Based User Verification** - Privacy-preserving temporary user mapping
- **IoT Gate Integration** - Automated barrier control

**No pre-registration required** - The system handles unknown vehicles through secure OTP-based mobile number claiming.

---

## ✨ Key Features

### 🚀 Core Capabilities

- **Real-Time Vehicle Detection** - YOLOv8/v11 powered detection and tracking
- **License Plate Recognition** - EasyOCR + custom models for accurate plate extraction
- **Vehicle Classification** - Categorizes vehicles (Car, Bike, Truck, Bus, Auto, Van)
- **Smart Parking Allocation** - Assigns optimal slots based on vehicle type and availability
- **Live Dashboard** - React-based real-time monitoring with SSE updates
- **Automated Billing** - Time-based calculation with UPI/payment integration
- **Queue Analytics** - Lane-wise queue length, waiting time, and congestion metrics
- **Congestion Prediction** - LSTM/Transformer models for traffic forecasting

### 🤖 AI Agent Ecosystem

1. **Entry Agent** - Handles vehicle entry, LPR, slot assignment, gate control
2. **Monitoring Agent** - Tracks slot occupancy, detects violations, sends alerts
3. **Billing Agent** - Manages exit verification, payment processing, session closure
4. **Admin Assistant** - Provides insights, analytics, and RAG-based query support

### 🔒 Security & Privacy

- OTP-based temporary user mapping (no permanent database storage)
- Secure gate controller commands (HMAC/JWT signing)
- API authentication and rate limiting
- GDPR/privacy-compliant data handling

---

## 🏗️ System Architecture

```
┌─────────────────┐
│  Camera Feeds   │
│   (CV Service)  │
└────────┬────────┘
         │ POST /event/entry
         ▼
┌─────────────────────────────┐
│    FastAPI Backend          │
│  ┌─────────────────────┐   │
│  │ Entry Event Handler │   │
│  └──────────┬──────────┘   │
│             │               │
│  ┌──────────▼──────────┐   │
│  │  Slot Allocator     │   │
│  └──────────┬──────────┘   │
│             │               │
│  ┌──────────▼──────────┐   │
│  │  DB (SQLite/MySQL)  │   │
│  └─────────────────────┘   │
└─────────┬───────────────────┘
          │
          ├─────────────────────────────┐
          │                             │
          ▼                             ▼
┌─────────────────────┐     ┌──────────────────────┐
│   Entry Agent       │     │   SSE Event Stream   │
│   (LangChain + LLM) │     │   /events            │
└─────────┬───────────┘     └──────────┬───────────┘
          │                             │
          ▼                             ▼
┌─────────────────────┐     ┌──────────────────────┐
│  Gate Controller    │     │  React Dashboard     │
│  (IoT/HTTP API)     │     │  (Real-time UI)      │
└─────────────────────┘     └──────────────────────┘
```

### Data Flow

1. **Vehicle Detection** → Camera captures vehicle → CV service runs YOLOv8 + OCR
2. **Event Creation** → POST to `/event/entry` with image, bbox, plate text
3. **Backend Processing** → Validates, assigns slot, persists to DB
4. **Agent Invocation** → Entry Agent processes with LangChain tools
5. **Gate Control** → Agent decides (open/deny) → IoT controller executes
6. **Real-Time Updates** → SSE broadcasts events → Dashboard updates instantly

---

## 🛠️ Technology Stack

### Backend
- **FastAPI** - High-performance async web framework
- **SQLAlchemy 2.0** - ORM with SQLite/MySQL support
- **Pydantic V2** - Data validation and serialization
- **SSE** - Server-Sent Events for real-time updates

### AI & Computer Vision
- **YOLOv8/v11** - Object detection and vehicle classification
- **EasyOCR** - License plate text recognition
- **LangChain** - AI agent orchestration
- **OpenAI/LLM** - Reasoning and decision making
- **DeepSORT/ByteTrack** - Multi-object tracking
- **LSTM/ConvLSTM** - Traffic prediction models

### Frontend
- **React 18** - Modern UI framework
- **Vite** - Fast build tool
- **TanStack Query** - Server state management
- **SSE Client** - Real-time event consumption

### Infrastructure
- **Docker** - Containerization
- **Docker Compose** - Multi-service orchestration
- **MySQL/PostgreSQL** - Production database
- **Redis** - Caching and pub/sub (optional)

---

## 📁 Project Structure

```
visual-park/
├── detect vehicle/              # CV detection & tracking module
│   ├── main.py                 # Main detection script
│   ├── vehicle_tracker.py      # Multi-object tracking
│   ├── code/
│   │   ├── realtime_camera.py  # Live camera processing
│   │   └── samplepredict.py    # Model testing
│   ├── models/                 # Trained YOLO models
│   └── dataset_cls/            # Training datasets
│
├── mall/                        # Parking system implementation
│   ├── frontend/               # React dashboard
│   │   ├── index.html
│   │   ├── pages/
│   │   │   ├── dashboard.html
│   │   │   ├── camera.html
│   │   │   └── data.html
│   │   ├── js/
│   │   └── css/
│   ├── model/                  # ML models
│   └── receipts/               # Billing module
│
├── documatation/               # Detailed reports & docs
│   ├── Report 1.txt           # System overview
│   ├── Report 2.txt           # Technical implementation
│   └── README.md              # Documentation index
│
└── README.md                   # This file
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker (optional)
- CUDA GPU (optional, for faster inference)

### Installation

#### 1. Clone the Repository

```bash
git clone https://github.com/your-org/visual-park.git
cd visual-park
```

#### 2. Backend Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Initialize database
python seed_sqlite.py

# Start backend server
uvicorn app.main:app --reload --port 8000
```

#### 3. Entry Agent Setup

```bash
cd entry_agent
pip install -r requirements.txt

# Set environment variables
export OPENAI_API_KEY="your-key-here"

# Start agent service
uvicorn entry_agent:app --reload --port 8001
```

#### 4. Frontend Setup

```bash
cd mall/frontend
npm install
npm run dev
# Open http://localhost:5173
```

#### 5. CV Service (Optional)

```bash
cd "detect vehicle"
python main.py --camera 0  # Use webcam
# OR
python main.py --video path/to/video.mp4
```

### Docker Deployment (Recommended)

```bash
docker-compose up -d
```

Services will be available at:
- Backend: `http://localhost:8000`
- Entry Agent: `http://localhost:8001`
- Frontend: `http://localhost:5173`

---

## 📚 API Documentation

### Core Endpoints

#### Entry Events

```bash
# Create entry event
POST /event/entry
Content-Type: application/json

{
  "camera_id": "cam_1",
  "image_url": "https://example.com/frame.jpg",
  "plate_text": "KA01AB1234",
  "slot_id": "A-C-01",
  "timestamp": "2025-12-12T10:22:01Z"
}
```

#### Slot Management

```bash
# Get available slots
GET /api/v1/slots/available

# Update slot status
PUT /api/v1/slots/{slot_id}
Content-Type: application/json

{
  "status": "OCCUPIED",
  "plate_number": "KA01AB1234"
}
```

#### Real-Time Events (SSE)

```bash
# Subscribe to live updates
GET /events
Accept: text/event-stream
```

Event types:
- `slot_update` - Slot occupancy changes
- `entry` - New vehicle entry
- `agent_decision` - AI agent actions
- `gate_action` - Gate open/close events

#### Agent Invocation

```bash
POST /api/v1/agent/invoke
Content-Type: application/json

{
  "image_url": "https://example.com/vehicle.jpg",
  "camera_id": "cam_1",
  "trace_id": "abc123"
}
```

### Interactive API Docs

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## 🎯 Use Cases

### 1. **Shopping Mall Parking**
- Automated entry/exit gates
- Real-time slot availability display
- Dynamic pricing based on duration
- Mobile app integration

### 2. **Toll Plaza Monitoring**
- Queue length measurement
- Lane performance scoring
- Congestion prediction and alerts
- FASTag integration

### 3. **Airport Pickup Zones**
- Illegal parking detection
- Vehicle movement tracking
- Automated overstay alerts

### 4. **Smart City Traffic**
- Intersection queue analytics
- Dynamic signal timing optimization
- Emergency vehicle detection

### 5. **Corporate Campuses**
- Employee parking management
- Visitor slot allocation
- Permit verification

---

## 🚢 Deployment

### Production Checklist

- [ ] Use managed database (MySQL/PostgreSQL)
- [ ] Set up Redis for caching and pub/sub
- [ ] Configure HTTPS with SSL certificates
- [ ] Implement API authentication (JWT/OAuth)
- [ ] Set up monitoring (Prometheus + Grafana)
- [ ] Configure logging (ELK stack)
- [ ] Enable auto-scaling for backend/agents
- [ ] Set up CI/CD pipeline
- [ ] Implement backup strategy
- [ ] Configure rate limiting

### Environment Variables

```bash
# Backend
DATABASE_URL=mysql://user:pass@host:3306/parking
REDIS_URL=redis://localhost:6379
SECRET_KEY=your-secret-key
ENVIRONMENT=production

# Entry Agent
OPENAI_API_KEY=sk-...
AGENT_TIMEOUT=4
MAX_WORKERS=10

# Frontend
VITE_API_URL=https://api.example.com
VITE_WS_URL=wss://api.example.com/events
```

---

## 🧪 Testing

```bash
# Run backend tests
pytest tests/ -v --cov

# Run CV mock events
python send_mock_events.py --count 100 --interval 0.5

# Test agent directly
curl -X POST http://localhost:8001/invoke \
  -H "Content-Type: application/json" \
  -d '{"image_url":"https://example.com/car.jpg","trace_id":"test1"}'
```

---

## 🔮 Future Enhancements

- [ ] Mobile app (React Native)
- [ ] Vehicle color/make recognition
- [ ] Automatic payment wallet integration
- [ ] Multi-tenant support
- [ ] Video playback and incident review
- [ ] Pollution/emission analytics
- [ ] Emergency vehicle priority corridors
- [ ] ML model A/B testing framework
- [ ] Multi-sensor fusion (radar/LiDAR)

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details

---

## 👥 Contributors

**Dharshan Kumar J.** - Lead Developer

---

## 📞 Support

For questions, issues, or feature requests:
- Create an issue on GitHub
- Email: support@visual-park.io
- Documentation: [Full Docs](./documatation/)

---

## 🙏 Acknowledgments

- YOLOv8/v11 by Ultralytics
- LangChain for AI orchestration
- FastAPI framework
- React and Vite teams

---

**Built with ❤️ for smarter cities and seamless parking experiences**
