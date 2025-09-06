# Story Tracker Newsletter App

A newsletter management system for curating and distributing solutions journalism articles from the Solutions Story Tracker website.

## Features

### Public Interface
- **Newsletter Subscription**: Users can subscribe with email and choose 3 topic areas
- **Preference Management**: Subscribers can update their preferences or unsubscribe
- **Clean, Accessible Design**: Simple form interface optimized for all users

### Admin Dashboard
- **Subscriber Management**: View, add, and manage all subscribers
- **Email Campaign Control**: Send newsletters manually or on schedule
- **Article Management**: Monitor scraped articles and manage exclusions
- **Scheduling System**: Automated weekly newsletters and daily scraping
- **Analytics Dashboard**: Track subscriber stats and campaign performance

### Automated Features
- **Daily Article Scraping**: Automatically collects new articles from all topic areas
- **Weekly Newsletter Delivery**: Personalized emails with 3 articles per subscriber
- **Smart Article Selection**: Prevents duplicate sends and uses fallback categories
- **Database Cleanup**: Automatic removal of old articles

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd storytrackerapp
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables** (optional):
   ```bash
   export ADMIN_PASSWORD=your-secure-password
   export EMAIL_FROM_ADDRESS=your-email@yourdomain.edu
   export ENVIRONMENT=production
   ```

## Usage

### Run the Public Subscription Interface
```bash
streamlit run src/main.py
```

### Access Admin Dashboard
1. Navigate to the app URL with `?admin=true` parameter
2. Enter the admin password (default: `admin123`)
3. Or set the `ADMIN_PASSWORD` environment variable

### Development Mode
```bash
# Run with debug mode
export DEBUG=true
streamlit run src/main.py
```

## Configuration

### Environment Variables
- `ADMIN_PASSWORD`: Admin dashboard password
- `EMAIL_FROM_ADDRESS`: From address for emails
- `DATABASE_PATH`: Database file location (default: `story_tracker.db`)
- `EMAIL_OUTPUT_DIR`: Directory for generated email files
- `ENVIRONMENT`: `development` or `production`

### Admin Settings (configurable via dashboard)
- **Email Schedule**: Day of week and time for newsletter delivery
- **Scraping Limits**: Articles per category, retention period
- **Fallback Settings**: Enable/disable category fallbacks

## Database Schema

### Core Tables
- **subscribers**: Email, 3 chosen topics, subscription status
- **articles**: Scraped articles with deduplication
- **email_campaigns**: Campaign tracking and history
- **article_sends**: Tracks which articles were sent to which subscribers
- **admin_settings**: System configuration

## Email System

The app generates HTML email files instead of sending directly, making it suitable for environments with email restrictions (like .edu networks).

### Email Features
- Personalized content based on subscriber preferences
- Fallback category selection when topics have insufficient articles
- Responsive HTML design
- Duplicate prevention per subscriber
- Campaign tracking and analytics

## Article Collection

### Supported Categories
- Education, Health, Housing, Environment
- Criminal Justice, Economic Development
- Democracy & Governance, Immigration
- Transportation, Food Security
- Mental Health, Community Development
- Technology, Energy, Agriculture
- Social Services, Arts & Culture
- Youth Development, Senior Services
- Public Safety, Infrastructure
- Workforce Development

### Scraping Features
- Daily automated collection
- Rate limiting and respectful scraping
- Duplicate detection by URL hash
- Category-based organization
- Article exclusion management

## Scheduling

### Automated Tasks
- **Weekly Newsletter**: Configurable day/time (default: Tuesday 9 AM)
- **Daily Scraping**: Early morning collection (6 AM)
- **Weekly Cleanup**: Remove old articles (Sunday 2 AM)

### Manual Controls
- Trigger newsletter campaigns immediately
- Run article scraping on demand
- Override automated schedules

## File Structure

```
storytrackerapp/
├── src/
│   ├── main.py                 # App entry point
│   ├── models/
│   │   ├── database.py         # Database operations
│   │   └── article.py          # Data models
│   ├── services/
│   │   ├── scraper.py          # Web scraping
│   │   ├── email_service.py    # Email generation
│   │   └── scheduler.py        # Automation
│   ├── screens/
│   │   ├── subscription.py     # Public interface
│   │   └── admin.py           # Admin dashboard
│   └── utils/
│       └── helpers.py         # Utility functions
├── config/
│   └── settings.py            # Configuration
├── emails_output/             # Generated email files
├── requirements.txt
└── README.md
```

## Security

- Admin access protected by password
- Input validation on all forms
- SQL injection prevention with parameterized queries
- Rate limiting on web scraping
- Environment variable configuration for sensitive data

## Future Enhancements

- Real SMTP integration for direct email sending
- API endpoints for external integrations
- Advanced analytics and reporting
- Multiple admin users with role-based access
- Email template customization
- Webhook support for external notifications

## Support

For questions or issues:
1. Check the admin dashboard for system status
2. Review the generated email files in `emails_output/`
3. Check application logs for error details
4. Contact the system administrator

## License

This project is intended for educational and institutional use.
