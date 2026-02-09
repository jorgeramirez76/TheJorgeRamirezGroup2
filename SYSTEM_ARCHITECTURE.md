# Homeowner Selling Prediction System - Technical Architecture

## Executive Summary

This document outlines the technical architecture for a system that predicts homeowner selling likelihood using multiple data sources, machine learning scoring, and automated monitoring for NJ counties (Union, Hudson, Middlesex, Morris, Essex).

---

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         DATA COLLECTION LAYER                            │
├───────────────┬───────────────┬───────────────┬─────────────────────────┤
│ Public Records│   APIs        │   Scraping    │   Manual Entry          │
│ (Tax, Deeds)  │ (Zillow, etc) │(Foreclosures) │   (Probate, News)       │
└───────┬───────┴───────┬───────┴───────┬───────┴─────────┬───────────────┘
        │               │               │                 │
        └───────────────┴───────────────┴─────────────────┘
                            │
                    ┌───────▼───────┐
                    │  ETL Pipeline │
                    │   (Python)    │
                    └───────┬───────┘
                            │
┌───────────────────────────▼─────────────────────────────────────────────┐
│                         DATA STORAGE                                     │
│                    ┌─────────────────┐                                   │
│                    │   PostgreSQL    │                                   │
│                    │   - properties  │                                   │
│                    │   - owners      │                                   │
│                    │   - scores      │                                   │
│                    │   - events      │                                   │
│                    └────────┬────────┘                                   │
└─────────────────────────────┼───────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
┌───────▼──────┐    ┌────────▼────────┐   ┌───────▼────────┐
│   SCORING    │    │    MONITORING   │   │     DASHBOARD  │
│    ENGINE    │    │      SYSTEM     │   │    (Web UI)    │
│              │    │                 │   │                │
│ Rule-based   │    │ Change Tracker  │   │ Lead List      │
│ ML Model     │    │ Alert Engine    │   │ Scores         │
└───────┬──────┘    └────────┬────────┘   └───────┬────────┘
        │                    │                     │
        └────────────────────┴─────────────────────┘
                              │
                    ┌─────────▼──────────┐
                    │  SCHEDULER (cron)  │
                    └────────────────────┘
