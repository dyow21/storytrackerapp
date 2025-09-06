"""
Story Tracker App - Main Entry Point

This application manages a newsletter system for solutions journalism articles.
It provides both a public subscription interface and an admin dashboard.
"""

import streamlit as st
import sys
import os
from pathlib import Path

# Add src directory to path for imports
src_path = Path(__file__).parent
sys.path.insert(0, str(src_path))

# Add parent directory to path so we can import from storytrackerapp
parent_path = src_path.parent
sys.path.insert(0, str(parent_path))

from src.models.database import DatabaseManager
from src.screens.subscription import SubscriptionScreen
from src.screens.admin import AdminDashboard


def main():
    """Main application entry point"""

    # Initialize database
    db = DatabaseManager()

    # Check if this is admin mode via URL parameter
    query_params = st.experimental_get_query_params()
    is_admin = query_params.get('admin', [False])[0]

    # Also check for admin password in environment or session state
    admin_password = os.getenv('ADMIN_PASSWORD', 'admin123')

    if is_admin or st.session_state.get('admin_authenticated', False):
        if not st.session_state.get('admin_authenticated', False):
            # Show admin login
            _show_admin_login(admin_password)
        else:
            # Show admin dashboard
            admin_dashboard = AdminDashboard(db)
            admin_dashboard.render()
    else:
        # Show public subscription interface
        subscription_screen = SubscriptionScreen(db)
        subscription_screen.render()


def _show_admin_login(correct_password: str):
    """Show admin login form"""
    st.set_page_config(
        page_title="Admin Login",
        page_icon="🔐",
        layout="centered"
    )

    st.title("🔐 Admin Access")

    with st.form("admin_login"):
        password = st.text_input("Admin Password", type="password")
        submitted = st.form_submit_button("Login")

        if submitted:
            if password == correct_password:
                st.session_state['admin_authenticated'] = True
                st.success("✅ Access granted")
                st.rerun()
            else:
                st.error("❌ Invalid password")

    st.markdown("---")
    st.markdown("### Public Access")
    if st.button("🔙 Back to Newsletter Signup"):
        # Clear admin parameter by setting empty query params
        st.query_params.clear()
        st.rerun()


if __name__ == "__main__":
    main()