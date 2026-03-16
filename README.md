# RESPiRE Backend API

A FastAPI-based backend for the RESPiRE air quality monitoring system, designed to serve the Flutter mobile application.

## Features

- **Air Quality Data**: Fetch real-time air quality data from AirGradient sensors
- **IQA Calculation**: Calculate Air Quality Index (IQA) from pollutant measurements
- **Interactive Maps**: Generate HTML maps showing sensor locations and air quality
- **Alert System**: Send SMS and WhatsApp alerts to parents and authorities
- **Sensibilisation Content**: Educational content about air quality and health impacts
- **Data Storage**: Persistent storage of air quality data

## Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file with your API keys:
   ```env
   AIRGRADIENT_TOKEN=your_token_here
   TWILIO_ACCOUNT_SID=your_sid
   TWILIO_AUTH_TOKEN=your_auth_token
   TWILIO_PHONE_NUMBER=your_phone
   WACHAP_ACCESS_TOKEN=your_wachap_token
   WACHAP_INSTANCE_ID=your_instance_id
   ```

## Running the API

Start the server with:
```bash
uvicorn main:app --reload
```

The API will be available at `http://127.0.0.1:8000`

## API Documentation

Once running, visit `http://127.0.0.1:8000/docs` for interactive API documentation.

## API Endpoints

- `GET /` - Health check
- `GET /data/{device_id}` - Get data for specific device
- `GET /data/latest` - Get latest data from all devices
- `GET /map` - Generate interactive map
- `POST /alerts/send` - Send alerts
- `GET /sensibilisation` - Get educational content
- `GET /health` - Health check

## Project Structure

```
backend/
├── main.py              # FastAPI application
├── requirements.txt     # Python dependencies
├── .env                 # Environment variables
├── src/
│   ├── airgradient_api.py    # AirGradient API client
│   ├── iqa_calculator.py     # IQA calculation logic
│   ├── map_service.py        # Map generation
│   ├── alert_service.py      # Alert system (SMS/WhatsApp)
│   ├── sensibilisation.py    # Educational content
│   ├── data_store.py         # Data persistence
│   ├── models.py             # Pydantic models
│   └── utils.py              # Utility functions
├── data/                # Data storage directory
├── archive/             # archived Streamlit-specific files
└── README.md           # This file
```

## Environment Variables

| Variable | Description | Required |
{{ ... }}
| `AIRGRADIENT_TOKEN` | AirGradient API token | Yes |
| `TWILIO_ACCOUNT_SID` | Twilio account SID | No |
| `TWILIO_AUTH_TOKEN` | Twilio auth token | No |
| `TWILIO_PHONE_NUMBER` | Twilio phone number | No |
| `WACHAP_ACCESS_TOKEN` | WaChap access token | No |
| `WACHAP_INSTANCE_ID` | WaChap instance ID | No |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, etc.) | No |

## Development

The backend has been refactored from a Streamlit web application to a clean FastAPI REST API, making it suitable for mobile application consumption.

### Key Changes from Original Streamlit Version:

- Removed all Streamlit UI components
- Converted UI logic to pure Python functions
- Added FastAPI routes with proper request/response models
- Implemented CORS for mobile app access
- Added environment variable configuration
- Unified SMS and WhatsApp alert systems
- Added data persistence layer

## Testing

Test the API endpoints using the interactive documentation at `/docs` or tools like Postman/curl.

Example request:
```bash
curl -X GET "http://127.0.0.1:8000/health"
```

## Deployment

For production deployment, consider using:
- Docker containers
- Reverse proxy (nginx)
- Environment-specific configuration
- Database integration for larger scale
- API rate limiting
- Authentication/Authorization

## License

[Add your license information here]
