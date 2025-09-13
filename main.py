import configparser
from scraper import MoodleScraper


def main():
    """
    Main function to run the Moodle agent using Selenium.
    """
    config = configparser.ConfigParser()
    config.read('config.ini')

    try:
        username = config.get('moodle', 'username')
        password = config.get('moodle', 'password')
        login_url = config.get('moodle', 'login_url')
        calendar_url = config.get('moodle', 'calendar_url')
    except (configparser.NoSectionError, configparser.NoOptionError) as e:
        print(f"Error reading from config.ini: {e}")
        return

    if 'YOUR_USERNAME_HERE' in username or 'YOUR_PASSWORD_HERE' in password:
        print("Error: Please replace the placeholder credentials in config.ini.")
        return

    # Initialize and run the scraper
    scraper = MoodleScraper(username, password, login_url, calendar_url)

    if scraper.login():
        events = scraper.get_calendar_events_with_details()

        if events:
            print("\n--- ✅ Your Final Detailed Moodle Summary ---")
            for event in events:
                print(f"  -------------------------------------------")
                print(f"  📌 Event:     {event.get('name', 'N/A')}")
                print(f"  🎓 Course:    {event.get('course_name', 'N/A')}")
                print(f"  🕒 Due:       {event.get('full_due_date', 'N/A')}")
                print(f"  🔗 Link:      {event.get('url', 'N/A')}")


if __name__ == "__main__":
    main()