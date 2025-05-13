from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

class SalonBoardScraper:
    def __init__(self):
        self.base_url = "https://beauty.hotpepper.jp/"
        self.driver = None
        self.wait = None

    def _setup_driver(self):
        """Initialize the Selenium WebDriver with appropriate options."""
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 10)

    def login(self) -> bool:
        """Login to Salon Board."""
        try:
            self._setup_driver()
            self.driver.get(f"{self.base_url}login")
            
            # Wait for login form and input credentials
            username_field = self.wait.until(
                EC.presence_of_element_located((By.NAME, "username"))
            )
            password_field = self.driver.find_element(By.NAME, "password")
            
            username_field.send_keys(settings.SALON_BOARD_USERNAME)
            password_field.send_keys(settings.SALON_BOARD_PASSWORD)
            
            # Submit login form
            login_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            login_button.click()
            
            # Wait for successful login
            self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".dashboard"))
            )
            return True
            
        except TimeoutException:
            logger.error("Timeout while logging in to Salon Board")
            return False
        except Exception as e:
            logger.error(f"Error logging in to Salon Board: {str(e)}")
            return False

    def get_appointments(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Get appointments from Salon Board for the specified date range."""
        try:
            if not self.driver:
                if not self.login():
                    return []

            # Navigate to appointments page
            self.driver.get(f"{self.base_url}appointments")
            
            # Wait for appointments to load
            self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".appointment-list"))
            )
            
            # Parse appointments
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            appointments = []
            
            for appointment in soup.select(".appointment-item"):
                try:
                    appointment_data = {
                        'external_id': appointment.get('data-appointment-id'),
                        'customer_name': appointment.select_one('.customer-name').text.strip(),
                        'start_time': datetime.strptime(
                            appointment.select_one('.start-time').text.strip(),
                            '%Y-%m-%d %H:%M'
                        ),
                        'end_time': datetime.strptime(
                            appointment.select_one('.end-time').text.strip(),
                            '%Y-%m-%d %H:%M'
                        ),
                        'service_name': appointment.select_one('.service-name').text.strip(),
                        'status': appointment.select_one('.status').text.strip().lower(),
                        'customer_phone': appointment.select_one('.customer-phone').text.strip(),
                        'customer_email': appointment.select_one('.customer-email').text.strip(),
                    }
                    
                    # Filter appointments within date range
                    if start_date <= appointment_data['start_time'] <= end_date:
                        appointments.append(appointment_data)
                        
                except Exception as e:
                    logger.error(f"Error parsing appointment: {str(e)}")
                    continue
                    
            return appointments
            
        except Exception as e:
            logger.error(f"Error getting appointments from Salon Board: {str(e)}")
            return []

    def update_appointment_availability(self, start_time: datetime, end_time: datetime, is_available: bool) -> bool:
        """Update appointment availability in Salon Board."""
        try:
            if not self.driver:
                if not self.login():
                    return False

            # Navigate to availability settings
            self.driver.get(f"{self.base_url}availability")
            
            # Wait for calendar to load
            self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".calendar"))
            )
            
            # Find and click the time slot
            time_slot = self.driver.find_element(
                By.CSS_SELECTOR,
                f".time-slot[data-time='{start_time.strftime('%Y-%m-%d %H:%M')}']"
            )
            time_slot.click()
            
            # Update availability
            availability_toggle = self.driver.find_element(By.CSS_SELECTOR, ".availability-toggle")
            current_state = availability_toggle.get_attribute("data-available")
            
            if (current_state == "true" and not is_available) or \
               (current_state == "false" and is_available):
                availability_toggle.click()
                
            # Save changes
            save_button = self.driver.find_element(By.CSS_SELECTOR, "button.save-changes")
            save_button.click()
            
            # Wait for confirmation
            self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".success-message"))
            )
            return True
            
        except Exception as e:
            logger.error(f"Error updating appointment availability: {str(e)}")
            return False

    def close(self):
        """Close the WebDriver."""
        if self.driver:
            self.driver.quit()
            self.driver = None 