```

---

## Database Schema

### Core Tables

```sql
-- Properties
CREATE TABLE properties (
    id SERIAL PRIMARY KEY,
    property_id VARCHAR(50) UNIQUE,
    address VARCHAR(255),
    city VARCHAR(100),
    county VARCHAR(50),
    state VARCHAR(2),
    zip_code VARCHAR(10),
    property_type VARCHAR(50),
    year_built INTEGER,
    square_feet INTEGER,
    assessed_value DECIMAL(12,2),
    market_value DECIMAL(12,2),
    owner_id INTEGER,
    ownership_years DECIMAL(4,1),
    purchase_price DECIMAL(12,2),
    purchase_date DATE,
    data_source VARCHAR(50),
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Owners
CREATE TABLE owners (
    id SERIAL PRIMARY KEY,
    owner_id VARCHAR(50) UNIQUE,
    full_name VARCHAR(200),
    mailing_address VARCHAR(255),
    mailing_city VARCHAR(100),
    mailing_state VARCHAR(2),
    mailing_zip VARCHAR(10),
    phone VARCHAR(20),
    email VARCHAR(255),
    property_count INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Scores
CREATE TABLE scores (
    id SERIAL PRIMARY KEY,
    property_id INTEGER,
    selling_score INTEGER CHECK (selling_score >= 0 AND selling_score <= 100),
    score_category VARCHAR(20),
    equity_score INTEGER,
    market_score INTEGER,
    life_event_score INTEGER,
    top_factors JSONB,
    scored_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Events
CREATE TABLE events (
    id SERIAL PRIMARY KEY,
    property_id INTEGER,
    owner_id INTEGER,
    event_type VARCHAR(50), -- divorce, foreclosure, probate, bankruptcy
    event_date DATE,
    source VARCHAR(100),
    impact_score INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_properties_zip ON properties(zip_code);
CREATE INDEX idx_properties_county ON properties(county);
CREATE INDEX idx_scores_property ON scores(property_id);
CREATE INDEX idx_scores_score ON scores(selling_score);
CREATE INDEX idx_events_property ON events(property_id);
CREATE INDEX idx_events_type ON events(event_type);
```

---

## Tech Stack Recommendations

| Component | Technology | Cost |
|-----------|-----------|------|
| Database | PostgreSQL | Free (self-hosted) |
| Backend | Python 3.11+ | Free |
| Scheduler | cron / APScheduler | Free |
| Dashboard | Streamlit or Flask | Free |
| Hosting | Raspberry Pi / Old PC | Free |
| ORM | SQLAlchemy | Free |
| Data Collection | requests, BeautifulSoup | Free |

---

## Data Collection Scripts

### Property Records Scraper
```python
# collectors/property_records.py
import requests
from bs4 import BeautifulSoup
import psycopg2
from datetime import datetime

class NJPropertyCollector:
    """Collect property records from NJ counties"""
    
    COUNTY_URLS = {
        'union': 'https://tax1.co.union.nj.us/cgi-bin/prc6.cgi',
        'essex': 'https://www.tax Essex.nj.us/search.aspx',
        'morris': 'https://taxrecords.morriscountynj.gov/search.aspx',
        'middlesex': 'https://mcassessor.middlesexcountynj.gov/search.aspx',
        'hudson': 'https://taxes.hudsoncountynj.org/search.aspx'
    }
    
    def collect_by_zip(self, zip_code, county):
        """Collect properties by ZIP code"""
        # Implementation varies by county
        # Most use ASP.NET forms requiring session handling
        pass
```

### Foreclosure Monitor
```python
# collectors/foreclosure_monitor.py
import feedparser
import requests
from datetime import datetime, timedelta

class ForeclosureMonitor:
    """Monitor foreclosure filings"""
    
    SOURCES = {
        'union': 'https://www.unioncountynj.gov/foreclosures',
        'essex': 'https://www.essexsheriff.com/foreclosures',
        # Add other counties
    }
    
    def check_new_filings(self, days_back=7):
        """Check for new foreclosure filings"""
        pass
```

---

## Scoring Engine

### Simple Rule-Based Scorer
```python
# scoring/engine.py

class SellingLikelihoodScorer:
    """Calculate selling likelihood score 0-100"""
    
    def __init__(self):
        self.weights = {
            'equity': 0.25,
            'life_events': 0.30,
            'market': 0.20,
            'demographics': 0.15,
            'property_age': 0.10
        }
    
    def score_property(self, property_data, events, market_data):
        scores = {}
        
        # Equity score (0-100)
        scores['equity'] = self._score_equity(
            property_data.get('market_value', 0),
            property_data.get('purchase_price', 0),
            property_data.get('ownership_years', 0)
        )
        
        # Life events score
        scores['life_events'] = self._score_life_events(events)
        
        # Market score
        scores['market'] = self._score_market(market_data)
        
        # Weighted total
        total = sum(scores[k] * self.weights[k] for k in scores)
        
        return {
            'total_score': round(total),
            'category': self._categorize(total),
            'component_scores': scores
        }
    
    def _score_equity(self, market_value, purchase_price, years_owned):
        """Score based on equity position"""
        if not purchase_price or not market_value:
            return 50
        
        # Estimate loan balance (simplified amortization)
        if years_owned >= 30:
            equity_pct = 1.0
        else:
            # Rough estimate: paid off 1/30 per year
            equity_pct = 0.2 + (years_owned / 30) * 0.8
            equity_pct += (market_value - purchase_price) / market_value
        
        # Higher equity = higher score (more likely to sell)
        if equity_pct > 0.5:
            return 90
        elif equity_pct > 0.3:
            return 70
        elif equity_pct > 0.1:
            return 50
        else:
            return 30
    
    def _score_life_events(self, events):
        """Score based on life events"""
        if not events:
            return 50
        
        event_scores = {
            'divorce': 95,
            'foreclosure': 100,
            'lis_pendens': 90,
            'probate': 85,
            'bankruptcy': 80,
            'tax_delinquent': 75
        }
        
        max_score = 50
        for event in events:
            score = event_scores.get(event['event_type'], 50)
            max_score = max(max_score, score)
        
        return max_score
    
    def _score_market(self, market_data):
        """Score based on market conditions"""
        if not market_data:
            return 50
        
        # Hot market = more likely to sell
        score = 50
        if market_data.get('price_change_12m', 0) > 5:
            score += 20
        if market_data.get('days_on_market', 60) < 30:
            score += 15
        if market_data.get('inventory_months', 6) < 3:
            score += 15
        
        return min(100, score)
    
    def _categorize(self, score):
        if score >= 70:
            return 'HOT'
        elif score >= 50:
            return 'WARM'
        else:
            return 'COLD'
```

---

## Monitoring System

### Change Tracker
```python
# monitoring/change_tracker.py
import hashlib
from datetime import datetime

class PropertyChangeTracker:
    """Track changes in property records"""
    
    def __init__(self, db_connection):
        self.db = db_connection
    
    def detect_changes(self, property_id, new_data):
        """Detect what changed in property data"""
        old_data = self._get_stored_data(property_id)
        
        changes = []
        for key in new_data:
            if old_data.get(key) != new_data[key]:
                changes.append({
                    'field': key,
                    'old': old_data.get(key),
                    'new': new_data[key]
                })
        
        return changes
    
    def score_changed_significantly(self, property_id, old_score, new_score):
        """Check if score changed enough to alert"""
        if new_score >= 70 and old_score < 70:
            return True  # Became hot lead
        if new_score - old_score >= 20:
            return True  # Significant increase
        return False
```

---

## Dashboard (Streamlit)

```python
# dashboard/app.py
import streamlit as st
import pandas as pd
import psycopg2

def main():
    st.title("Homeowner Selling Prediction Dashboard")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        county = st.selectbox("County", ["All", "Union", "Essex", "Morris", "Middlesex", "Hudson"])
    with col2:
        category = st.selectbox("Category", ["All", "HOT", "WARM", "COLD"])
    with col3:
        min_score = st.slider("Min Score", 0, 100, 70)
    
    # Load leads
    leads = load_leads(county, category, min_score)
    
    # Display
    st.write(f"Found {len(leads)} leads")
    st.dataframe(leads)
    
    # Lead details
    if st.checkbox("Show lead details"):
        lead_id = st.selectbox("Select Lead", leads['id'])
        show_lead_details(lead_id)

def load_leads(county, category, min_score):
    """Load leads from database"""
    conn = psycopg2.connect("dbname=prop_predictor user=postgres")
    query = """
        SELECT p.address, p.city, o.full_name, s.selling_score, s.score_category
        FROM properties p
        JOIN owners o ON p.owner_id = o.id
        JOIN scores s ON s.property_id = p.id
        WHERE s.selling_score >= %s
    """
    return pd.read_sql(query, conn, params=(min_score,))

if __name__ == "__main__":
    main()
```

---

## Deployment

### Self-Hosted (Free Option)
1. **Old PC or Raspberry Pi** (4GB+ RAM)
2. **Ubuntu Server**
3. **PostgreSQL** installed locally
4. **Python environment** with requirements
5. **Cron jobs** for scheduling
6. **Streamlit** running locally on port 8501

### Cloud Option (Low Cost)
- **Digital Ocean droplet**: $6/month
- **PostgreSQL**: Included
- **1TB transfer**: Included

---

## Implementation Roadmap

### Phase 1: MVP (Week 1-2)
- [ ] Set up PostgreSQL database
- [ ] Build property collector for 1 county
- [ ] Create basic scoring engine
- [ ] Build simple Streamlit dashboard

### Phase 2: Expansion (Week 3-4)
- [ ] Add all 5 counties
- [ ] Implement event tracking (foreclosures, tax delinquencies)
- [ ] Add monitoring/alerts
- [ ] Build contact enrichment

### Phase 3: Advanced (Month 2)
- [ ] Machine learning model
- [ ] Automated data collection scheduling
- [ ] Email alerts for hot leads
- [ ] CRM integration

---

## Legal & Compliance Notes

1. **TCPA**: Cannot auto-dial cell phones without consent
2. **DNC Registry**: Check before calling
3. **Data Sources**: Only use publicly available data
4. **Storage**: Secure database, limit access
5. **Emails**: Follow CAN-SPAM if emailing

---

*Document created: February 2026*
*Next steps: Begin Phase 1 implementation*