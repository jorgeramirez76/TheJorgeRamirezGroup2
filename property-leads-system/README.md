# Property Lead Manager

Complete property lead management system for NJ real estate investing.

## Features

- **Property Database**: Store and manage property records
- **Lead Scoring**: 0-100 sell likelihood scores based on 7 factors
- **Avery 5160 Labels**: Generate PDF mailing labels
- **Union County Import**: Scrape real property data from Union County NJ

## Quick Start

1. **Install dependencies:**
```bash
pip3 install streamlit sqlalchemy reportlab beautifulsoup4 lxml requests pandas
```

2. **Start the app:**
```bash
cd ~/.openclaw/workspace/website-repo/property-leads-system
python3 -m streamlit run app.py
```

3. **Open browser:** http://localhost:8501

## Using the App

### Generate Sample Data
- Click "Generate Sample Data" in the sidebar
- Select number of properties (default 50)
- Scores are calculated automatically

### View Properties
- Go to "All Properties" 
- Filter by city, score range
- Click any Property ID to see details
- Expand "View Detailed Scoring Breakdown" to see all factors

### Understanding Scores

Scores are calculated from 7 weighted factors:

| Factor | Weight | Description |
|--------|--------|-------------|
| Years Owned | 15% | Longer ownership = higher score |
| Property Age | 10% | Older properties score higher |
| Assessed Value | 10% | Higher value = more equity |
| Absentee Owner | 20% | Different mailing address = higher |
| Property Type | 5% | Multi-family/commercial = higher |
| Market Timing | 15% | Seasonal trends |
| Distress Signals | 25% | Tax issues, probate, etc. |

**Score Ranges:**
- 🔴 70-100: **Hot Lead** - High likelihood to sell
- 🟠 50-69: **Warm Lead** - Moderate likelihood
- 🟡 30-49: **Cool Lead** - Lower likelihood
- ⚪ 0-29: **Cold Lead** - Unlikely to sell soon

### Export Mailing Labels

1. Go to "Export Labels"
2. Filter by city and score (e.g., min score 70 for hot leads)
3. Click "Generate PDF Labels"
4. Download and print on Avery 5160 label sheets

**Label Specs:** 30 per sheet, 1" x 2-5/8", 3 columns x 10 rows

### Import Real Union County Data

```bash
python3 import_union_county.py --city Elizabeth --max-pages 5
```

Available Union County cities:
- Berkeley Heights, Clark, Cranford, Elizabeth, Fanwood
- Garwood, Hillside, Kenilworth, Linden, Mountainside
- New Providence, Plainfield, Rahway, Roselle, Roselle Park
- Scotch Plains, Springfield, Summit, Union, Westfield, Winfield

## Troubleshooting

**"No module named X" errors:**
```bash
pip3 install streamlit sqlalchemy reportlab beautifulsoup4 lxml requests pandas
```

**All scores showing 0:**
1. Click "🔄 Rescore All" on the Dashboard
2. Or delete `property_leads.db` and regenerate data

**App won't start:**
```bash
# Kill any existing streamlit processes
pkill -f streamlit

# Start fresh
python3 -m streamlit run app.py
```

## File Structure

- `app.py` - Main Streamlit application
- `database.py` - SQLite database models
- `scorer.py` - Scoring engine
- `collector.py` - Sample data generator
- `labels.py` - Avery 5160 PDF label generator
- `union_county_collector.py` - Union County scraper
- `import_union_county.py` - Import script

## Data Storage

All data is stored in `property_leads.db` (SQLite). The database is created automatically when you first run the app.