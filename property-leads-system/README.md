# Property Lead Manager

A Streamlit app for managing property leads with selling likelihood scoring and Avery 5160 label generation.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the app:
```bash
streamlit run app.py
```

## Features

- **Dashboard**: View stats and property counts by city
- **All Properties**: View complete property list with scores
- **Filter & Export**: Filter by city and score, export to Avery 5160 labels
- **Add Property**: Manually add new properties
- **Import Sample Data**: Generate mock data for testing

## Avery 5160 Labels

The label export generates PDFs formatted for Avery 5160 mailing labels:
- 30 labels per sheet (3 columns x 10 rows)
- Label size: 2-5/8" x 1"
- Compatible with standard address labels

## Scoring System

Selling likelihood score (0-100) based on:
- Years of ownership (longer = higher score)
- Equity gain (more appreciation = higher score)
- Property age (older homes = higher score)

## Data Storage

All data stored locally in SQLite database (`property_leads.db`).