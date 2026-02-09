"""
Union County NJ Property Tax Records Scraper
URL: https://tax1.co.union.nj.us/cgi-bin/prc6.cgi

DISCLAIMER: For educational purposes. Review website Terms of Service before use.
Implements rate limiting (2 sec delay) to be respectful to the server.
"""

import requests
import time
import logging
import re
from typing import List, Dict, Optional, Generator
from dataclasses import dataclass
from bs4 import BeautifulSoup
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PropertyRecord:
    address: str
    owner_name: str
    city: str
    zip_code: str
    assessed_value: Optional[float]
    lot_size: Optional[str]
    year_built: Optional[int]
    block: Optional[str] = None
    lot: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            'address': self.address,
            'owner_name': self.owner_name,
            'city': self.city,
            'zip_code': self.zip_code,
            'assessed_value': self.assessed_value,
            'lot_size': self.lot_size,
            'year_built': self.year_built,
            'block': self.block,
            'lot': self.lot
        }

class UnionCountyCollector:
    BASE_URL = "https://tax1.co.union.nj.us/cgi-bin/prc6.cgi"
    
    # Union County municipalities
    MUNICIPALITIES = [
        "Berkeley Heights", "Clark", "Cranford", "Elizabeth", "Fanwood",
        "Garwood", "Hillside", "Kenilworth", "Linden", "Mountainside",
        "New Providence", "Plainfield", "Rahway", "Roselle", "Roselle Park",
        "Scotch Plains", "Springfield", "Summit", "Union", "Westfield", "Winfield"
    ]
    
    def __init__(self, delay: float = 2.0):
        self.delay = delay
        self.last_request_time = 0
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Research Bot - Educational)'
        })
    
    def _rate_limit(self):
        elapsed = time.time() - self.last_request_time
        if elapsed < self.delay:
            time.sleep(self.delay - elapsed)
        self.last_request_time = time.time()
    
    def search_by_city(self, city: str, max_pages: Optional[int] = None) -> Generator[PropertyRecord, None, None]:
        """Search for properties by city."""
        city_normalized = city.title()
        logger.info(f"Searching for city: {city_normalized}")
        
        try:
            # Get search form
            self._rate_limit()
            response = self.session.get(self.BASE_URL, timeout=30)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find and submit form
            form = soup.find('form')
            if not form:
                logger.error("No form found")
                return
            
            # Build form data
            form_data = {}
            for input_tag in form.find_all('input'):
                name = input_tag.get('name')
                if name:
                    form_data[name] = input_tag.get('value', '')
            
            # Add municipality
            form_data['municipality'] = city_normalized.upper()
            
            # Submit search
            self._rate_limit()
            response = self.session.post(self.BASE_URL, data=form_data, timeout=30)
            
            page_count = 0
            while True:
                if max_pages and page_count >= max_pages:
                    break
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find results table
                table = soup.find('table')
                if table:
                    rows = table.find_all('tr')[1:]  # Skip header
                    logger.info(f"Page {page_count + 1}: {len(rows)} rows")
                    
                    for row in rows:
                        record = self._parse_row(row, city_normalized)
                        if record:
                            yield record
                
                page_count += 1
                
                # Look for next page
                next_link = None
                for link in soup.find_all('a'):
                    if 'next' in link.get_text().lower():
                        next_link = link.get('href')
                        break
                
                if not next_link:
                    break
                
                self._rate_limit()
                response = self.session.get(f"{self.BASE_URL}?{next_link}", timeout=30)
                
        except Exception as e:
            logger.error(f"Search failed: {e}")
    
    def _parse_row(self, row, city: str) -> Optional[PropertyRecord]:
        """Parse a table row into a PropertyRecord."""
        try:
            cells = row.find_all(['td', 'th'])
            if len(cells) < 3:
                return None
            
            texts = [c.get_text(strip=True) for c in cells]
            
            # Extract fields (heuristic parsing)
            address = None
            owner = None
            assessed = None
            year = None
            
            for text in texts:
                # Look for address (contains numbers and street keywords)
                if not address and any(x in text.lower() for x in ['st', 'ave', 'rd', 'dr']):
                    if any(c.isdigit() for c in text):
                        address = text
                
                # Look for owner (uppercase, no numbers)
                elif not owner and text.isupper() and len(text) > 3:
                    if not any(c.isdigit() for c in text):
                        owner = text.title()
                
                # Look for assessed value ($)
                elif '$' in text and not assessed:
                    assessed = self._parse_money(text)
                
                # Look for year (4 digits)
                elif re.match(r'^(19|20)\d{2}$', text) and not year:
                    year = int(text)
            
            if not address:
                return None
            
            # Extract zip
            zip_code = ""
            zip_match = re.search(r'\b(\d{5})\b', address)
            if zip_match:
                zip_code = zip_match.group(1)
            
            return PropertyRecord(
                address=address,
                owner_name=owner or "Unknown",
                city=city,
                zip_code=zip_code,
                assessed_value=assessed,
                lot_size=None,
                year_built=year
            )
            
        except Exception as e:
            logger.error(f"Parse error: {e}")
            return None
    
    def _parse_money(self, value: str) -> Optional[float]:
        """Parse monetary value."""
        try:
            cleaned = re.sub(r'[$,\s]', '', value)
            return float(cleaned) if cleaned else None
        except:
            return None
    
    def get_municipalities(self) -> List[str]:
        return self.MUNICIPALITIES.copy()
    
    def close(self):
        self.session.close()


if __name__ == "__main__":
    print("Union County NJ Property Tax Records Scraper")
    print("=" * 50)
    print("\nDISCLAIMER: Educational use only. Review Terms of Service.")
    print("\nAvailable municipalities:")
    
    collector = UnionCountyCollector()
    for i, muni in enumerate(collector.get_municipalities(), 1):
        print(f"  {i}. {muni}")
    
    print("\nExample:")
    print("  from union_county_collector import UnionCountyCollector")
    print("  collector = UnionCountyCollector()")
    print("  for record in collector.search_by_city('Elizabeth', max_pages=2):")
    print("      print(record)")
    
    collector.close()