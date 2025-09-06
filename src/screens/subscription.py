import streamlit as st
from typing import List, Optional
from datetime import datetime

from src.models.database import DatabaseManager
from src.models.article import AVAILABLE_ISSUE_AREAS, Subscriber


class SubscriptionScreen:
    """Public subscription form for users to sign up for newsletters"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def render(self):
        """Render the subscription form"""
        st.set_page_config(
            page_title="Story Tracker Newsletter",
            page_icon="📰",
            layout="centered",
            initial_sidebar_state="collapsed"
        )

        # Custom CSS for better styling
        st.markdown("""
        <style>
        .main-header {
            text-align: center;
            color: #2c5aa0;
            margin-bottom: 2rem;
        }
        .description-box {
            background-color: #f8f9fa;
            padding: 1.5rem;
            border-radius: 10px;
            border-left: 4px solid #2c5aa0;
            margin-bottom: 2rem;
        }
        .success-message {
            background-color: #d4edda;
            color: #155724;
            padding: 1rem;
            border-radius: 5px;
            border-left: 4px solid #28a745;
            margin: 1rem 0;
        }
        .error-message {
            background-color: #f8d7da;
            color: #721c24;
            padding: 1rem;
            border-radius: 5px;
            border-left: 4px solid #dc3545;
            margin: 1rem 0;
        }
        .form-section {
            background-color: white;
            padding: 2rem;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 2rem;
        }
        .category-help {
            font-size: 0.9em;
            color: #6c757d;
            font-style: italic;
            margin-top: 0.5rem;
        }
        </style>
        """, unsafe_allow_html=True)

        # Main header
        st.markdown('<h1 class="main-header">📰 Solutions Story Newsletter</h1>', unsafe_allow_html=True)

        # Description
        st.markdown("""
        <div class="description-box">
            <h3>Get Weekly Solutions Stories Delivered to Your Inbox</h3>
            <p>Stay inspired with positive, actionable stories that highlight innovative approaches to social challenges. 
            Choose three topic areas that matter most to you, and we'll send you carefully selected articles every week.</p>
            <p><strong>What you'll receive:</strong></p>
            <ul>
                <li>3 curated articles weekly, one from each of your chosen categories</li>
                <li>Solutions-focused journalism that goes beyond problems to explore what's working</li>
                <li>Stories about innovative programs, policies, and approaches making a difference</li>
                <li>Clean, readable format delivered every Tuesday morning</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

        # Check if user is updating existing subscription
        if 'update_email' in st.session_state:
            self._render_update_form()
        else:
            self._render_signup_form()

        # Footer
        st.markdown("---")
        st.markdown(
            "*This service is powered by the [Solutions Story Tracker](https://storytracker.solutionsjournalism.org/)*")
        st.markdown("*Questions? Contact your administrator*")

    def _render_signup_form(self):
        """Render the main signup form"""
        st.markdown('<div class="form-section">', unsafe_allow_html=True)

        with st.form("subscription_form", clear_on_submit=True):
            st.markdown("### ✉️ Sign Up for Your Newsletter")

            # Email input
            email = st.text_input(
                "Email Address *",
                placeholder="your.email@example.com",
                help="We'll only use this to send you your weekly newsletter"
            )

            st.markdown("### 📋 Choose Your Three Topic Areas")
            st.markdown('<div class="category-help">Select exactly three areas you\'re most interested in:</div>',
                        unsafe_allow_html=True)

            # Issue area selection
            col1, col2, col3 = st.columns(3)

            with col1:
                area1 = st.selectbox(
                    "First Topic Area *",
                    options=[""] + AVAILABLE_ISSUE_AREAS,
                    key="area1"
                )

            with col2:
                area2 = st.selectbox(
                    "Second Topic Area *",
                    options=[""] + AVAILABLE_ISSUE_AREAS,
                    key="area2"
                )

            with col3:
                area3 = st.selectbox(
                    "Third Topic Area *",
                    options=[""] + AVAILABLE_ISSUE_AREAS,
                    key="area3"
                )

            # Show selected topics summary
            if area1 and area2 and area3:
                st.markdown("**Your selected topics:**")
                st.write(f"• {area1}")
                st.write(f"• {area2}")
                st.write(f"• {area3}")

            # Terms and submit
            st.markdown("---")
            terms_agreed = st.checkbox(
                "I agree to receive weekly newsletter emails and understand I can unsubscribe at any time."
            )

            submitted = st.form_submit_button("🚀 Subscribe to Newsletter", type="primary")

            if submitted:
                self._handle_subscription(email, area1, area2, area3, terms_agreed)

        st.markdown('</div>', unsafe_allow_html=True)

        # Existing subscriber section
        st.markdown("---")
        st.markdown("### Already Subscribed?")

        col1, col2 = st.columns([2, 1])
        with col1:
            existing_email = st.text_input("Enter your email to update preferences:", key="existing_email")
        with col2:
            st.write("")  # Spacing
            if st.button("Update Preferences"):
                if existing_email:
                    self._load_existing_subscription(existing_email)

    def _render_update_form(self):
        """Render form for updating existing subscription"""
        existing_subscriber = st.session_state.get('existing_subscriber')

        st.markdown('<div class="form-section">', unsafe_allow_html=True)
        st.markdown("### 🔄 Update Your Subscription")

        if existing_subscriber:
            st.success(f"Updating preferences for: **{existing_subscriber['email']}**")

            with st.form("update_form", clear_on_submit=False):
                st.markdown("### 📋 Update Your Three Topic Areas")

                # Pre-populate with existing selections
                col1, col2, col3 = st.columns(3)

                with col1:
                    area1 = st.selectbox(
                        "First Topic Area *",
                        options=AVAILABLE_ISSUE_AREAS,
                        index=AVAILABLE_ISSUE_AREAS.index(existing_subscriber['issue_area_1']),
                        key="update_area1"
                    )

                with col2:
                    area2 = st.selectbox(
                        "Second Topic Area *",
                        options=AVAILABLE_ISSUE_AREAS,
                        index=AVAILABLE_ISSUE_AREAS.index(existing_subscriber['issue_area_2']),
                        key="update_area2"
                    )

                with col3:
                    area3 = st.selectbox(
                        "Third Topic Area *",
                        options=AVAILABLE_ISSUE_AREAS,
                        index=AVAILABLE_ISSUE_AREAS.index(existing_subscriber['issue_area_3']),
                        key="update_area3"
                    )

                st.markdown("---")
                col1, col2, col3 = st.columns(3)

                with col1:
                    if st.form_submit_button("💾 Save Changes", type="primary"):
                        self._handle_update(existing_subscriber['email'], area1, area2, area3)

                with col2:
                    if st.form_submit_button("❌ Cancel"):
                        self._clear_update_session()
                        st.rerun()

                with col3:
                    if st.form_submit_button("🗑️ Unsubscribe", type="secondary"):
                        self._handle_unsubscribe(existing_subscriber['email'])

        st.markdown('</div>', unsafe_allow_html=True)

    def _handle_subscription(self, email: str, area1: str, area2: str, area3: str, terms_agreed: bool):
        """Handle new subscription submission"""
        errors = []

        # Validation
        if not email or not self._validate_email(email):
            errors.append("Please enter a valid email address")

        if not area1 or not area2 or not area3:
            errors.append("Please select all three topic areas")

        if len(set([area1, area2, area3])) != 3:
            errors.append("Please choose three different topic areas")

        if not terms_agreed:
            errors.append("Please agree to the terms to continue")

        if errors:
            for error in errors:
                st.markdown(f'<div class="error-message">❌ {error}</div>', unsafe_allow_html=True)
            return

        # Check if user already exists
        existing = self.db.get_subscriber_by_email(email)

        try:
            success = self.db.add_subscriber(email, area1, area2, area3)

            if success:
                if existing:
                    st.markdown(f'''
                    <div class="success-message">
                        ✅ <strong>Subscription Updated!</strong><br>
                        Your preferences have been updated for <strong>{email}</strong><br>
                        You'll receive stories about: <strong>{area1}</strong>, <strong>{area2}</strong>, and <strong>{area3}</strong>
                    </div>
                    ''', unsafe_allow_html=True)
                else:
                    st.markdown(f'''
                    <div class="success-message">
                        ✅ <strong>Welcome to Solutions Stories!</strong><br>
                        You're now subscribed with <strong>{email}</strong><br>
                        You'll receive stories about: <strong>{area1}</strong>, <strong>{area2}</strong>, and <strong>{area3}</strong><br>
                        Your first newsletter will arrive next Tuesday morning.
                    </div>
                    ''', unsafe_allow_html=True)

                # Show balloons for new subscribers
                if not existing:
                    st.balloons()

            else:
                st.markdown(
                    '<div class="error-message">❌ There was an error processing your subscription. Please try again.</div>',
                    unsafe_allow_html=True)

        except Exception as e:
            st.markdown(f'<div class="error-message">❌ Error: {str(e)}</div>', unsafe_allow_html=True)

    def _handle_update(self, email: str, area1: str, area2: str, area3: str):
        """Handle subscription update"""
        if len(set([area1, area2, area3])) != 3:
            st.markdown('<div class="error-message">❌ Please choose three different topic areas</div>',
                        unsafe_allow_html=True)
            return

        try:
            success = self.db.add_subscriber(email, area1, area2, area3)

            if success:
                st.markdown(f'''
                <div class="success-message">
                    ✅ <strong>Preferences Updated!</strong><br>
                    Your subscription has been updated. You'll now receive stories about:<br>
                    <strong>{area1}</strong>, <strong>{area2}</strong>, and <strong>{area3}</strong>
                </div>
                ''', unsafe_allow_html=True)

                # Clear update session after successful update
                self._clear_update_session()

            else:
                st.markdown(
                    '<div class="error-message">❌ There was an error updating your subscription. Please try again.</div>',
                    unsafe_allow_html=True)

        except Exception as e:
            st.markdown(f'<div class="error-message">❌ Error: {str(e)}</div>', unsafe_allow_html=True)

    def _handle_unsubscribe(self, email: str):
        """Handle unsubscription"""
        try:
            success = self.db.deactivate_subscriber(email)

            if success:
                st.markdown(f'''
                <div class="success-message">
                    ✅ <strong>You've been unsubscribed</strong><br>
                    We're sorry to see you go! You will no longer receive newsletters at <strong>{email}</strong><br>
                    You can resubscribe at any time using the form above.
                </div>
                ''', unsafe_allow_html=True)

                # Clear update session
                self._clear_update_session()

            else:
                st.markdown(
                    '<div class="error-message">❌ There was an error processing your unsubscription. Please try again.</div>',
                    unsafe_allow_html=True)

        except Exception as e:
            st.markdown(f'<div class="error-message">❌ Error: {str(e)}</div>', unsafe_allow_html=True)

    def _load_existing_subscription(self, email: str):
        """Load existing subscription for updating"""
        if not email or not self._validate_email(email):
            st.markdown('<div class="error-message">❌ Please enter a valid email address</div>',
                        unsafe_allow_html=True)
            return

        existing = self.db.get_subscriber_by_email(email)

        if existing and existing['active']:
            st.session_state['update_email'] = email
            st.session_state['existing_subscriber'] = existing
            st.rerun()
        else:
            st.markdown(f'<div class="error-message">❌ No active subscription found for {email}</div>',
                        unsafe_allow_html=True)

    def _clear_update_session(self):
        """Clear update session state"""
        keys_to_remove = ['update_email', 'existing_subscriber']
        for key in keys_to_remove:
            if key in st.session_state:
                del st.session_state[key]

    def _validate_email(self, email: str) -> bool:
        """Basic email validation"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None


def main():
    """Main function to run the subscription app"""
    # Initialize database
    db = DatabaseManager()

    # Create and render subscription screen
    subscription_screen = SubscriptionScreen(db)
    subscription_screen.render()


if __name__ == "__main__":
    main()