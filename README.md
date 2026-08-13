# Pipeline AI - HubSpot Integration

## Overview

This project implements the HubSpot integration required for the Pipeline AI technical assessment.

The implementation supports:

- HubSpot OAuth 2.0 authorization
- OAuth state generation and validation
- Secure temporary credential storage using Redis
- HubSpot access token exchange
- Access token refresh
- HubSpot Contacts API integration
- Pagination of HubSpot contacts
- Conversion of HubSpot contacts into IntegrationItem objects
- React frontend integration
- Loading and displaying HubSpot contacts in the UI

## Tech Stack

### Frontend
- React
- Material UI
- Axios

### Backend
- Python
- FastAPI
- httpx
- Redis

## Project Structure

```text
Pipeline AI Assignment/
├── backend/
│   ├── integrations/
│   │   ├── airtable.py
│   │   ├── hubspot.py
│   │   ├── integration_item.py
│   │   └── notion.py
│   ├── main.py
│   ├── redis_client.py
│   ├── requirements.txt
│   └── .env.example
│
└── frontend/
    └── src/
        ├── data-form.js
        ├── integration-form.js
        └── integrations/
            ├── airtable.js
            ├── hubspot.js
            └── notion.js