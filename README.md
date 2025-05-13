# Hot Pepper Beauty - Google Calendar Integration

This tool synchronizes appointments between Hot Pepper Beauty (Salon Board) and Google Calendar, automating the booking process and preventing double bookings.

## Features

- Automated scraping of Hot Pepper Beauty Salon Board appointments
- Two-way synchronization with Google Calendar
- Prevention of double bookings
- Real-time appointment updates
- Admin dashboard for monitoring and manual synchronization
- Notification system for appointment changes

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment variables:
Create a `.env` file with the following variables:
```
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret
SALON_BOARD_USERNAME=your_username
SALON_BOARD_PASSWORD=your_password
DATABASE_URL=your_database_url
```

3. Set up Google Calendar API:
- Go to Google Cloud Console
- Create a new project
- Enable Google Calendar API
- Create OAuth 2.0 credentials
- Download the credentials and save as `credentials.json`

4. Initialize the database:
```bash
python scripts/init_db.py
```

5. Run the application:
```bash
uvicorn app.main:app --reload
```

## Project Structure

```
├── app/
│   ├── api/            # API endpoints
│   ├── core/           # Core functionality
│   ├── db/             # Database models and connections
│   ├── scrapers/       # Web scraping modules
│   ├── services/       # Business logic
│   └── utils/          # Utility functions
├── scripts/            # Utility scripts
├── tests/              # Test files
├── .env               # Environment variables
├── requirements.txt   # Project dependencies
└── README.md         # Project documentation
```

## Security

- OAuth 2.0 authentication for Google Calendar API
- Secure credential storage
- Rate limiting for API requests
- Input validation and sanitization

## License

MIT License 