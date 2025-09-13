import configparser
from scraper import MoodleScraper


def main():
    """
    Main function to run the Moodle agent.
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

    scraper = MoodleScraper(username, password, login_url, calendar_url)

    if scraper.login():
        events = scraper.get_calendar_events()

        if events:
            print("\n--- ✅ Your Detailed Moodle Calendar Summary ---")
            current_date = None
            for event in events:
                # Group events by the day
                if event['date'] != current_date:
                    # FIX: Clean up the date string for printing
                    clean_date = event['date'].replace(', Day', '')
                    print(f"\n🗓️  {clean_date}")
                    current_date = event['date']

                # Print the detailed information
                print(f"  -------------------------------------------")
                print(f"  📌 Event:     {event['name']}")
                print(f"  🎓 Course:    {event['course_name']}")
                print(f"  🕒 Due:       {event['full_due_date']}")
                print(f"  ℹ️  Type:      {event['event_type']}")
                print(f"  📝 Details:   {event['description']}")
                print(f"  🔗 Link:      {event['url']}")  # Changed to use the main URL

        else:
            print("\nCould not find any events for the current month.")


if __name__ == "__main__":
    main()