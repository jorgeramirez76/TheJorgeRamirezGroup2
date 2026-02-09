#!/usr/bin/env python3
"""
Import real property data from all 5 NJ counties.
Usage: python import_all_counties.py --county union --city Elizabeth --max-pages 5
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from database import init_db, get_session, add_property
from scorer import calculate_selling_likelihood

# Import all county collectors
from union_county_collector import UnionCountyCollector
from essex_county_collector import EssexCountyCollector
from hudson_county_collector import HudsonCountyCollector
from middlesex_county_collector import MiddlesexCountyCollector
from morris_county_collector import MorrisCountyCollector

COUNTY_COLLECTORS = {
    'union': UnionCountyCollector,
    'essex': EssexCountyCollector,
    'hudson': HudsonCountyCollector,
    'middlesex': MiddlesexCountyCollector,
    'morris': MorrisCountyCollector
}

def main():
    parser = argparse.ArgumentParser(description='Import NJ property data from any county')
    parser.add_argument('--county', required=True, choices=COUNTY_COLLECTORS.keys(),
                       help='County name')
    parser.add_argument('--city', required=True, help='City/municipality name')
    parser.add_argument('--max-pages', type=int, default=5, help='Max pages to fetch')
    args = parser.parse_args()
    
    print(f"Importing from {args.county.title()} County - {args.city}")
    print(f"Max pages: {args.max_pages}\n")
    
    # Initialize
    init_db()
    session = get_session()
    
    # Get collector
    CollectorClass = COUNTY_COLLECTORS[args.county]
    collector = CollectorClass(delay=2.0)
    
    # Import data
    imported = 0
    errors = 0
    
    try:
        for record in collector.search_by_city(args.city, max_pages=args.max_pages):
            try:
                score, reasons = calculate_selling_likelihood(record.to_dict())
                
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
                    print(f"  Imported {imported}...")
                    
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