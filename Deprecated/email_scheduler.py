import sqlite3
import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime, timedelta
import os
import schedule


class EmailScheduler:
    def __init__(self, db_path='story_tracker.db'):
        self.db_path = db_path

    def scrape_stories(self, state=None, limit=5):
        """Scrape stories from the Solutions Story Tracker website"""
        try:
            base_url = "https://storytracker.solutionsjournalism.org/"

            if state and state != 'All States':
                url = f"{base_url}?location={state.replace(' ', '+')}"
            else:
                url = base_url

            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }

            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            stories = []
            # Adjust these selectors based on actual website structure
            story_elements = soup.find_all('div', class_='story-item')[:limit]

            if not story_elements:
                story_elements = soup.find_all('a', href=True)[:limit]

            for element in story_elements:
                try:
                    title = element.get_text().strip()
                    link = element.get('href', '')

                    if link and not link.startswith('http'):
                        link = base_url.rstrip('/') + '/' + link.lstrip('/')

                    if title and link:
                        stories.append({
                            'title': title[:100] + '...' if len(title) > 100 else title,
                            'url': link
                        })
                except Exception as e:
                    continue

            return stories if stories else [
                {'title': 'Sample Story: Community Gardens Transform Urban Food Access',
                 'url': 'https://storytracker.solutionsjournalism.org/sample'}
            ]

        except Exception as e:
            print(f"Error scraping stories: {e}")
            return []

    def get_unsent_stories(self, user_email, stories):
        """Filter out stories that have already been sent to this user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT story_title, story_url FROM sent_stories 
            WHERE user_email = ?
        ''', (user_email,))

        sent_stories = {(row[0], row[1]) for row in cursor.fetchall()}
        conn.close()

        # Filter out already sent stories
        unsent_stories = []
        for story in stories:
            if (story['title'], story['url']) not in sent_stories:
                unsent_stories.append(story)

        return unsent_stories

    def mark_stories_as_sent(self, user_email, stories):
        """Mark stories as sent to avoid duplicates"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for story in stories:
            cursor.execute('''
                INSERT INTO sent_stories (user_email, story_title, story_url)
                VALUES (?, ?, ?)
            ''', (user_email, story['title'], story['url']))

        conn.commit()
        conn.close()

    def send_email_to_user(self, user):
        """Send email to a specific user"""
        email, state, frequency = user

        # Get fresh stories
        all_stories = self.scrape_stories(state, limit=10)

        # Filter out already sent stories
        new_stories = self.get_unsent_stories(email, all_stories)

        if not new_stories:
            print(f"No new stories for {email}")
            return

        # Limit to 5 stories per email
        stories_to_send = new_stories[:5]

        # Create email content
        subject = f"Your {frequency} Solutions Stories"
        if state != 'All States':
            subject += f" for {state}"

        email_content = f"""
Hello!

Here are your latest solutions journalism stories:

"""

        for i, story in enumerate(stories_to_send, 1):
            email_content += f"{i}. {story['title']}\n   Read more: {story['url']}\n\n"

        email_content += f"""
Best regards,
Solutions Story Tracker App

---
Frequency: {frequency}
State Filter: {state}
Delivered: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

        # Save to file (simulating email send)
        os.makedirs('../sent_emails', exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_email = email.replace('@', '_at_').replace('.', '_')
        filename = f"sent_emails/{frequency.lower()}_{safe_email}_{timestamp}.txt"

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"To: {email}\n")
                f.write(f"Subject: {subject}\n")
                f.write(f"Date: {datetime.now()}\n\n")
                f.write(email_content)

            # Mark stories as sent
            self.mark_stories_as_sent(email, stories_to_send)

            # Update last sent time
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE users SET last_sent = ? WHERE email = ?
            ''', (datetime.now(), email))
            conn.commit()
            conn.close()

            print(f"Email sent to {email}: {filename}")

        except Exception as e:
            print(f"Failed to send email to {email}: {e}")

    def send_daily_emails(self):
        """Send emails to users with daily frequency"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT email, state, frequency FROM users 
            WHERE frequency = 'Daily'
        ''')

        daily_users = cursor.fetchall()
        conn.close()

        print(f"Sending daily emails to {len(daily_users)} users...")
        for user in daily_users:
            self.send_email_to_user(user)

    def send_weekly_emails(self):
        """Send emails to users with weekly frequency"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Only send if it's been at least 6 days since last email
        cutoff_date = datetime.now() - timedelta(days=6)

        cursor.execute('''
            SELECT email, state, frequency FROM users 
            WHERE frequency = 'Weekly' 
            AND (last_sent IS NULL OR last_sent < ?)
        ''', (cutoff_date,))

        weekly_users = cursor.fetchall()
        conn.close()

        print(f"Sending weekly emails to {len(weekly_users)} users...")
        for user in weekly_users:
            self.send_email_to_user(user)

    def send_monthly_emails(self):
        """Send emails to users with monthly frequency"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Only send if it's been at least 25 days since last email
        cutoff_date = datetime.now() - timedelta(days=25)

        cursor.execute('''
            SELECT email, state, frequency FROM users 
            WHERE frequency = 'Monthly' 
            AND (last_sent IS NULL OR last_sent < ?)
        ''', (cutoff_date,))

        monthly_users = cursor.fetchall()
        conn.close()

        print(f"Sending monthly emails to {len(monthly_users)} users...")
        for user in monthly_users:
            self.send_email_to_user(user)

    def run_scheduler(self):
        """Run the email scheduler"""
        print("Starting Story Tracker Email Scheduler...")
        print("Emails will be saved to 'sent_emails' folder")

        # Schedule different frequencies
        schedule.every().day.at("09:00").do(self.send_daily_emails)
        schedule.every().monday.at("09:00").do(self.send_weekly_emails)
        schedule.every().month.do(self.send_monthly_emails)  # First of each month

        # For testing, you can also run immediately:
        # schedule.every(2).minutes.do(self.send_daily_emails)  # Uncomment for testing

        print("Schedule set up:")
        print("- Daily emails: Every day at 9:00 AM")
        print("- Weekly emails: Every Monday at 9:00 AM")
        print("- Monthly emails: First of each month")
        print("\nPress Ctrl+C to stop the scheduler")

        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            print("\nScheduler stopped.")


if __name__ == '__main__':
    scheduler = EmailScheduler()
    scheduler.run_scheduler()
