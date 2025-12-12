from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.database import get_db, engine
from app.core.config import settings
from app.models.camera import Camera
from datetime import datetime
from typing import Dict, Any
import platform
import psutil
import subprocess
import os

router = APIRouter()

@router.get("/health", response_model=Dict[str, Any])
async def health_check():
    """
    Basic health check endpoint.
    Returns API status and basic system information.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "Parking Management API",
        "version": "1.0.0",
        "environment": os.getenv("ENVIRONMENT", "development")
    }

@router.get("/health/detailed", response_model=Dict[str, Any])
async def detailed_health_check(db: Session = Depends(get_db)):
    """
    Detailed health check including database, system resources, and external dependencies.
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "Parking Management API",
        "version": "1.0.0",
        "checks": {}
    }
    
    # Database health check
    try:
        db.execute(text("SELECT 1"))
        health_status["checks"]["database"] = {
            "status": "healthy",
            "message": "Database connection successful",
            "database_url": settings.DATABASE_URL.split("://")[0] + "://[hidden]"
        }
    except Exception as e:
        health_status["checks"]["database"] = {
            "status": "unhealthy",
            "message": f"Database connection failed: {str(e)}"
        }
        health_status["status"] = "unhealthy"
    
    # System resources check
    try:
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        health_status["checks"]["system"] = {
            "status": "healthy",
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": memory.percent,
            "memory_available_gb": round(memory.available / (1024**3), 2),
            "disk_percent": disk.percent,
            "disk_free_gb": round(disk.free / (1024**3), 2),
            "platform": platform.system(),
            "python_version": platform.python_version()
        }
        
        # Check if resources are critically low
        if memory.percent > 90 or disk.percent > 90:
            health_status["checks"]["system"]["status"] = "warning"
            health_status["checks"]["system"]["message"] = "High resource usage detected"
            
    except Exception as e:
        health_status["checks"]["system"] = {
            "status": "unhealthy",
            "message": f"System check failed: {str(e)}"
        }
        health_status["status"] = "unhealthy"
    
    # Camera connectivity check
    try:
        cameras = db.query(Camera).filter(Camera.is_active == True).all()
        camera_stats = {
            "total_cameras": len(cameras),
            "online_cameras": 0,
            "offline_cameras": 0
        }
        
        for camera in cameras:
            try:
                # Simple ping check (simplified for demo)
                response = subprocess.run(
                    ["ping", "-n", "1", "-w", "1000", camera.camera_ip] if platform.system() == "Windows"
                    else ["ping", "-c", "1", "-W", "1", camera.camera_ip],
                    capture_output=True, text=True, timeout=2
                )
                if response.returncode == 0:
                    camera.is_online = True
                    camera.last_ping = datetime.utcnow()
                    camera_stats["online_cameras"] += 1
                else:
                    camera.is_online = False
                    camera_stats["offline_cameras"] += 1
            except:
                camera.is_online = False
                camera_stats["offline_cameras"] += 1
        
        db.commit()
        
        camera_health_status = "healthy"
        if camera_stats["offline_cameras"] > 0:
            camera_health_status = "warning" if camera_stats["offline_cameras"] < camera_stats["total_cameras"] else "unhealthy"
        
        health_status["checks"]["cameras"] = {
            "status": camera_health_status,
            **camera_stats
        }
        
        if camera_health_status == "unhealthy":
            health_status["status"] = "unhealthy"
        elif camera_health_status == "warning" and health_status["status"] != "unhealthy":
            health_status["status"] = "warning"
            
    except Exception as e:
        health_status["checks"]["cameras"] = {
            "status": "unhealthy",
            "message": f"Camera check failed: {str(e)}"
        }
        health_status["status"] = "unhealthy"
    
    return health_status

@router.get("/health/database", response_model=Dict[str, Any])
async def database_health(db: Session = Depends(get_db)):
    """
    Specific database health check with connection pool and query performance info.
    """
    try:
        # Test basic connectivity
        start_time = datetime.utcnow()
        db.execute(text("SELECT 1"))
        query_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        # Get database statistics
        stats = {}
        try:
            # SQLite specific checks
            if "sqlite" in settings.DATABASE_URL:
                result = db.execute(text("PRAGMA database_list")).fetchall()
                stats["databases"] = len(result)
                
                result = db.execute(text("PRAGMA table_info(slots)")).fetchall()
                stats["tables_accessible"] = True
            else:
                # Generic SQL checks
                stats["connection_pool"] = {
                    "pool_size": engine.pool.size(),
                    "connections_checked_in": engine.pool.checkedin(),
                    "connections_checked_out": engine.pool.checkedout()
                }
        except Exception as e:
            stats["error"] = str(e)
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "database_type": settings.DATABASE_URL.split("://")[0],
            "query_response_time_ms": round(query_time, 2),
            "statistics": stats
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }

@router.get("/health/cameras", response_model=Dict[str, Any])
async def cameras_health(db: Session = Depends(get_db)):
    """
    Check connectivity and status of all registered cameras.
    """
    try:
        cameras = db.query(Camera).all()
        camera_details = []
        
        for camera in cameras:
            camera_info = {
                "id": camera.id,
                "name": camera.camera_name,
                "ip": camera.camera_ip,
                "floor_id": camera.floor_id,
                "is_active": camera.is_active,
                "is_online": camera.is_online,
                "last_ping": camera.last_ping.isoformat() if camera.last_ping else None,
                "type": camera.camera_type
            }
            camera_details.append(camera_info)
        
        total_cameras = len(cameras)
        active_cameras = len([c for c in cameras if c.is_active])
        online_cameras = len([c for c in cameras if c.is_online])
        
        overall_status = "healthy"
        if online_cameras < active_cameras:
            overall_status = "warning" if online_cameras > 0 else "critical"
        
        return {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "summary": {
                "total_cameras": total_cameras,
                "active_cameras": active_cameras,
                "online_cameras": online_cameras,
                "offline_cameras": active_cameras - online_cameras
            },
            "cameras": camera_details
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }

@router.get("/health/ping", response_model=Dict[str, str])
async def ping():
    """
    Simple ping endpoint for load balancers and monitoring.
    """
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat()
    }