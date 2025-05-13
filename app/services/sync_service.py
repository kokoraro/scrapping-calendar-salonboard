from datetime import datetime, timedelta
import logging
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from app.db.models import Appointment, SyncLog, AppointmentSource, AppointmentStatus
from app.scrapers.salon_board import SalonBoardScraper
from app.services.google_calendar import GoogleCalendarService

logger = logging.getLogger(__name__)

class SyncService:
    def __init__(self, db: Session):
        self.db = db
        self.salon_board = SalonBoardScraper()
        self.google_calendar = GoogleCalendarService()

    def sync_appointments(self, start_date: datetime, end_date: datetime) -> bool:
        """Synchronize appointments between Salon Board and Google Calendar."""
        try:
            # Get appointments from both systems
            salon_appointments = self.salon_board.get_appointments(start_date, end_date)
            google_events = self.google_calendar.get_events(start_date, end_date)

            # Sync Salon Board appointments to Google Calendar
            for appointment in salon_appointments:
                self._sync_salon_to_google(appointment)

            # Sync Google Calendar events to Salon Board
            for event in google_events:
                self._sync_google_to_salon(event)

            return True

        except Exception as e:
            logger.error(f"Error synchronizing appointments: {str(e)}")
            return False

    def _sync_salon_to_google(self, appointment: Dict) -> None:
        """Sync a Salon Board appointment to Google Calendar."""
        try:
            # Check if appointment already exists in database
            existing_appointment = self.db.query(Appointment).filter_by(
                external_id=appointment['external_id'],
                source=AppointmentSource.SALON_BOARD
            ).first()

            if not existing_appointment:
                # Create new appointment in database
                new_appointment = Appointment(
                    external_id=appointment['external_id'],
                    customer_name=appointment['customer_name'],
                    customer_phone=appointment.get('customer_phone'),
                    customer_email=appointment.get('customer_email'),
                    start_time=appointment['start_time'],
                    end_time=appointment['end_time'],
                    service_name=appointment['service_name'],
                    status=AppointmentStatus(appointment['status']),
                    source=AppointmentSource.SALON_BOARD
                )
                self.db.add(new_appointment)
                self.db.commit()

                # Create event in Google Calendar
                event_data = {
                    'summary': f"Appointment: {appointment['service_name']}",
                    'description': f"Customer: {appointment['customer_name']}\nPhone: {appointment.get('customer_phone', 'N/A')}",
                    'start_time': appointment['start_time'],
                    'end_time': appointment['end_time'],
                    'location': 'Salon',
                }
                google_event_id = self.google_calendar.create_event(event_data)

                if google_event_id:
                    # Update appointment with Google Calendar event ID
                    new_appointment.google_calendar_id = google_event_id
                    self.db.commit()

                    # Log successful sync
                    self._log_sync(new_appointment.id, AppointmentSource.SALON_BOARD, 'create', 'success')

        except Exception as e:
            logger.error(f"Error syncing Salon Board appointment to Google Calendar: {str(e)}")
            if existing_appointment:
                self._log_sync(existing_appointment.id, AppointmentSource.SALON_BOARD, 'create', 'failed', str(e))

    def _sync_google_to_salon(self, event: Dict) -> None:
        """Sync a Google Calendar event to Salon Board."""
        try:
            # Check if event already exists in database
            existing_appointment = self.db.query(Appointment).filter_by(
                external_id=event['external_id'],
                source=AppointmentSource.GOOGLE_CALENDAR
            ).first()

            if not existing_appointment:
                # Create new appointment in database
                new_appointment = Appointment(
                    external_id=event['external_id'],
                    customer_name=event['summary'],
                    customer_email=event.get('attendees', [None])[0],
                    start_time=event['start_time'],
                    end_time=event['end_time'],
                    service_name=event['summary'],
                    status=AppointmentStatus(event['status']),
                    source=AppointmentSource.GOOGLE_CALENDAR,
                    notes=event.get('description', '')
                )
                self.db.add(new_appointment)
                self.db.commit()

                # Update Salon Board availability
                success = self.salon_board.update_appointment_availability(
                    event['start_time'],
                    event['end_time'],
                    False  # Mark as unavailable
                )

                if success:
                    # Log successful sync
                    self._log_sync(new_appointment.id, AppointmentSource.GOOGLE_CALENDAR, 'create', 'success')

        except Exception as e:
            logger.error(f"Error syncing Google Calendar event to Salon Board: {str(e)}")
            if existing_appointment:
                self._log_sync(existing_appointment.id, AppointmentSource.GOOGLE_CALENDAR, 'create', 'failed', str(e))

    def _log_sync(self, appointment_id: int, source: AppointmentSource, action: str, status: str, error_message: Optional[str] = None) -> None:
        """Log synchronization activity."""
        try:
            sync_log = SyncLog(
                appointment_id=appointment_id,
                source=source,
                action=action,
                status=status,
                error_message=error_message
            )
            self.db.add(sync_log)
            self.db.commit()

        except Exception as e:
            logger.error(f"Error logging sync activity: {str(e)}")

    def cleanup(self):
        """Clean up resources."""
        self.salon_board.close() 