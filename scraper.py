import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any
import time


class MoodleScraper:
    """A class to handle Moodle login and calendar scraping."""

    def __init__(self, username: str, password: str, login_url: str, calendar_url: str):
        self.username = username
        self.password = password
        self.login_url = login_url
        self.calendar_url = calendar_url
        self.session = requests.Session()
        self.course_name_cache = {}

    def login(self) -> bool:
        # This method is working correctly and remains unchanged.
        print("Attempting to log in...")
        try:
            login_page_response = self.session.get(self.login_url, timeout=15)
            login_page_response.raise_for_status()
            soup = BeautifulSoup(login_page_response.text, 'html.parser')
            logintoken = soup.find('input', {'name': 'logintoken'})
            if not logintoken: return False
            logintoken_value = logintoken.get('value')
            print(f"✅ Found logintoken.")
            payload = {'username': self.username, 'password': self.password, 'logintoken': logintoken_value}
            login_response = self.session.post(self.login_url, data=payload, timeout=15)
            login_response.raise_for_status()
            if 'login/logout.php' in login_response.text:
                print("✅ Login successful!")
                return True
            else:
                print("❌ Login failed. Please check your credentials in config.ini.")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ An error occurred during login: {e}")
            return False

    # FINAL CORRECTED METHOD
    def _scrape_event_details(self, event_url: str) -> Dict[str, str]:
        """
        Visits a single event URL and scrapes additional details robustly.
        """
        # FIX #1: Added 'event_type' back to prevent the KeyError
        details = {
            'full_due_date': 'N/A',
            'course_name': 'N/A',
            'description': 'N/A',
            'event_type': 'Course Event'  # Set a default value
        }
        try:
            response = self.session.get(event_url, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            # --- 1. Get Full Course Name (with Caching) --- (This part works well)
            nav_breadcrumb = soup.find('nav', {'aria-label': 'Navigation bar'})
            if nav_breadcrumb:
                breadcrumb_links = nav_breadcrumb.find_all('a')
                if len(breadcrumb_links) > 1:
                    course_link_tag = breadcrumb_links[-2]
                    course_url = course_link_tag['href']
                    if course_url in self.course_name_cache:
                        details['course_name'] = self.course_name_cache[course_url]
                    else:
                        print(f"      -> First time seeing this course. Fetching full name...")
                        course_page_res = self.session.get(course_url, timeout=15)
                        course_soup = BeautifulSoup(course_page_res.text, 'html.parser')
                        course_header = course_soup.find('div', class_='page-header-headings')
                        if course_header and course_header.find('h1'):
                            full_name = course_header.find('h1').get_text(strip=True)
                            details['course_name'] = full_name
                            self.course_name_cache[course_url] = full_name

            # --- 2. Get Full Due Date (FIX #2: More Robust Method) ---
            # Search for the table containing submission info by looking for the "Submission status" header
            submission_status_header = soup.find('th', string=lambda text: text and 'submission status' in text.lower())
            if submission_status_header:
                submission_table = submission_status_header.find_parent('table')
                if submission_table:
                    due_date_header = submission_table.find('th',
                                                            string=lambda text: text and 'due date' in text.lower())
                    if due_date_header:
                        date_cell = due_date_header.find_next_sibling('td')
                        if date_cell:
                            details['full_due_date'] = date_cell.get_text(strip=True)

            # --- 3. Get Activity Description/Title (This part works well) ---
            main_content = soup.find('div', {'role': 'main'})
            if main_content and main_content.find('h2'):
                details['description'] = main_content.find('h2').get_text(strip=True)

            # Add a generic link back to the event page
            details['submission_link'] = event_url

            return details

        except Exception as e:
            print(f"      -> Warning: An error occurred scraping details for {event_url}. Error: {e}")
            return details

    def get_calendar_events(self) -> List[Dict[str, Any]]:
        # This method's logic remains unchanged.
        print(f"Fetching calendar data from: {self.calendar_url}")
        try:
            calendar_response = self.session.get(self.calendar_url, timeout=15)
            calendar_response.raise_for_status()
            soup = BeautifulSoup(calendar_response.text, 'html.parser')
            month_header = soup.find('h2', class_='current')
            current_month_year = month_header.get_text(strip=True) if month_header else "Unknown Month"
            upcoming_events = []
            calendar_table = soup.find('table', class_='calendarmonth')
            if not calendar_table: return []
            days_with_events = calendar_table.find_all('td', class_='hasevent')
            all_event_items = []
            for day_cell in days_with_events:
                day_number = day_cell.get('data-day')
                date_str = f"{current_month_year}, Day {day_number}"
                events_on_day = day_cell.find_all('li', {'data-region': 'event-item'})
                for event_item in events_on_day:
                    all_event_items.append({'date_str': date_str, 'item': event_item})
            print(f"Found {len(all_event_items)} total events. Fetching details...")
            for idx, event_info in enumerate(all_event_items):
                event_item = event_info['item']
                date_str = event_info['date_str']
                event_link_tag = event_item.find('a', {'data-action': 'view-event'})
                if event_link_tag:
                    event_name = event_link_tag.find('span', class_='eventname').get_text(strip=True)
                    event_url = event_link_tag['href']
                    print(f"  ({idx + 1}/{len(all_event_items)}) Scraping: '{event_name}'")
                    details = self._scrape_event_details(event_url)
                    upcoming_events.append({'date': date_str, 'name': event_name, 'url': event_url, **details})
                    time.sleep(0.5)
            print(f"✅ Finished scraping details for {len(upcoming_events)} events.")
            return upcoming_events
        except Exception as e:
            print(f"❌ An error occurred during the process. Details: {e}")
            return []