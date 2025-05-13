from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import logging
from typing import List, Optional

from app.core.config import settings
from app.db.models import Appointment, SyncLog, AppointmentSource
from app.services.sync_service import SyncService
from app.db.database import get_db, init_db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database
init_db()

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    logger.info("Starting up application...")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown."""
    logger.info("Shutting down application...")

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Welcome to Hot Pepper Beauty Integration API"}

@app.post(f"{settings.API_V1_STR}/sync")
async def sync_appointments(
    background_tasks: BackgroundTasks,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    """Trigger synchronization between Salon Board and Google Calendar."""
    try:
        if not start_date:
            start_date = datetime.now()
        if not end_date:
            end_date = start_date + timedelta(days=30)

        sync_service = SyncService(db)
        
        # Run sync in background
        background_tasks.add_task(
            sync_service.sync_appointments,
            start_date,
            end_date
        )
        
        return {"message": "Synchronization started", "start_date": start_date, "end_date": end_date}

    except Exception as e:
        logger.error(f"Error starting synchronization: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get(f"{settings.API_V1_STR}/appointments")
async def get_appointments(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    source: Optional[AppointmentSource] = None,
    db: Session = Depends(get_db)
):
    """Get appointments from the database."""
    try:
        query = db.query(Appointment)
        
        if start_date:
            query = query.filter(Appointment.start_time >= start_date)
        if end_date:
            query = query.filter(Appointment.end_time <= end_date)
        if source:
            query = query.filter(Appointment.source == source)
            
        appointments = query.all()
        return appointments

    except Exception as e:
        logger.error(f"Error getting appointments: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get(f"{settings.API_V1_STR}/sync-logs")
async def get_sync_logs(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    source: Optional[AppointmentSource] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get synchronization logs."""
    try:
        query = db.query(SyncLog)
        
        if start_date:
            query = query.filter(SyncLog.created_at >= start_date)
        if end_date:
            query = query.filter(SyncLog.created_at <= end_date)
        if source:
            query = query.filter(SyncLog.source == source)
        if status:
            query = query.filter(SyncLog.status == status)
            
        logs = query.order_by(SyncLog.created_at.desc()).all()
        return logs

    except Exception as e:
        logger.error(f"Error getting sync logs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get(f"{settings.API_V1_STR}/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"} 