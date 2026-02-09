#!/usr/bin/env python3
"""Quick test to debug scoring issues."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from database import init_db, get_session, add_property, Property
from scorer import calculate_sell_score

print("Testing scoring system...")

# Initialize
init_db()
session = get_session()

# Create a test property
test_prop_data = {
    'address': '123 Test St',
    'city': 'Elizabeth',
    'state': 'NJ',
    'zip_code': '07201',
    'owner_name': 'Test Owner LLC',
    'property_type': 'Multi-Family',
    'year_built': 1950,
    'assessed_value': 450000.0,
    'owner_address': '456 Different St, New York, NY 10001'
}

# Calculate score
temp_prop = Property(**test_prop_data)
score, reasons = calculate_sell_score(temp_prop)

print(f"\nCalculated Score: {score}")
print(f"Reasons: {reasons}")

# Add to database with score
test_prop_data['sell_score'] = score
test_prop_data['score_reasons'] = reasons

prop = add_property(session, **test_prop_data)
print(f"\nSaved to database with ID: {prop.id}")
print(f"Score in DB: {prop.sell_score}")
print(f"Reasons in DB: {prop.score_reasons}")

# Verify by querying back
from database import get_property_by_id
check_prop = get_property_by_id(session, prop.id)
print(f"\nVerified from DB - Score: {check_prop.sell_score}")

session.close()
print("\nTest complete!")