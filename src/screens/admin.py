import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json
from typing import Dict, List, Optional

from src.models.database import DatabaseManager
from src.models.article import AVAILABLE_ISSUE_AREAS
from src.services.email_service import EmailService
from src.services.scraper import SolutionsStoryScraper
from src.services.scheduler import SchedulerService


class AdminDashboard:
    """Admin dashboard for managing the Story Tracker app"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.email_service = EmailService(db_manager)
        self.scraper = SolutionsStoryScraper(db_manager)
        self.scheduler = SchedulerService(db_manager)

        # Initialize scheduler if not already running
        if not self.scheduler.is_running:
            self.scheduler.start_scheduler()

    def render(self):
        """Render the admin dashboard"""
        st.set_page_config(
            page_title="Story Tracker Admin",
            page_icon="⚙️",
            layout="wide",
            initial_sidebar_state="expanded"
        )

        # Custom CSS
        st.markdown("""
        <style>
        .metric-card {
            background-color: white;
            padding: 1rem;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            border-left: 4px solid #2c5aa0;
            margin-bottom: 1rem;
        }
        .success-alert {
            background-color: #d4edda;
            color: #155724;
            padding: 1rem;
            border-radius: 5px;
            border-left: 4px solid #28a745;
            margin: 1rem 0;
        }
        .warning-alert {
            background-color: #fff3cd;
            color: #856404;
            padding: 1rem;
            border-radius: 5px;
            border-left: 4px solid #ffc107;
            margin: 1rem 0;
        }
        .error-alert {
            background-color: #f8d7da;
            color: #721c24;
            padding: 1rem;
            border-radius: 5px;
            border-left: 4px solid #dc3545;
            margin: 1rem 0;
        }
        </style>
        """, unsafe_allow_html=True)

        # Sidebar navigation
        with st.sidebar:
            st.title("⚙️ Admin Panel")

            page = st.selectbox(
                "Navigation",
                [
                    "📊 Dashboard",
                    "👥 Subscribers",
                    "📧 Email Campaigns",
                    "📰 Articles",
                    "🕒 Scheduler",
                    "⚙️ Settings"
                ]
            )

            # Quick actions
            st.markdown("---")
            st.markdown("### Quick Actions")

            if st.button("🚀 Send Newsletter Now", type="primary"):
                self._quick_send_newsletter()

            if st.button("🔄 Scrape Articles"):
                self._quick_scrape_articles()

            # System status
            st.markdown("---")
            st.markdown("### System Status")
            schedule_info = self.scheduler.get_schedule_info()

            if schedule_info['is_running']:
                st.success("✅ Scheduler Running")
            else:
                st.error("❌ Scheduler Stopped")

            # Next newsletter info
            if schedule_info.get('next_newsletter'):
                next_time = datetime.fromisoformat(schedule_info['next_newsletter'])
                st.info(f"📅 Next newsletter: {next_time.strftime('%m/%d at %I:%M %p')}")

        # Render selected page
        if page == "📊 Dashboard":
            self._render_dashboard()
        elif page == "👥 Subscribers":
            self._render_subscribers()
        elif page == "📧 Email Campaigns":
            self._render_campaigns()
        elif page == "📰 Articles":
            self._render_articles()
        elif page == "🕒 Scheduler":
            self._render_scheduler()
        elif page == "⚙️ Settings":
            self._render_settings()

    def _render_dashboard(self):
        """Render the main dashboard overview"""
        st.title("📊 Dashboard Overview")

        # Get statistics
        subscriber_stats = self.db.get_subscriber_stats()
        recent_campaigns = self.db.get_recent_campaigns(5)
        scraping_stats = self.scraper.get_recent_articles_count(7)

        # Metrics row
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Active Subscribers",
                subscriber_stats['active_subscribers'],
                delta=None
            )

        with col2:
            total_articles = sum(scraping_stats.values())
            st.metric(
                "Articles This Week",
                total_articles,
                delta=None
            )

        with col3:
            sent_campaigns = [c for c in recent_campaigns if c['status'] == 'sent']
            st.metric(
                "Campaigns This Month",
                len(sent_campaigns),
                delta=None
            )

        with col4:
            schedule_info = self.scheduler.get_schedule_info()
            if schedule_info['is_running']:
                st.metric("Scheduler Status", "Running", delta="Healthy")
            else:
                st.metric("Scheduler Status", "Stopped", delta="Needs Attention")

        # Charts and detailed info
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📈 Popular Topics")
            if subscriber_stats['popular_issues']:
                # Create DataFrame for chart
                df_topics = pd.DataFrame(
                    subscriber_stats['popular_issues'][:10],
                    columns=['Topic', 'Subscribers']
                )
                st.bar_chart(df_topics.set_index('Topic'))
            else:
                st.info("No subscriber data available yet")

        with col2:
            st.subheader("📰 Recent Article Collection")
            if scraping_stats:
                df_scraping = pd.DataFrame(
                    list(scraping_stats.items()),
                    columns=['Category', 'Articles']
                )
                st.bar_chart(df_scraping.set_index('Category'))
            else:
                st.info("No recent articles scraped")

        # Recent activity
        st.subheader("🕒 Recent Activity")

        if recent_campaigns:
            for campaign in recent_campaigns[:3]:
                status_emoji = "✅" if campaign['status'] == 'sent' else "⏳"
                timestamp = campaign.get('sent_at') or campaign.get('scheduled_for', 'Unknown')

                st.markdown(f"""
                <div class="metric-card">
                    {status_emoji} <strong>{campaign['campaign_type'].title()} Campaign</strong><br>
                    Recipients: {campaign.get('total_recipients', 0)} | Time: {timestamp}<br>
                    Status: {campaign['status'].title()}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No recent campaigns")

    def _render_subscribers(self):
        """Render subscriber management page"""
        st.title("👥 Subscriber Management")

        # Subscriber statistics
        stats = self.db.get_subscriber_stats()

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Active Subscribers", stats['active_subscribers'])
        with col2:
            st.metric("Inactive Subscribers", stats['inactive_subscribers'])
        with col3:
            st.metric("Total Subscribers", stats['total_subscribers'])

        # Subscriber list
        st.subheader("📋 All Subscribers")

        subscribers = self.db.get_all_active_subscribers()

        if subscribers:
            df = pd.DataFrame(subscribers)
            df['created_at'] = pd.to_datetime(df['created_at']).dt.strftime('%Y-%m-%d')
            df['updated_at'] = pd.to_datetime(df['updated_at']).dt.strftime('%Y-%m-%d')

            # Display table
            st.dataframe(
                df[['email', 'issue_area_1', 'issue_area_2', 'issue_area_3', 'created_at', 'updated_at']],
                use_container_width=True
            )

            # Export functionality
            if st.button("📄 Export to CSV"):
                csv = df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"subscribers_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
        else:
            st.info("No subscribers found")

        # Manual subscriber management
        st.subheader("➕ Add Subscriber Manually")

        with st.form("add_subscriber"):
            col1, col2 = st.columns(2)

            with col1:
                email = st.text_input("Email Address")
                area1 = st.selectbox("First Topic", AVAILABLE_ISSUE_AREAS)

            with col2:
                area2 = st.selectbox("Second Topic", AVAILABLE_ISSUE_AREAS)
                area3 = st.selectbox("Third Topic", AVAILABLE_ISSUE_AREAS)

            if st.form_submit_button("Add Subscriber"):
                if email and area1 and area2 and area3:
                    if len(set([area1, area2, area3])) == 3:
                        success = self.db.add_subscriber(email, area1, area2, area3)
                        if success:
                            st.success(f"✅ Added subscriber: {email}")
                            st.rerun()
                        else:
                            st.error("❌ Error adding subscriber")
                    else:
                        st.error("❌ Please choose three different topics")
                else:
                    st.error("❌ Please fill in all fields")

    def _render_campaigns(self):
        """Render email campaign management"""
        st.title("📧 Email Campaign Management")

        # Campaign statistics
        recent_campaigns = self.db.get_recent_campaigns(10)
        email_stats = self.email_service.get_campaign_statistics(30)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Sends (30 days)", email_stats['total_sends'])
        with col2:
            sent_count = email_stats['campaign_stats'].get('sent', 0)
            st.metric("Successful Campaigns", sent_count)
        with col3:
            failed_count = email_stats['campaign_stats'].get('failed', 0)
            st.metric("Failed Campaigns", failed_count)

        # Manual campaign
        st.subheader("🚀 Send Manual Campaign")

        with st.form("manual_campaign"):
            campaign_type = st.radio(
                "Campaign Type",
                ["Regular Newsletter", "Special Announcement"],
                help="Regular newsletter uses personalized article selection"
            )

            notes = st.text_area("Campaign Notes (optional)")

            if st.form_submit_button("Send Campaign Now", type="primary"):
                self._send_manual_campaign(campaign_type, notes)

        # Preview functionality
        st.subheader("👁️ Preview Newsletter")

        subscribers = self.db.get_all_active_subscribers()
        if subscribers:
            preview_email = st.selectbox(
                "Preview for subscriber:",
                [s['email'] for s in subscribers]
            )

            if st.button("Generate Preview"):
                self._generate_preview(preview_email)

        # Recent campaigns
        st.subheader("📋 Recent Campaigns")

        if recent_campaigns:
            df_campaigns = pd.DataFrame(recent_campaigns)
            df_campaigns['sent_at'] = pd.to_datetime(df_campaigns['sent_at'], errors='coerce').dt.strftime(
                '%Y-%m-%d %H:%M')
            df_campaigns['scheduled_for'] = pd.to_datetime(df_campaigns['scheduled_for'], errors='coerce').dt.strftime(
                '%Y-%m-%d %H:%M')

            st.dataframe(
                df_campaigns[['id', 'campaign_type', 'status', 'total_recipients', 'sent_at', 'notes']],
                use_container_width=True
            )
        else:
            st.info("No recent campaigns")

    def _render_articles(self):
        """Render article management page"""
        st.title("📰 Article Management")

        # Article statistics
        scraping_stats = self.scraper.get_recent_articles_count(30)

        if scraping_stats:
            total_articles = sum(scraping_stats.values())
            st.metric("Articles (Last 30 days)", total_articles)

            # Articles by category chart
            df_articles = pd.DataFrame(
                list(scraping_stats.items()),
                columns=['Category', 'Count']
            )
            st.bar_chart(df_articles.set_index('Category'))

        # Manual scraping
        st.subheader("🔄 Manual Article Scraping")

        with st.form("manual_scrape"):
            col1, col2 = st.columns(2)

            with col1:
                scrape_category = st.selectbox(
                    "Category (optional)",
                    ["All Categories"] + AVAILABLE_ISSUE_AREAS
                )

            with col2:
                article_limit = st.number_input(
                    "Articles per category",
                    min_value=1,
                    max_value=50,
                    value=10
                )

            if st.form_submit_button("Start Scraping"):
                self._manual_scrape(scrape_category, article_limit)

        # Article exclusion management
        st.subheader("🚫 Article Exclusions")
        st.info("Article exclusion management coming soon...")

    def _render_scheduler(self):
        """Render scheduler management page"""
        st.title("🕒 Scheduler Management")

        # Current schedule info
        schedule_info = self.scheduler.get_schedule_info()

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📅 Current Schedule")

            if schedule_info['is_running']:
                st.success("✅ Scheduler is running")
            else:
                st.error("❌ Scheduler is stopped")

            current_schedule = schedule_info['email_schedule']
            st.info(f"""
            **Newsletter Schedule:**
            - Day: {current_schedule['day_name']}
            - Time: {current_schedule['time_string']}
            """)

            if schedule_info.get('next_newsletter'):
                next_time = datetime.fromisoformat(schedule_info['next_newsletter'])
                st.info(f"📧 Next newsletter: {next_time.strftime('%B %d, %Y at %I:%M %p')}")

        with col2:
            st.subheader("⚙️ Update Schedule")

            with st.form("update_schedule"):
                new_day = st.selectbox(
                    "Day of week",
                    options=list(range(7)),
                    format_func=lambda x:
                    ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][x],
                    index=schedule_info['email_schedule']['day']
                )

                col_h, col_m = st.columns(2)
                with col_h:
                    new_hour = st.number_input("Hour (24h)", 0, 23, schedule_info['email_schedule']['hour'])
                with col_m:
                    new_minute = st.number_input("Minute", 0, 59, schedule_info['email_schedule']['minute'])

                if st.form_submit_button("Update Schedule"):
                    self.scheduler.update_schedule(new_day, new_hour, new_minute)
                    st.success("✅ Schedule updated!")
                    st.rerun()

        # Scheduler controls
        st.subheader("🎮 Scheduler Controls")

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("▶️ Start Scheduler"):
                if not schedule_info['is_running']:
                    self.scheduler.start_scheduler()
                    st.success("Scheduler started")
                    st.rerun()
                else:
                    st.info("Scheduler already running")

        with col2:
            if st.button("⏹️ Stop Scheduler"):
                if schedule_info['is_running']:
                    self.scheduler.stop_scheduler()
                    st.success("Scheduler stopped")
                    st.rerun()
                else:
                    st.info("Scheduler already stopped")

        with col3:
            if st.button("🔄 Restart Scheduler"):
                self.scheduler.stop_scheduler()
                self.scheduler.start_scheduler()
                st.success("Scheduler restarted")
                st.rerun()

        # Recent activity
        st.subheader("📊 Recent Activity")
        recent_activity = self.scheduler.get_recent_activity(7)

        if recent_activity['recent_campaigns']:
            st.write(f"**Campaigns in last 7 days:** {recent_activity['total_campaigns']}")
            for campaign in recent_activity['recent_campaigns'][:5]:
                st.write(f"• {campaign['campaign_type']} - {campaign['total_recipients']} recipients")

        if recent_activity['scraping_stats']:
            st.write(f"**Articles scraped in last 7 days:** {recent_activity['total_articles_scraped']}")

    def _render_settings(self):
        """Render system settings page"""
        st.title("⚙️ System Settings")

        # Email settings
        st.subheader("📧 Email Settings")

        with st.form("email_settings"):
            min_articles = st.number_input(
                "Minimum articles per category",
                min_value=1,
                max_value=5,
                value=int(self.db.get_setting('min_articles_per_category', '1'))
            )

            fallback_enabled = st.checkbox(
                "Enable fallback categories",
                value=bool(int(self.db.get_setting('fallback_enabled', '1')))
            )

            if st.form_submit_button("Save Email Settings"):
                self.db.set_setting('min_articles_per_category', str(min_articles))
                self.db.set_setting('fallback_enabled', str(int(fallback_enabled)))
                st.success("✅ Email settings saved")

        # Scraping settings
        st.subheader("🔄 Scraping Settings")

        with st.form("scraping_settings"):
            daily_limit = st.number_input(
                "Daily scrape limit per category",
                min_value=1,
                max_value=50,
                value=int(self.db.get_setting('daily_scrape_limit', '5'))
            )

            retention_days = st.number_input(
                "Article retention days",
                min_value=30,
                max_value=365,
                value=int(self.db.get_setting('article_retention_days', '90'))
            )

            if st.form_submit_button("Save Scraping Settings"):
                self.db.set_setting('daily_scrape_limit', str(daily_limit))
                self.db.set_setting('article_retention_days', str(retention_days))
                st.success("✅ Scraping settings saved")

        # Database maintenance
        st.subheader("🗃️ Database Maintenance")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("🧹 Clean Old Articles"):
                retention_days = int(self.db.get_setting('article_retention_days', '90'))
                removed = self.scraper.cleanup_old_articles(retention_days)
                st.success(f"✅ Removed {removed} old articles")

        with col2:
            if st.button("📊 Export All Data"):
                st.info("Data export functionality coming soon...")

    def _quick_send_newsletter(self):
        """Quick action to send newsletter"""
        with st.spinner("Sending newsletter..."):
            result = self.scheduler.trigger_manual_newsletter()

            if result['success']:
                st.success(f"✅ Newsletter sent to {result['successful_sends']} subscribers!")
            else:
                st.error(f"❌ Newsletter failed: {result.get('message', 'Unknown error')}")

    def _quick_scrape_articles(self):
        """Quick action to scrape articles"""
        with st.spinner("Scraping articles..."):
            result = self.scheduler.trigger_manual_scrape(limit=5)

            if result['success']:
                st.success(f"✅ Scraped {result['total_articles']} articles!")
            else:
                st.error(f"❌ Scraping failed: {result.get('message', 'Unknown error')}")

    def _send_manual_campaign(self, campaign_type: str, notes: str):
        """Send manual email campaign"""
        with st.spinner("Sending campaign..."):
            result = self.email_service.send_newsletter_campaign('manual')

            if result['success']:
                st.markdown(f'''
                <div class="success-alert">
                    ✅ <strong>Campaign sent successfully!</strong><br>
                    Campaign ID: {result['campaign_id']}<br>
                    Recipients: {result['successful_sends']}<br>
                    Failed: {result['failed_sends']}
                </div>
                ''', unsafe_allow_html=True)
            else:
                st.markdown(f'''
                <div class="error-alert">
                    ❌ <strong>Campaign failed:</strong> {result.get('message', 'Unknown error')}
                </div>
                ''', unsafe_allow_html=True)

    def _generate_preview(self, email: str):
        """Generate newsletter preview"""
        with st.spinner("Generating preview..."):
            preview_html = self.email_service.preview_newsletter_for_subscriber(email)

            if preview_html:
                st.subheader(f"📧 Preview for {email}")
                st.components.v1.html(preview_html, height=600, scrolling=True)
            else:
                st.error("❌ Could not generate preview")

    def _manual_scrape(self, category: str, limit: int):
        """Perform manual scraping"""
        with st.spinner(f"Scraping {category}..."):
            if category == "All Categories":
                result = self.scheduler.trigger_manual_scrape(limit=limit)
            else:
                result = self.scheduler.trigger_manual_scrape(category, limit)

            if result['success']:
                st.success(f"✅ Scraped {result['total_articles']} articles!")

                # Show breakdown
                for cat, count in result['articles_by_category'].items():
                    if count > 0:
                        st.write(f"• {cat}: {count} articles")
            else:
                st.error(f"❌ Scraping failed: {result.get('message', 'Unknown error')}")


def main():
    """Main function to run the admin dashboard"""
    # Initialize database
    db = DatabaseManager()

    # Create and render admin dashboard
    admin_dashboard = AdminDashboard(db)
    admin_dashboard.render()


if __name__ == "__main__":
    main()