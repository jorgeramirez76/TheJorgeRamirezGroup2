#!/usr/bin/env python3
"""
Import real Union County property data into the database.
Usage: python import_union_county.py --city Elizabeth --max-pages 5
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from union_county_collector import UnionCountyCollector
from database import init_db, get_session, add_property
from scorer import calculate_sell_score

def main():
    parser = argparse.ArgumentParser(description='Import Union County property data')
    parser.add_argument('--city', required=True, help='City name (e.g., Elizabeth)')
    parser.add_argument('--max-pages', type=int, default=5, help='Max pages to fetch')
    args = parser.parse_args()
    
    print(f"Importing {args.city} properties (max {args.max_pages} pages)...")
    print("This may take several minutes due to rate limiting.\n")
    
    # Initialize database
    init_db()
    session = get_session()
    
    # Collect data
    collector = UnionCountyCollector(delay=2.0)
    
    imported = 0
    errors = 0
    
    try:
        for record in collector.search_by_city(args.city, max_pages=args.max_pages):
            try:
                # Calculate score
                # Create temporary property object for scoring
            from database import Property
            temp_prop = Property(
                address=record.address,
                city=record.city,
                owner_name=record.owner_name,
                assessed_value=record.assessed_value,
                year_built=record.year_built,
                owner_address=None,
                property_type=None
            )
            score, reasons = calculate_sell_score(temp_prop)
                
                # Add to database
                add_property(session,
                    address=record.address,
                    city=record.city,
                    state="NJ",
                    zip_code=record.zip_code,
                    owner_name=record.owner_name,
                    assessed_value=record.assessed_value,
                    year_built=record.year_built,
                    sell_score=score,
                    score_reasons=reasons
                )
                
                imported += 1
                if imported % 10 == 0:
                    print(f"  Imported {imported} records...")
                    
            except Exception as e:
                errors += 1
                print(f"  Error: {e}")
                continue
        
        print(f"\n✓ Complete!")
        print(f"  Imported: {imported}")
        print(f"  Errors: {errors}")
        
    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
    finally:
        collector.close()

if __name__ == "__main__":
    main()