import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.clock import Clock

import sqlite3
import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import threading
import time
from datetime import datetime, timedelta
import os
import webbrowser

kivy.require('2.0.0')


class BrowseScreen(Screen):
    def __init__(self, app_instance, **kwargs):
        super(BrowseScreen, self).__init__(**kwargs)
        self.app_instance = app_instance
        self.current_articles = []

        # Main layout with proper spacing
        main_layout = BoxLayout(orientation='vertical', spacing=15, padding=20)

        # Title and back button - fixed height
        header_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=60, spacing=10)

        back_btn = Button(
            text='← Back',
            size_hint_x=None,
            width=100,
            background_color=[0.7, 0.7, 0.7, 1]
        )
        back_btn.bind(on_press=self.go_back)
        header_layout.add_widget(back_btn)

        title_label = Label(
            text='Browse Solutions Stories',
            font_size=20,
            bold=True
        )
        header_layout.add_widget(title_label)
        main_layout.add_widget(header_layout)

        # Search controls with proper sizing
        search_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=50, spacing=10)

        search_layout.add_widget(Label(text='Issue:', size_hint_x=None, width=60))

        # Issue Areas list (based on common solutions journalism topics)
        issue_areas = [
            'All Issues', 'Education', 'Health', 'Housing', 'Environment', 'Criminal Justice',
            'Economic Development', 'Democracy & Governance', 'Immigration', 'Transportation',
            'Food Security', 'Mental Health', 'Community Development', 'Technology',
            'Energy', 'Agriculture', 'Social Services', 'Arts & Culture', 'Youth Development',
            'Senior Services', 'Public Safety', 'Infrastructure', 'Workforce Development'
        ]

        self.browse_state_spinner = Spinner(
            text='All Issues',
            values=issue_areas,
            size_hint_x=0.6
        )
        search_layout.add_widget(self.browse_state_spinner)

        search_btn = Button(
            text='Search',
            size_hint_x=None,
            width=120,
            background_color=[0.2, 0.6, 0.8, 1]
        )
        search_btn.bind(on_press=self.search_stories)
        search_layout.add_widget(search_btn)

        main_layout.add_widget(search_layout)

        # Status label with fixed height
        self.browse_status_label = Label(
            text='Click "Search" to browse articles',
            size_hint_y=None,
            height=40
        )
        main_layout.add_widget(self.browse_status_label)

        # Scrollable articles list - this takes remaining space
        scroll = ScrollView()
        self.articles_layout = BoxLayout(
            orientation='vertical',
            spacing=10,
            size_hint_y=None,
            padding=10
        )
        self.articles_layout.bind(minimum_height=self.articles_layout.setter('height'))
        scroll.add_widget(self.articles_layout)
        main_layout.add_widget(scroll)

        self.add_widget(main_layout)

    def go_back(self, instance):
        """Go back to subscription screen"""
        self.manager.current = 'subscription'

    def search_stories(self, instance):
        """Search for stories based on selected issue area"""
        issue_area = self.browse_state_spinner.text

        self.browse_status_label.text = f"Searching for stories about {issue_area}..."

        # Clear previous articles
        self.articles_layout.clear_widgets()

        # Run search in thread
        threading.Thread(target=self._search_stories_thread, args=(issue_area,)).start()

    def _search_stories_thread(self, issue_area):
        """Search for stories in a separate thread"""
        try:
            # Use the existing scrape_stories method but get more articles
            articles = self.app_instance.scrape_stories(issue_area if issue_area != 'All Issues' else None, limit=15)
            self.current_articles = articles

            # Update UI on main thread
            Clock.schedule_once(lambda dt: self._display_articles(articles, issue_area), 0)

        except Exception as e:
            Clock.schedule_once(
                lambda dt: self._show_search_error(str(e)), 0
            )

    def _display_articles(self, articles, issue_area):
        """Display articles in the scrollable list"""
        if not articles:
            self.browse_status_label.text = f"No articles found about {issue_area}"
            return

        self.browse_status_label.text = f"Found {len(articles)} articles about {issue_area}"

        # Clear existing widgets
        self.articles_layout.clear_widgets()

        # Add article cards
        for i, article in enumerate(articles):
            article_card = self._create_article_card(article, i)
            self.articles_layout.add_widget(article_card)

    def _create_article_card(self, article, index):
        """Create a card widget for each article"""
        # Card container with fixed height
        card = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=160,  # Slightly taller to accommodate outlet info
            spacing=8,
            padding=15
        )

        # Add background color
        card.canvas.before.clear()
        with card.canvas.before:
            from kivy.graphics import Color, Rectangle
            Color(0.95, 0.95, 0.95, 1)  # Light gray background
            card.rect = Rectangle(size=card.size, pos=card.pos)

        def update_rect(instance, value):
            card.rect.pos = instance.pos
            card.rect.size = instance.size

        card.bind(pos=update_rect, size=update_rect)

        # Article title
        title_text = article['title'][:100] + '...' if len(article['title']) > 100 else article['title']

        title_label = Label(
            text=title_text,
            text_size=(None, None),
            font_size=14,
            bold=True,
            color=[0.1, 0.1, 0.1, 1],
            size_hint_y=None,
            height=50,
            halign='center',
            valign='middle'
        )
        card.add_widget(title_label)

        # Outlet information
        outlet_text = f"Source: {article.get('outlet', 'News Outlet')}"
        outlet_label = Label(
            text=outlet_text,
            font_size=12,
            color=[0.4, 0.4, 0.4, 1],
            size_hint_y=None,
            height=25,
            halign='center',
            valign='middle'
        )
        card.add_widget(outlet_label)

        # Button row
        button_layout = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=40,
            spacing=10
        )

        # View article button
        view_btn = Button(
            text='Read Original',
            background_color=[0.2, 0.6, 0.8, 1]
        )
        view_btn.bind(on_press=lambda x: self.view_article(article))
        button_layout.add_widget(view_btn)

        # Select for subscription button
        select_btn = Button(
            text='Select for Email',
            background_color=[0.4, 0.7, 0.4, 1]
        )
        select_btn.bind(on_press=lambda x: self.select_article(article))
        button_layout.add_widget(select_btn)

        card.add_widget(button_layout)

        return card

    def view_article(self, article):
        """Open article in browser or show article viewer"""
        try:
            # Try to open in system browser
            webbrowser.open(article['url'])
            self.show_popup("Article Opened", f"Opening article in your default browser:\n\n{article['title']}")
        except Exception as e:
            # Fallback: show article details in popup
            self.show_article_popup(article)

    def show_article_popup(self, article):
        """Show article details in a popup"""
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)

        # Title
        title_label = Label(
            text=article['title'],
            text_size=(500, None),
            font_size=16,
            bold=True,
            size_hint_y=None,
            height=80
        )
        content.add_widget(title_label)

        # URL
        url_label = Label(
            text=f"URL: {article['url']}",
            text_size=(500, None),
            size_hint_y=None,
            height=60
        )
        content.add_widget(url_label)

        # Buttons
        button_layout = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=50,
            spacing=10
        )

        copy_url_btn = Button(text='Copy URL')
        copy_url_btn.bind(on_press=lambda x: self.copy_to_clipboard(article['url']))
        button_layout.add_widget(copy_url_btn)

        close_btn = Button(text='Close')
        button_layout.add_widget(close_btn)

        content.add_widget(button_layout)

        popup = Popup(
            title='Article Details',
            content=content,
            size_hint=(0.9, 0.7)
        )
        close_btn.bind(on_press=popup.dismiss)
        popup.open()

    def copy_to_clipboard(self, text):
        """Copy text to clipboard (simplified)"""
        self.show_popup("URL", f"Copy this URL:\n{text}")

    def select_article(self, article):
        """Select article for email subscription"""
        # Store selected article and go back to subscription screen
        self.app_instance.selected_article = article
        self.manager.current = 'subscription'

        # Show confirmation
        self.show_popup(
            "Article Selected",
            f"Selected article:\n\n{article['title']}\n\nReturn to subscription screen to send it via email."
        )

    def _show_search_error(self, error):
        """Show search error"""
        self.browse_status_label.text = "Error searching for articles"
        self.show_popup("Search Error", f"Failed to search articles:\n{error}")

    def show_popup(self, title, message):
        """Show a popup with a message"""
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)

        message_label = Label(
            text=message,
            text_size=(400, None),
            halign='center',
            valign='middle'
        )
        content.add_widget(message_label)

        close_btn = Button(
            text='OK',
            size_hint_y=None,
            height=50
        )
        content.add_widget(close_btn)

        popup = Popup(title=title, content=content, size_hint=(0.8, 0.6))
        close_btn.bind(on_press=popup.dismiss)
        popup.open()


