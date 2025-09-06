import os
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path

from src.models.database import DatabaseManager
from src.models.article import Article, Subscriber, ArticleSelector


class EmailService:
    """Handles email generation and delivery for the Story Tracker app"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.article_selector = ArticleSelector(db_manager)
        self.output_dir = Path("emails_output")
        self.output_dir.mkdir(exist_ok=True)

    def generate_newsletter_for_subscriber(self, subscriber: Subscriber, campaign_id: int) -> Optional[str]:
        """
        Generate newsletter content for a single subscriber
        Returns the email content as HTML string
        """
        # Select articles for subscriber
        selected_articles = self.article_selector.select_articles_for_subscriber(subscriber)

        if not any(selected_articles.values()):
            print(f"No articles found for subscriber {subscriber.email}")
            return None

        # Record article sends in database
        for issue_area, articles in selected_articles.items():
            for article in articles:
                if article.id:
                    self.db.record_article_send(subscriber.id, article.id, campaign_id)

        # Generate HTML email content
        html_content = self._generate_html_email(subscriber, selected_articles)

        return html_content

    def send_newsletter_campaign(self, campaign_type: str = 'scheduled',
                                 manual_articles: Optional[List[int]] = None) -> Dict:
        """
        Send newsletter campaign to all active subscribers
        Returns summary of the campaign
        """
        # Get all active subscribers
        subscribers_data = self.db.get_all_active_subscribers()
        subscribers = [Subscriber.from_dict(data) for data in subscribers_data]

        if not subscribers:
            return {"success": False, "message": "No active subscribers found"}

        # Create campaign record
        campaign_id = self.db.create_campaign(
            campaign_type=campaign_type,
            notes=f"Campaign sent to {len(subscribers)} subscribers"
        )

        successful_sends = 0
        failed_sends = 0
        all_articles_sent = set()

        print(f"Starting campaign {campaign_id} for {len(subscribers)} subscribers...")

        for subscriber in subscribers:
            try:
                if manual_articles:
                    # Manual campaign with specific articles
                    html_content = self._generate_manual_campaign_email(
                        subscriber, manual_articles, campaign_id
                    )
                else:
                    # Regular personalized campaign
                    html_content = self.generate_newsletter_for_subscriber(subscriber, campaign_id)

                if html_content:
                    # Save email to file
                    self._save_email_to_file(subscriber.email, html_content, campaign_id)
                    successful_sends += 1
                    print(f"✓ Generated email for {subscriber.email}")
                else:
                    failed_sends += 1
                    print(f"✗ Failed to generate email for {subscriber.email}")

            except Exception as e:
                failed_sends += 1
                print(f"✗ Error generating email for {subscriber.email}: {e}")

        # Mark campaign as sent
        if successful_sends > 0:
            self.db.mark_campaign_sent(campaign_id, successful_sends, list(all_articles_sent))

        # Generate campaign summary
        summary = {
            "success": True,
            "campaign_id": campaign_id,
            "total_subscribers": len(subscribers),
            "successful_sends": successful_sends,
            "failed_sends": failed_sends,
            "timestamp": datetime.now().isoformat()
        }

        # Save campaign summary
        self._save_campaign_summary(campaign_id, summary)

        print(f"\nCampaign {campaign_id} completed:")
        print(f"✓ Successful: {successful_sends}")
        print(f"✗ Failed: {failed_sends}")

        return summary

    def _generate_html_email(self, subscriber: Subscriber,
                             selected_articles: Dict[str, List[Article]]) -> str:
        """Generate HTML email content for subscriber"""

        # Count total articles
        total_articles = sum(len(articles) for articles in selected_articles.values())

        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Your Weekly Solutions Stories</title>
    <style>
        body {{
            font-family: Georgia, 'Times New Roman', serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f9f9f9;
        }}
        .email-container {{
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
            border-bottom: 3px solid #2c5aa0;
            padding-bottom: 20px;
        }}
        .header h1 {{
            color: #2c5aa0;
            margin: 0;
            font-size: 28px;
        }}
        .header .date {{
            color: #666;
            font-size: 16px;
            margin-top: 5px;
        }}
        .issue-section {{
            margin-bottom: 35px;
            border-left: 4px solid #2c5aa0;
            padding-left: 20px;
        }}
        .issue-title {{
            color: #2c5aa0;
            font-size: 20px;
            font-weight: bold;
            margin-bottom: 15px;
            border-bottom: 1px solid #eee;
            padding-bottom: 8px;
        }}
        .article {{
            margin-bottom: 20px;
            padding: 15px;
            background-color: #fafafa;
            border-radius: 5px;
        }}
        .article-title {{
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 8px;
        }}
        .article-title a {{
            color: #2c5aa0;
            text-decoration: none;
        }}
        .article-title a:hover {{
            text-decoration: underline;
        }}
        .article-meta {{
            font-size: 14px;
            color: #666;
            font-style: italic;
        }}
        .fallback-notice {{
            background-color: #fff3cd;
            border: 1px solid #ffeaa7;
            color: #856404;
            padding: 10px;
            border-radius: 4px;
            font-size: 14px;
            margin-bottom: 15px;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #eee;
            text-align: center;
            font-size: 14px;
            color: #666;
        }}
        .footer a {{
            color: #2c5aa0;
            text-decoration: none;
        }}
    </style>
</head>
<body>
    <div class="email-container">
        <div class="header">
            <h1>Your Weekly Solutions Stories</h1>
            <div class="date">{datetime.now().strftime('%B %d, %Y')}</div>
        </div>

        <p>Hello!</p>
        <p>Here are your personalized solutions stories for this week, featuring {total_articles} article{'s' if total_articles != 1 else ''} across your chosen topics.</p>
"""

        # Add each issue section
        for issue_area in subscriber.issue_areas:
            articles = selected_articles.get(issue_area, [])

            html_content += f'<div class="issue-section">\n'
            html_content += f'<div class="issue-title">{issue_area}</div>\n'

            # Check if fallback was used
            if self.article_selector.was_fallback_used(issue_area):
                html_content += '''
                <div class="fallback-notice">
                    <strong>Note:</strong> We included some articles from related categories to ensure you have fresh content this week.
                </div>
                '''

            if articles:
                for article in articles:
                    html_content += f'''
                <div class="article">
                    <div class="article-title">
                        <a href="{article.url}" target="_blank">{article.title}</a>
                    </div>
                    <div class="article-meta">
                        Source: {article.outlet or 'Unknown'} • Category: {article.issue_area}
                    </div>
                </div>
                '''
            else:
                html_content += '''
                <div class="article">
                    <div class="article-meta">
                        No new articles available in this category this week. Check back next week!
                    </div>
                </div>
                '''

            html_content += '</div>\n'

        # Add footer
        html_content += f"""
        <div class="footer">
            <p>This email was generated for {subscriber.email}</p>
            <p>These solutions stories highlight positive, actionable approaches to social issues.</p>
            <p><a href="#">Update your preferences</a> | <a href="#">Unsubscribe</a></p>
        </div>
    </div>
</body>
</html>
"""

        return html_content

    def _generate_manual_campaign_email(self, subscriber: Subscriber,
                                        article_ids: List[int], campaign_id: int) -> str:
        """Generate email for manual campaign with specific articles"""

        # Get article details
        articles = []
        conn = self.db.get_connection()
        cursor = conn.cursor()

        for article_id in article_ids:
            cursor.execute('''
                SELECT id, title, url, outlet, issue_area, scraped_at
                FROM articles WHERE id = ?
            ''', (article_id,))

            row = cursor.fetchone()
            if row:
                article = Article(
                    id=row[0],
                    title=row[1],
                    url=row[2],
                    outlet=row[3],
                    issue_area=row[4],
                    scraped_at=datetime.fromisoformat(row[5]) if row[5] else None
                )
                articles.append(article)

                # Record send
                self.db.record_article_send(subscriber.id, article_id, campaign_id)

        conn.close()

        if not articles:
            return None

        # Generate HTML for manual campaign
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Special Solutions Stories Collection</title>
    <style>
        /* Same CSS as regular email */
        body {{
            font-family: Georgia, 'Times New Roman', serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f9f9f9;
        }}
        .email-container {{
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
            border-bottom: 3px solid #d63384;
            padding-bottom: 20px;
        }}
        .header h1 {{
            color: #d63384;
            margin: 0;
            font-size: 28px;
        }}
        .article {{
            margin-bottom: 25px;
            padding: 20px;
            background-color: #fafafa;
            border-radius: 5px;
            border-left: 4px solid #d63384;
        }}
        .article-title {{
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 8px;
        }}
        .article-title a {{
            color: #d63384;
            text-decoration: none;
        }}
        .article-meta {{
            font-size: 14px;
            color: #666;
            font-style: italic;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #eee;
            text-align: center;
            font-size: 14px;
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="email-container">
        <div class="header">
            <h1>Special Solutions Stories</h1>
            <div class="date">{datetime.now().strftime('%B %d, %Y')}</div>
        </div>

        <p>Hello!</p>
        <p>We've curated a special collection of {len(articles)} solutions stor{'ies' if len(articles) != 1 else 'y'} that we think you'll find particularly inspiring.</p>
"""

        # Add articles
        for article in articles:
            html_content += f'''
            <div class="article">
                <div class="article-title">
                    <a href="{article.url}" target="_blank">{article.title}</a>
                </div>
                <div class="article-meta">
                    Source: {article.outlet or 'Unknown'} • Category: {article.issue_area}
                </div>
            </div>
            '''

        html_content += f"""
        <div class="footer">
            <p>This special collection was sent to {subscriber.email}</p>
            <p><a href="#">Update your preferences</a> | <a href="#">Unsubscribe</a></p>
        </div>
    </div>
</body>
</html>
"""

        return html_content

    def _save_email_to_file(self, email: str, html_content: str, campaign_id: int):
        """Save generated email to file"""
        safe_email = email.replace('@', '_at_').replace('.', '_')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"campaign_{campaign_id}_{safe_email}_{timestamp}.html"

        filepath = self.output_dir / filename
        filepath.write_text(html_content, encoding='utf-8')

        print(f"Email saved to: {filepath}")

    def _save_campaign_summary(self, campaign_id: int, summary: Dict):
        """Save campaign summary to file"""
        import json

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"campaign_summary_{campaign_id}_{timestamp}.json"

        filepath = self.output_dir / filename
        filepath.write_text(json.dumps(summary, indent=2), encoding='utf-8')

        print(f"Campaign summary saved to: {filepath}")

    def preview_newsletter_for_subscriber(self, subscriber_email: str) -> Optional[str]:
        """Generate preview of newsletter for a subscriber without recording sends"""

        subscriber_data = self.db.get_subscriber_by_email(subscriber_email)
        if not subscriber_data:
            return None

        subscriber = Subscriber.from_dict(subscriber_data)

        # Create temporary campaign for preview (won't be marked as sent)
        temp_campaign_id = self.db.create_campaign('preview', notes='Preview generation')

        # Select articles (but don't record sends)
        selected_articles = self.article_selector.select_articles_for_subscriber(subscriber)

        # Generate HTML without recording sends
        html_content = self._generate_html_email(subscriber, selected_articles)

        return html_content

    def get_campaign_statistics(self, days: int = 30) -> Dict:
        """Get email campaign statistics for the last N days"""
        from datetime import timedelta

        cutoff_date = datetime.now() - timedelta(days=days)

        conn = self.db.get_connection()
        cursor = conn.cursor()

        # Get campaign counts
        cursor.execute('''
            SELECT status, COUNT(*) 
            FROM email_campaigns 
            WHERE sent_at >= ? OR scheduled_for >= ?
            GROUP BY status
        ''', (cutoff_date, cutoff_date))

        campaign_stats = dict(cursor.fetchall())

        # Get total sends
        cursor.execute('''
            SELECT COUNT(*) 
            FROM article_sends s
            JOIN email_campaigns c ON s.campaign_id = c.id
            WHERE s.sent_at >= ?
        ''', (cutoff_date,))

        total_sends = cursor.fetchone()[0]

        conn.close()

        return {
            'campaign_stats': campaign_stats,
            'total_sends': total_sends,
            'period_days': days,
            'generated_at': datetime.now().isoformat()
        }