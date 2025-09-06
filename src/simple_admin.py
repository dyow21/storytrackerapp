import streamlit as st
import pandas as pd
from datetime import datetime
from typing import Dict, List

from src.models.database import DatabaseManager
from src.models.article import AVAILABLE_ISSUE_AREAS


class SimpleAdminDashboard:
    """Simplified admin dashboard for testing"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def render(self):
        """Render the admin dashboard"""
        st.set_page_config(
            page_title="Story Tracker Admin",
            page_icon="⚙️",
            layout="wide"
        )

        # Force text visibility
        st.markdown("""
        <style>
        .main .block-container {
            color: #262730;
        }
        .stMarkdown p, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
            color: #262730 !important;
        }
        .stSelectbox label, .stTextInput label, .stCheckbox label, .stMetric label {
            color: #262730 !important;
        }
        </style>
        """, unsafe_allow_html=True)

        st.title("⚙️ Story Tracker Admin Dashboard")

        # Sidebar navigation
        with st.sidebar:
            st.title("Admin Panel")
            page = st.selectbox(
                "Navigation",
                [
                    "📊 Dashboard",
                    "👥 Subscribers",
                    "📧 Quick Actions"
                ]
            )

        # Render selected page
        if page == "📊 Dashboard":
            self._render_dashboard()
        elif page == "👥 Subscribers":
            self._render_subscribers()
        elif page == "📧 Quick Actions":
            self._render_quick_actions()

    def _render_dashboard(self):
        """Render dashboard overview"""
        st.header("📊 Dashboard Overview")

        # Get statistics
        try:
            subscriber_stats = self.db.get_subscriber_stats()

            # Metrics
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Active Subscribers", subscriber_stats['active_subscribers'])
            with col2:
                st.metric("Total Subscribers", subscriber_stats['total_subscribers'])
            with col3:
                st.metric("Inactive Subscribers", subscriber_stats['inactive_subscribers'])

            # Popular topics
            st.subheader("📈 Popular Topics")
            if subscriber_stats['popular_issues']:
                for topic, count in subscriber_stats['popular_issues'][:10]:
                    st.write(f"• **{topic}**: {count} subscribers")
            else:
                st.info("No subscriber data available yet")

        except Exception as e:
            st.error(f"Error loading dashboard: {e}")

    def _render_subscribers(self):
        """Render subscriber management"""
        st.header("👥 Subscriber Management")

        try:
            # Get all subscribers
            subscribers = self.db.get_all_active_subscribers()

            if subscribers:
                st.write(f"**Total Active Subscribers:** {len(subscribers)}")

                # Display as table
                df = pd.DataFrame(subscribers)
                df['created_at'] = pd.to_datetime(df['created_at']).dt.strftime('%Y-%m-%d')

                st.dataframe(
                    df[['email', 'issue_area_1', 'issue_area_2', 'issue_area_3', 'created_at']],
                    use_container_width=True
                )

                # Add subscriber form
                st.subheader("➕ Add New Subscriber")
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
            else:
                st.info("No subscribers found")

        except Exception as e:
            st.error(f"Error loading subscribers: {e}")

    def _render_quick_actions(self):
        """Render quick actions"""
        st.header("📧 Quick Actions")

        st.subheader("🧪 Test Email Generation")

        # Get subscribers for testing
        try:
            subscribers = self.db.get_all_active_subscribers()

            if subscribers:
                # Email preview
                st.write("**Generate Test Email Preview:**")

                preview_email = st.selectbox(
                    "Select subscriber for preview:",
                    [s['email'] for s in subscribers]
                )

                if st.button("📧 Generate Preview Email"):
                    self._generate_test_email(preview_email)
            else:
                st.info("No subscribers available for testing")

            # Database test
            st.subheader("🔧 Database Tests")

            if st.button("Test Database Connection"):
                try:
                    stats = self.db.get_subscriber_stats()
                    st.success("✅ Database connection successful!")
                    st.json(stats)
                except Exception as e:
                    st.error(f"❌ Database error: {e}")

            # Quick scraping test (without actual scraping)
            st.subheader("🔄 Test Article System")

            if st.button("Test Article Storage"):
                try:
                    # Add a test article
                    test_id = self.db.add_article(
                        title="Test Article - Solutions in Education",
                        url="https://example.com/test-article",
                        outlet="Test Outlet",
                        issue_area="Education"
                    )

                    if test_id:
                        st.success(f"✅ Test article added with ID: {test_id}")
                    else:
                        st.info("ℹ️ Test article already exists (duplicate URL)")

                except Exception as e:
                    st.error(f"❌ Article system error: {e}")

        except Exception as e:
            st.error(f"Error in quick actions: {e}")

    def _generate_test_email(self, email: str):
        """Generate a test email preview"""
        try:
            # Get subscriber
            subscriber_data = self.db.get_subscriber_by_email(email)

            if subscriber_data:
                # Simple HTML email preview
                html_preview = f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h1 style="color: #2c5aa0;">Your Weekly Solutions Stories</h1>
                    <p><strong>Hello!</strong></p>
                    <p>Here would be your personalized newsletter for:</p>
                    <ul>
                        <li><strong>{subscriber_data['issue_area_1']}</strong></li>
                        <li><strong>{subscriber_data['issue_area_2']}</strong></li>
                        <li><strong>{subscriber_data['issue_area_3']}</strong></li>
                    </ul>
                    <p><em>This is a test preview. Real newsletters would contain actual articles.</em></p>
                </div>
                """

                st.success("✅ Test email generated!")
                st.subheader(f"Preview for {email}")
                st.components.v1.html(html_preview, height=300)

            else:
                st.error("❌ Subscriber not found")

        except Exception as e:
            st.error(f"❌ Error generating preview: {e}")


def main():
    """Main function for testing admin dashboard"""
    db = DatabaseManager()
    admin = SimpleAdminDashboard(db)
    admin.render()


if __name__ == "__main__":
    main()