import threading
import time
from datetime import datetime, timedelta
from typing import Optional, Callable
import schedule

from src.models.database import DatabaseManager
from src.services.email_service import EmailService
from src.services.scraper import SolutionsStoryScraper


class SchedulerService:
    """Handles automated scheduling for the Story Tracker app"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.email_service = EmailService(db_manager)
        self.scraper = SolutionsStoryScraper(db_manager)
        self.scheduler_thread = None
        self.is_running = False
        self.callbacks = {
            'on_email_sent': None,
            'on_scrape_complete': None,
            'on_error': None
        }

    def start_scheduler(self):
        """Start the background scheduler thread"""
        if self.is_running:
            print("Scheduler is already running")
            return

        self.is_running = True
        self._setup_schedules()

        # Start scheduler in background thread
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()

        print("Scheduler started successfully")

    def stop_scheduler(self):
        """Stop the background scheduler"""
        self.is_running = False
        schedule.clear()

        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=5)

        print("Scheduler stopped")

    def _setup_schedules(self):
        """Setup all scheduled tasks based on admin settings"""
        schedule.clear()

        # Get scheduling settings from database
        schedule_day = int(self.db.get_setting('email_schedule_day', '1'))  # Tuesday
        schedule_hour = int(self.db.get_setting('email_schedule_hour', '9'))
        schedule_minute = int(self.db.get_setting('email_schedule_minute', '0'))

        # Convert day number to schedule day name
        days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        schedule_day_name = days[schedule_day]

        # Schedule weekly newsletter
        schedule_time = f"{schedule_hour:02d}:{schedule_minute:02d}"
        getattr(schedule.every(), schedule_day_name).at(schedule_time).do(self._send_weekly_newsletter)

        # Schedule daily scraping (early morning)
        schedule.every().day.at("06:00").do(self._daily_scrape)

        # Schedule weekly cleanup (Sunday at 2 AM)
        schedule.every().sunday.at("02:00").do(self._weekly_cleanup)

        print(f"Scheduled weekly newsletter: Every {schedule_day_name.title()} at {schedule_time}")
        print("Scheduled daily scraping: Every day at 06:00")
        print("Scheduled weekly cleanup: Every Sunday at 02:00")

    def _run_scheduler(self):
        """Run the scheduler loop"""
        while self.is_running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except Exception as e:
                print(f"Scheduler error: {e}")
                if self.callbacks['on_error']:
                    self.callbacks['on_error'](e)
                time.sleep(60)

    def _send_weekly_newsletter(self):
        """Send the weekly newsletter to all subscribers"""
        try:
            print(f"Starting weekly newsletter campaign at {datetime.now()}")

            # Send newsletter campaign
            result = self.email_service.send_newsletter_campaign('scheduled')

            if result['success']:
                print(f"Weekly newsletter sent successfully to {result['successful_sends']} subscribers")

                if self.callbacks['on_email_sent']:
                    self.callbacks['on_email_sent'](result)
            else:
                print(f"Weekly newsletter failed: {result.get('message', 'Unknown error')}")

        except Exception as e:
            print(f"Error sending weekly newsletter: {e}")
            if self.callbacks['on_error']:
                self.callbacks['on_error'](e)

    def _daily_scrape(self):
        """Perform daily article scraping"""
        try:
            print(f"Starting daily article scraping at {datetime.now()}")

            # Scrape articles for all issue areas
            articles_per_issue = int(self.db.get_setting('daily_scrape_limit', '5'))
            scraped_articles = self.scraper.scrape_all_issue_areas(articles_per_issue)

            total_scraped = sum(len(articles) for articles in scraped_articles.values())
            print(f"Daily scraping completed: {total_scraped} articles scraped")

            if self.callbacks['on_scrape_complete']:
                self.callbacks['on_scrape_complete']({
                    'total_articles': total_scraped,
                    'by_category': {k: len(v) for k, v in scraped_articles.items()},
                    'timestamp': datetime.now().isoformat()
                })

        except Exception as e:
            print(f"Error during daily scraping: {e}")
            if self.callbacks['on_error']:
                self.callbacks['on_error'](e)

    def _weekly_cleanup(self):
        """Perform weekly database cleanup"""
        try:
            print(f"Starting weekly cleanup at {datetime.now()}")

            # Clean up old articles
            days_to_keep = int(self.db.get_setting('article_retention_days', '90'))
            removed_count = self.scraper.cleanup_old_articles(days_to_keep)

            print(f"Weekly cleanup completed: {removed_count} old articles removed")

        except Exception as e:
            print(f"Error during weekly cleanup: {e}")
            if self.callbacks['on_error']:
                self.callbacks['on_error'](e)

    def set_callback(self, event: str, callback: Callable):
        """Set callback function for scheduler events"""
        if event in self.callbacks:
            self.callbacks[event] = callback
        else:
            raise ValueError(f"Unknown callback event: {event}")

    def update_schedule(self, day: int, hour: int, minute: int):
        """Update the email schedule"""
        self.db.set_setting('email_schedule_day', str(day))
        self.db.set_setting('email_schedule_hour', str(hour))
        self.db.set_setting('email_schedule_minute', str(minute))

        # Restart scheduler with new settings
        if self.is_running:
            self._setup_schedules()
            print(f"Schedule updated: Day {day}, {hour:02d}:{minute:02d}")

    def trigger_manual_newsletter(self, article_ids: Optional[list] = None) -> dict:
        """Manually trigger newsletter campaign"""
        try:
            print(f"Starting manual newsletter campaign at {datetime.now()}")

            if article_ids:
                # Manual campaign with specific articles - would need to implement this in EmailService
                print(f"Manual campaign with {len(article_ids)} specific articles")
                # For now, send regular campaign
                result = self.email_service.send_newsletter_campaign('manual')
            else:
                result = self.email_service.send_newsletter_campaign('manual')

            return result

        except Exception as e:
            print(f"Error in manual newsletter: {e}")
            return {
                'success': False,
                'message': str(e)
            }

    def trigger_manual_scrape(self, issue_area: Optional[str] = None, limit: int = 10) -> dict:
        """Manually trigger article scraping"""
        try:
            print(f"Starting manual scraping at {datetime.now()}")

            if issue_area:
                # Scrape specific issue area
                articles = self.scraper.scrape_articles_for_issue(issue_area, limit)
                total_scraped = len(articles)
                result = {issue_area: articles}
            else:
                # Scrape all issue areas
                result = self.scraper.scrape_all_issue_areas(limit)
                total_scraped = sum(len(articles) for articles in result.values())

            print(f"Manual scraping completed: {total_scraped} articles")

            return {
                'success': True,
                'total_articles': total_scraped,
                'articles_by_category': {k: len(v) for k, v in result.items()},
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            print(f"Error in manual scraping: {e}")
            return {
                'success': False,
                'message': str(e)
            }

    def get_schedule_info(self) -> dict:
        """Get current schedule information"""
        schedule_day = int(self.db.get_setting('email_schedule_day', '1'))
        schedule_hour = int(self.db.get_setting('email_schedule_hour', '9'))
        schedule_minute = int(self.db.get_setting('email_schedule_minute', '0'))

        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

        return {
            'is_running': self.is_running,
            'email_schedule': {
                'day': schedule_day,
                'day_name': days[schedule_day],
                'hour': schedule_hour,
                'minute': schedule_minute,
                'time_string': f"{schedule_hour:02d}:{schedule_minute:02d}"
            },
            'next_newsletter': self._get_next_newsletter_time(),
            'next_scrape': self._get_next_scrape_time()
        }

    def _get_next_newsletter_time(self) -> Optional[str]:
        """Calculate next newsletter send time"""
        try:
            schedule_day = int(self.db.get_setting('email_schedule_day', '1'))
            schedule_hour = int(self.db.get_setting('email_schedule_hour', '9'))
            schedule_minute = int(self.db.get_setting('email_schedule_minute', '0'))

            now = datetime.now()
            days_ahead = schedule_day - now.weekday()

            if days_ahead <= 0:  # Target day has passed this week
                days_ahead += 7

            next_send = now + timedelta(days=days_ahead)
            next_send = next_send.replace(hour=schedule_hour, minute=schedule_minute, second=0, microsecond=0)

            # If it's the same day but time has passed, add a week
            if next_send <= now:
                next_send += timedelta(weeks=1)

            return next_send.isoformat()

        except Exception as e:
            print(f"Error calculating next newsletter time: {e}")
            return None

    def _get_next_scrape_time(self) -> Optional[str]:
        """Calculate next scrape time"""
        try:
            now = datetime.now()
            next_scrape = now.replace(hour=6, minute=0, second=0, microsecond=0)

            # If 6 AM has passed today, schedule for tomorrow
            if next_scrape <= now:
                next_scrape += timedelta(days=1)

            return next_scrape.isoformat()

        except Exception as e:
            print(f"Error calculating next scrape time: {e}")
            return None

    def get_recent_activity(self, days: int = 7) -> dict:
        """Get recent scheduler activity"""
        from datetime import timedelta

        cutoff_date = datetime.now() - timedelta(days=days)

        # Get recent campaigns
        recent_campaigns = self.db.get_recent_campaigns(limit=20)

        # Filter to specified time period
        recent_campaigns = [
            campaign for campaign in recent_campaigns
            if campaign.get('sent_at') and
               datetime.fromisoformat(campaign['sent_at'].replace('Z', '+00:00')) >= cutoff_date
        ]

        # Get article scraping stats
        scraping_stats = self.scraper.get_recent_articles_count(days)

        return {
            'period_days': days,
            'recent_campaigns': recent_campaigns,
            'scraping_stats': scraping_stats,
            'total_campaigns': len(recent_campaigns),
            'total_articles_scraped': sum(scraping_stats.values())
        }