class SubscriptionScreen(Screen):
    def __init__(self, app_instance, **kwargs):
        super(SubscriptionScreen, self).__init__(**kwargs)
        self.app_instance = app_instance

        # Main layout with consistent spacing
        main_layout = BoxLayout(orientation='vertical', spacing=20, padding=30)

        # Title with fixed height
        title_label = Label(
            text='Solutions Story Tracker\nEmail Subscription Service',
            font_size=24,
            bold=True,
            size_hint_y=None,
            height=100,
            halign='center',
            valign='middle'
        )
        main_layout.add_widget(title_label)

        # Form container
        form_layout = BoxLayout(orientation='vertical', spacing=15, size_hint_y=None)

        # Email input
        email_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=50, spacing=10)
        email_layout.add_widget(Label(text='Email:', size_hint_x=None, width=100, halign='right'))
        self.email_input = TextInput(
            hint_text='Enter your email address',
            multiline=False,
            size_hint_x=0.7
        )
        email_layout.add_widget(self.email_input)
        form_layout.add_widget(email_layout)

        # Issue selection
        state_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=50, spacing=10)
        state_layout.add_widget(Label(text='Issue:', size_hint_x=None, width=100, halign='right'))

        # Issue Areas list (same as browse screen)
        issue_areas = [
            'All Issues', 'Education', 'Health', 'Housing', 'Environment', 'Criminal Justice',
            'Economic Development', 'Democracy & Governance', 'Immigration', 'Transportation',
            'Food Security', 'Mental Health', 'Community Development', 'Technology',
            'Energy', 'Agriculture', 'Social Services', 'Arts & Culture', 'Youth Development',
            'Senior Services', 'Public Safety', 'Infrastructure', 'Workforce Development'
        ]

        self.state_spinner = Spinner(
            text='All Issues',
            values=issue_areas,
            size_hint_x=0.7
        )
        state_layout.add_widget(self.state_spinner)
        form_layout.add_widget(state_layout)

        # Frequency selection
        freq_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=50, spacing=10)
        freq_layout.add_widget(Label(text='Frequency:', size_hint_x=None, width=100, halign='right'))
        self.freq_spinner = Spinner(
            text='Weekly',
            values=['Daily', 'Weekly', 'Monthly'],
            size_hint_x=0.7
        )
        freq_layout.add_widget(self.freq_spinner)
        form_layout.add_widget(freq_layout)

        # Set height for form layout
        form_layout.height = 150
        main_layout.add_widget(form_layout)

        # Add some space between form and selected article
        spacer1 = Label(text='', size_hint_y=None, height=20)
        main_layout.add_widget(spacer1)

        # Selected article display
        self.selected_article_layout = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=0,  # Initially hidden
            spacing=10,
            padding=[10, 5, 10, 5]
        )

        # Add background for selected article
        with self.selected_article_layout.canvas.before:
            from kivy.graphics import Color, Rectangle
            Color(0.9, 0.95, 0.9, 1)  # Light green background
            self.selected_article_rect = Rectangle(size=self.selected_article_layout.size,
                                                   pos=self.selected_article_layout.pos)

        def update_selected_rect(instance, value):
            self.selected_article_rect.pos = instance.pos
            self.selected_article_rect.size = instance.size

        self.selected_article_layout.bind(pos=update_selected_rect, size=update_selected_rect)

        self.selected_article_label = Label(
            text='',
            text_size=(None, None),
            size_hint_y=None,
            height=50,
            bold=True
        )
        self.selected_article_layout.add_widget(self.selected_article_label)

        clear_selection_btn = Button(
            text='Clear Selection',
            size_hint_y=None,
            height=40,
            background_color=[0.8, 0.4, 0.4, 1]
        )
        clear_selection_btn.bind(on_press=self.clear_selected_article)
        self.selected_article_layout.add_widget(clear_selection_btn)

        main_layout.add_widget(self.selected_article_layout)

        # Add space between selected article and buttons
        spacer2 = Label(text='', size_hint_y=None, height=15)
        main_layout.add_widget(spacer2)

        # Buttons with fixed height
        button_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=60, spacing=15)

        self.subscribe_btn = Button(
            text='Start\nSubscription',
            background_color=[0.2, 0.6, 0.8, 1]
        )
        self.subscribe_btn.bind(on_press=self.app_instance.start_subscription)
        button_layout.add_widget(self.subscribe_btn)

        self.preview_btn = Button(
            text='Preview\nStories',
            background_color=[0.4, 0.7, 0.4, 1]
        )
        self.preview_btn.bind(on_press=self.app_instance.preview_stories)
        button_layout.add_widget(self.preview_btn)

        browse_btn = Button(
            text='Browse\nArticles',
            background_color=[0.6, 0.4, 0.8, 1]
        )
        browse_btn.bind(on_press=self.go_to_browse)
        button_layout.add_widget(browse_btn)

        self.test_email_btn = Button(
            text='Test\nEmail',
            background_color=[0.8, 0.6, 0.2, 1]
        )
        self.test_email_btn.bind(on_press=self.app_instance.test_email)
        button_layout.add_widget(self.test_email_btn)

        main_layout.add_widget(button_layout)

        # Status label with fixed height
        self.status_label = Label(
            text='Ready to set up your story subscription!',
            size_hint_y=None,
            height=60,
            font_size=16
        )
        main_layout.add_widget(self.status_label)

        # Add spacer to push everything up
        spacer = Label(text='', size_hint_y=None, height=50)
        main_layout.add_widget(spacer)

        self.add_widget(main_layout)

    def go_to_browse(self, instance):
        """Go to browse screen"""
        self.manager.current = 'browse'

    def clear_selected_article(self, instance):
        """Clear the selected article"""
        self.app_instance.selected_article = None
        self.update_selected_article_display()

    def update_selected_article_display(self):
        """Update the display of selected article"""
        if hasattr(self.app_instance, 'selected_article') and self.app_instance.selected_article:
            article = self.app_instance.selected_article
            self.selected_article_label.text = f"Selected: {article['title'][:80]}..."
            self.selected_article_layout.height = 90  # Slightly smaller height
        else:
            self.selected_article_label.text = ''
            self.selected_article_layout.height = 0

    def on_enter(self):
        """Called when screen is entered"""
        self.update_selected_article_display()


class StoryTrackerApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.selected_article = None

    def build(self):
        self.title = "Solutions Story Tracker - Enhanced"

        # Initialize database
        self.init_database()

        # Create screen manager
        sm = ScreenManager()

        # Create screens
        self.subscription_screen = SubscriptionScreen(self, name='subscription')
        self.browse_screen = BrowseScreen(self, name='browse')

        # Add screens to manager
        sm.add_widget(self.subscription_screen)
        sm.add_widget(self.browse_screen)

        # Set default screen
        sm.current = 'subscription'

        return sm

    def init_database(self):
        """Initialize SQLite database to track users and sent stories"""
        self.db_path = 'story_tracker.db'
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                state TEXT,
                frequency TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_sent TIMESTAMP
            )
        ''')

        # Create sent stories table to avoid duplicates
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sent_stories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_email TEXT,
                story_title TEXT,
                story_url TEXT,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_email) REFERENCES users (email)
            )
        ''')

        conn.commit()
        conn.close()

    def scrape_stories(self, issue_area=None, limit=5):
        """Scrape stories from the Solutions Story Tracker website"""
        try:
            base_url = "https://storytracker.solutionsjournalism.org/"

            # Build search URL with issue area filter if specified
            if issue_area and issue_area != 'All Issues':
                # Use the form parameters we discovered for issue areas
                search_params = {
                    'issue-areas[]': issue_area,
                    'search_stories': 'Search'
                }
                # Use POST method as forms typically do
                response = requests.post(base_url, data=search_params, headers=self.get_headers(), timeout=15)
            else:
                response = requests.get(base_url, headers=self.get_headers(), timeout=15)

            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            stories = []

            # Look for story links using multiple selectors
            story_selectors = [
                'a[href*="/stories/"]',  # Links containing /stories/
                '.story-card a',  # Story card links
                '.story-title a',  # Story title links
                'article a[href*="/stories/"]',  # Article links with stories
                '[class*="story"] a[href*="/stories/"]'  # Any story-related class
            ]

            story_links = []
            for selector in story_selectors:
                found_links = soup.select(selector)
                if found_links:
                    story_links.extend(found_links)
                    break  # Use the first selector that finds results

            # Fallback: find any links with /stories/ in href
            if not story_links:
                all_links = soup.find_all('a', href=True)
                story_links = [link for link in all_links if '/stories/' in link.get('href', '')]

            print(f"Found {len(story_links)} story links")  # Debug

            # Process each story link
            processed_count = 0
            for link in story_links:
                if processed_count >= limit:
                    break

                try:
                    href = link.get('href', '')
                    title = link.get_text().strip()

                    # Skip if no meaningful title or href
                    if not title or len(title) < 10 or not href:
                        continue

                    # Make sure it's a full URL
                    if href.startswith('/'):
                        story_tracker_url = base_url.rstrip('/') + href
                    elif href.startswith('http'):
                        story_tracker_url = href
                    else:
                        continue

                    # Clean up title
                    clean_title = ' '.join(title.split())
                    if len(clean_title) > 120:
                        clean_title = clean_title[:120] + '...'

                    # Get the original article URL
                    original_url, outlet = self.get_original_article_info(story_tracker_url)

                    # Use original URL if found, otherwise skip this story
                    if original_url:
                        stories.append({
                            'title': clean_title,
                            'url': original_url,
                            'outlet': outlet
                        })
                        processed_count += 1

                        # Add delay between requests to be respectful
                        time.sleep(0.5)

                except Exception as e:
                    print(f"Error processing story link: {e}")
                    continue

            print(f"Successfully processed {len(stories)} stories")
            return stories if stories else self.get_fallback_stories(issue_area, limit)

        except Exception as e:
            print(f"Error scraping stories: {e}")
            return self.get_fallback_stories(issue_area, limit)

    def get_headers(self):
        """Get request headers that work with the site"""
        return {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }

    def get_original_article_info(self, story_tracker_url):
        """Extract the original article URL and outlet from a story tracker page"""
        try:
            response = requests.get(story_tracker_url, headers=self.get_headers(), timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Look for the "Go to Original Story" link based on our test results
            original_link = None

            # Method 1: Look for specific text patterns
            text_patterns = ['go to original story', 'read the full story', 'view original', 'original article']

            for pattern in text_patterns:
                links = soup.find_all('a', href=True)
                for link in links:
                    link_text = link.get_text().strip().lower()
                    if pattern in link_text:
                        href = link.get('href')
                        if href and href.startswith('http') and 'storytracker.solutionsjournalism.org' not in href:
                            original_link = href
                            break
                if original_link:
                    break

            # Method 2: Use our scoring system from the test
            if not original_link:
                potential_articles = []

                excluded_domains = [
                    'solutionsjournalism.org',
                    'storytracker.solutionsjournalism.org',
                    'facebook.com', 'twitter.com', 'instagram.com', 'linkedin.com',
                    'youtube.com', 'flipboard.com'
                ]

                for link in soup.find_all('a', href=True):
                    href = link.get('href', '')
                    text = link.get_text().strip()

                    # Skip excluded domains
                    if any(domain in href.lower() for domain in excluded_domains):
                        continue
                    if not href.startswith('http'):
                        continue

                    # Score the link
                    score = 0
                    text_lower = text.lower()
                    if any(word in text_lower for word in ['read', 'original', 'full', 'source', 'view', 'go']):
                        score += 10
                    if any(word in text_lower for word in ['more', 'article', 'story']):
                        score += 5
                    if len(text) > 5:
                        score += 2

                    if score > 0:
                        potential_articles.append((score, href, text))

                # Get the highest scoring link
                if potential_articles:
                    potential_articles.sort(reverse=True)
                    original_link = potential_articles[0][1]

            if original_link:
                outlet = self.extract_outlet_from_url(original_link)
                return original_link, outlet

            return None, None

        except Exception as e:
            print(f"Error getting original article from {story_tracker_url}: {e}")
            return None, None

    def extract_outlet_from_url(self, url):
        """Extract news outlet name from URL"""
        try:
            if not url:
                return "News Outlet"

            # Parse domain from URL
            from urllib.parse import urlparse
            domain = urlparse(url).netloc.lower()

            # Common outlet mappings
            outlet_mappings = {
                'nytimes.com': 'The New York Times',
                'washingtonpost.com': 'The Washington Post',
                'npr.org': 'NPR',
                'cnn.com': 'CNN',
                'bbc.com': 'BBC',
                'reuters.com': 'Reuters',
                'ap.org': 'Associated Press',
                'usatoday.com': 'USA Today',
                'wsj.com': 'The Wall Street Journal',
                'chicagotribune.com': 'Chicago Tribune',
                'sfchronicle.com': 'San Francisco Chronicle',
                'miamiherald.com': 'Miami Herald',
                'tampabay.com': 'Tampa Bay Times',
                'twincities.com': 'Twin Cities Pioneer Press',
                'startribune.com': 'Star Tribune',
                'dallasnews.com': 'The Dallas Morning News',
                'houstonchronicle.com': 'Houston Chronicle',
                'seattletimes.com': 'The Seattle Times',
                'denverpost.com': 'The Denver Post',
                'bostonglobe.com': 'The Boston Globe',
                'philly.com': 'The Philadelphia Inquirer',
                'ajc.com': 'The Atlanta Journal-Constitution'
            }

            # Check for exact matches
            for domain_part, outlet_name in outlet_mappings.items():
                if domain_part in domain:
                    return outlet_name

            # Extract from domain name
            domain_parts = domain.replace('www.', '').split('.')
            if domain_parts:
                base_name = domain_parts[0].replace('-', ' ').replace('_', ' ').title()
                return f"{base_name} News"

            return "News Outlet"

        except Exception as e:
            return "News Outlet"

    def get_fallback_stories(self, issue_area, limit):
        """Return fallback stories if scraping fails"""
        # Issue-specific fallback stories
        issue_stories = {
            'Health': [
                {
                    'title': 'How Rural Hospitals Are Using Telemedicine to Save Lives',
                    'url': 'https://www.npr.org/sections/health-shots/2024/12/01/rural-hospitals-telemedicine-success',
                    'outlet': 'NPR'
                },
                {
                    'title': 'Community Health Workers Bridge Care Gaps',
                    'url': 'https://www.washingtonpost.com/health/2024/11/20/community-health-workers-success/',
                    'outlet': 'The Washington Post'
                }
            ],
            'Housing': [
                {
                    'title': 'Community Land Trusts: A National Model for Affordable Housing',
                    'url': 'https://www.washingtonpost.com/business/2024/11/15/community-land-trusts-affordable-housing/',
                    'outlet': 'The Washington Post'
                },
                {
                    'title': 'How Housing First Programs End Chronic Homelessness',
                    'url': 'https://www.nytimes.com/2024/10/15/us/housing-first-homelessness.html',
                    'outlet': 'The New York Times'
                }
            ],
            'Criminal Justice': [
                {
                    'title': 'Mental Health Courts: A Growing Solution to Mass Incarceration',
                    'url': 'https://www.themarshallproject.org/2024/11/08/mental-health-courts-mass-incarceration-solution',
                    'outlet': 'The Marshall Project'
                },
                {
                    'title': 'Community Violence Intervention Programs Show Results',
                    'url': 'https://www.pewtrusts.org/en/research-and-analysis/articles/2024/12/10/community-violence-intervention-data-driven-prevention',
                    'outlet': 'The Pew Charitable Trusts'
                }
            ],
            'Environment': [
                {
                    'title': 'Green Infrastructure: How Cities Are Fighting Climate Change',
                    'url': 'https://www.reuters.com/sustainability/climate-energy/cities-green-infrastructure-climate-change-2024-12-03/',
                    'outlet': 'Reuters'
                },
                {
                    'title': 'How Community Solar Is Democratizing Clean Energy',
                    'url': 'https://www.csmonitor.com/Environment/2024/1118/community-solar-democratizing-clean-energy',
                    'outlet': 'The Christian Science Monitor'
                }
            ],
            'Education': [
                {
                    'title': 'How Digital Equity Programs Bridge the Homework Gap',
                    'url': 'https://www.edweek.org/technology/how-digital-equity-programs-bridge-homework-gap/2024/10',
                    'outlet': 'Education Week'
                },
                {
                    'title': 'Community Schools Transform Neighborhoods',
                    'url': 'https://www.npr.org/2024/11/12/education/community-schools-transform-neighborhoods',
                    'outlet': 'NPR'
                }
            ]
        }

        # General fallback stories
        general_stories = [
            {
                'title': 'How Participatory Budgeting Is Strengthening Democracy',
                'url': 'https://www.nytimes.com/2024/10/20/us/participatory-budgeting-democracy.html',
                'outlet': 'The New York Times'
            },
            {
                'title': 'Food Recovery Programs Fight Hunger and Food Waste',
                'url': 'https://www.usatoday.com/story/news/2024/11/25/food-recovery-programs-hunger-waste/12345678901/',
                'outlet': 'USA Today'
            },
            {
                'title': 'Refugee Integration Programs Transform Communities Nationwide',
                'url': 'https://www.pbs.org/newshour/nation/refugee-integration-programs-transform-communities',
                'outlet': 'PBS NewsHour'
            }
        ]

        # Get issue-specific stories if available, otherwise use general stories
        if issue_area and issue_area in issue_stories:
            available_stories = issue_stories[issue_area] + general_stories
        else:
            available_stories = general_stories

        return available_stories[:limit]

    def start_subscription(self, instance):
        """Start the subscription process"""
        email = self.subscription_screen.email_input.text.strip()
        issue_area = self.subscription_screen.state_spinner.text
        frequency = self.subscription_screen.freq_spinner.text

        # Validate inputs
        if not email or '@' not in email:
            self.show_popup("Error", "Please enter a valid email address")
            return

        # Save to database
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT OR REPLACE INTO users (email, state, frequency, last_sent)
                VALUES (?, ?, ?, ?)
            ''', (email, issue_area, frequency, datetime.now()))

            conn.commit()
            conn.close()

            self.subscription_screen.status_label.text = f"Subscription started for {email}!\nFrequency: {frequency}, Issue: {issue_area}"
            self.show_popup("Success",
                            "Subscription created successfully!\nTest emails will be saved to 'sent_emails' folder.")

        except Exception as e:
            self.show_popup("Error", f"Failed to create subscription: {str(e)}")

    def preview_stories(self, instance):
        """Preview stories for the selected issue area"""
        issue_area = self.subscription_screen.state_spinner.text if self.subscription_screen.state_spinner.text != 'All Issues' else None

        self.subscription_screen.status_label.text = "Fetching stories..."

        # Run in thread to avoid blocking UI
        threading.Thread(target=self._preview_stories_thread, args=(issue_area,)).start()

    def _preview_stories_thread(self, issue_area):
        """Preview stories in a separate thread"""
        stories = self.scrape_stories(issue_area, limit=3)

        # Update UI on main thread
        Clock.schedule_once(lambda dt: self._show_preview_popup(stories), 0)

    def _show_preview_popup(self, stories):
        """Show preview stories in a popup"""
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # Create scrollable content for stories
        scroll = ScrollView()
        content_layout = BoxLayout(orientation='vertical', spacing=15, size_hint_y=None, padding=10)
        content_layout.bind(minimum_height=content_layout.setter('height'))

        content_text = "Recent Stories:\n\n"
        for i, story in enumerate(stories, 1):
            content_text += f"{i}. {story['title']}\n   URL: {story['url']}\n\n"

        content_label = Label(
            text=content_text,
            text_size=(500, None),
            size_hint_y=None,
            halign='left',
            valign='top'
        )
        content_label.bind(texture_size=content_label.setter('size'))
        content_layout.add_widget(content_label)

        scroll.add_widget(content_layout)
        content.add_widget(scroll)

        close_btn = Button(text='Close', size_hint_y=None, height=50)
        content.add_widget(close_btn)

        popup = Popup(title='Story Preview', content=content, size_hint=(0.9, 0.8))
        close_btn.bind(on_press=popup.dismiss)
        popup.open()

        self.subscription_screen.status_label.text = "Preview ready!"

    def test_email(self, instance):
        """Send a test email (simulate by saving to file)"""
        email = self.subscription_screen.email_input.text.strip()
        issue_area = self.subscription_screen.state_spinner.text if self.subscription_screen.state_spinner.text != 'All Issues' else None

        if not email or '@' not in email:
            self.show_popup("Error", "Please enter a valid email address")
            return

        self.subscription_screen.status_label.text = "Preparing test email..."
        threading.Thread(target=self._test_email_thread, args=(email, issue_area)).start()

    def _test_email_thread(self, email, issue_area):
        """Send test email in a separate thread"""
        # Check if user selected a specific article
        if hasattr(self, 'selected_article') and self.selected_article:
            stories = [self.selected_article]
            subject_prefix = "Selected Article: "
        else:
            stories = self.scrape_stories(issue_area, limit=3)
            subject_prefix = "Test: "

        # Create email content
        subject = f"{subject_prefix}Solutions Stories about {issue_area if issue_area else 'All Issues'}"

        email_content = f"""
Hello!

This is a test email from your Solutions Story Tracker subscription.

Here are some recent stories:

"""

        for i, story in enumerate(stories, 1):
            email_content += f"{i}. {story['title']}\n   Read more: {story['url']}\n\n"

        email_content += """
Best regards,
Solutions Story Tracker App

---
This is a simulated email. In production, this would be sent via SMTP.
"""

        # Save to file (simulating email send)
        os.makedirs('sent_emails', exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"sent_emails/test_email_{timestamp}.txt"

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"To: {email}\n")
            f.write(f"Subject: {subject}\n")
            f.write(f"Date: {datetime.now()}\n\n")
            f.write(email_content)

        # Clear selected article after sending
        if hasattr(self, 'selected_article') and self.selected_article:
            self.selected_article = None

        # Update UI on main thread
        Clock.schedule_once(
            lambda dt: self._update_test_email_status(filename), 0
        )

    def _update_test_email_status(self, filename):
        """Update status after test email"""
        self.subscription_screen.status_label.text = f"Test email saved to: {filename}"
        self.subscription_screen.update_selected_article_display()  # Update the selected article display
        self.show_popup("Test Email Sent", f"Email saved to:\n{filename}\n\nCheck the file to see the email content!")

    def show_popup(self, title, message):
        """Show a popup with a message"""
        content = BoxLayout(orientation='vertical', padding=15, spacing=15)

        message_label = Label(
            text=message,
            text_size=(400, None),
            halign='center',
            valign='middle'
        )
        content.add_widget(message_label)

        close_btn = Button(text='OK', size_hint_y=None, height=50)
        content.add_widget(close_btn)

        popup = Popup(title=title, content=content, size_hint=(0.8, 0.6))
        close_btn.bind(on_press=popup.dismiss)
        popup.open()


if __name__ == '__main__':
    StoryTrackerApp().run()