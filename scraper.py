import time
from typing import List, Dict, Any
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class MoodleScraper:
    """A class to handle Moodle login and calendar scraping using Selenium."""

    def __init__(self, username: str, password: str, login_url: str, calendar_url: str):
        self.username = username
        self.password = password
        self.login_url = login_url
        self.calendar_url = calendar_url

        # Setup Selenium WebDriver
        service = Service()  # Assumes chromedriver is in the same folder
        options = webdriver.ChromeOptions()
        # options.add_argument('--headless')  # Uncomment to run without opening a browser window
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        self.driver = webdriver.Chrome(service=service, options=options)
        print("✅ Selenium WebDriver initialized.")

    def login(self) -> bool:
        print("Attempting to log in using Selenium...")
        try:
            self.driver.get(self.login_url)
            # Find username/password fields and login button, then interact
            self.driver.find_element(By.ID, 'username').send_keys(self.username)
            self.driver.find_element(By.ID, 'password').send_keys(self.password)
            self.driver.find_element(By.ID, 'loginbtn').click()

            # Wait until the dashboard page loads by checking for the user menu
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.ID, 'user-menu-toggle'))
            )
            print("✅ Login successful!")
            return True
        except Exception as e:
            print(f"❌ An error occurred during Selenium login: {e}")
            self.driver.quit()
            return False

    def get_calendar_events_with_details(self) -> List[Dict[str, Any]]:
        """
        Fetches calendar, clicks each event, and scrapes details from the pop-up modal.
        """
        try:
            print(f"Navigating to calendar: {self.calendar_url}")
            self.driver.get(self.calendar_url)

            # Wait for the calendar to be present
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'calendarmonth'))
            )
            time.sleep(2)  # Extra wait for all events to render

            event_links = self.driver.find_elements(By.CSS_SELECTOR,
                                                    'li[data-region="event-item"] a[data-action="view-event"]')
            num_events = len(event_links)
            print(f"Found {num_events} total events. Fetching details one by one...")

            all_events_data = []

            for i in range(num_events):
                # We must re-find the links each time because the page can change after a modal closes
                events_to_click = self.driver.find_elements(By.CSS_SELECTOR,
                                                            'li[data-region="event-item"] a[data-action="view-event"]')
                link = events_to_click[i]
                event_name = link.text
                print(f"  ({i + 1}/{num_events}) Clicking: '{event_name}'")

                link.click()

                # Wait for the modal pop-up to be visible
                modal_wait = WebDriverWait(self.driver, 10)
                modal_dialog = modal_wait.until(
                    EC.visibility_of_element_located((By.CSS_SELECTOR, 'div.modal-dialog[data-region="modal"]'))
                )

                # Get the HTML of the modal and parse with BeautifulSoup
                modal_html = modal_dialog.get_attribute('innerHTML')
                soup = BeautifulSoup(modal_html, 'html.parser')

                # --- Scrape data from the modal using the correct selectors ---
                details = {}
                clock_icon = soup.find('i', class_='fa-clock')
                if clock_icon:
                    date_div = clock_icon.find_parent('div', class_='row').find('div', class_='col-11')
                    details['full_due_date'] = date_div.get_text(strip=True, separator=' ') if date_div else 'N/A'

                course_icon = soup.find('i', class_='fa-graduation-cap')
                if course_icon:
                    course_div = course_icon.find_parent('div', class_='row').find('div', class_='col-11')
                    details['course_name'] = course_div.get_text(strip=True) if course_div else 'N/A'

                # Add other details
                details['name'] = event_name
                details['url'] = link.get_attribute('href')

                all_events_data.append(details)

                # Close the modal
                close_button = self.driver.find_element(By.CSS_SELECTOR, 'button.btn-close[data-action="hide"]')
                close_button.click()

                # Wait for modal to disappear
                modal_wait.until(EC.invisibility_of_element(modal_dialog))
                time.sleep(1)  # Small delay for stability

            print(f"✅ Finished scraping details for {len(all_events_data)} events.")
            self.driver.quit()
            return all_events_data

        except Exception as e:
            print(f"❌ An error occurred during scraping: {e}")
            self.driver.quit()
            return []