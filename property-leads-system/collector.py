"""
NJ Property Data Collector
Mock/Demo version for testing the system.
In production, this would connect to NJ property tax records, 
MLS data, or county assessor databases.
"""

import random
from datetime import datetime, timedelta
from database import get_session, add_property

# Sample NJ cities and towns
NJ_CITIES = [
    'Newark', 'Jersey City', 'Paterson', 'Elizabeth', 'Edison', 
    'Woodbridge', 'Lakewood', 'Toms River', 'Hamilton', 'Trenton',
    'Clifton', 'Camden', 'Brick', 'Cherry Hill', 'Passaic',
    'Union City', 'Bayonne', 'East Orange', 'North Bergen', 'Vineland'
]

# Sample street names
STREET_NAMES = [
    'Main St', 'Oak Ave', 'Maple Dr', 'Washington St', 'Park Ave',
    'Lake St', 'Hill Rd', 'River Rd', 'Church St', 'School St',
    'Elm St', 'Pine St', 'Cedar Ln', 'Spruce Ave', 'Birch Dr',
    'Railroad Ave', 'Union Ave', 'Spring St', 'Highland Ave', 'Prospect St'
]

# Sample last names
LAST_NAMES = [
    'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller',
    'Davis', 'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzalez',
    'Wilson', 'Anderson', 'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin'
]

FIRST_NAMES = [
    'James', 'Mary', 'John', 'Patricia', 'Robert', 'Jennifer', 'Michael',
    'Linda', 'William', 'Elizabeth', 'David', 'Barbara', 'Richard', 'Susan',
    'Joseph', 'Jessica', 'Thomas', 'Sarah', 'Charles', 'Karen'
]

PROPERTY_TYPES = ['Single Family', 'Condo', 'Townhouse', 'Multi-Family', 'Commercial']


def generate_address(city=None):
    """Generate a random NJ address."""
    if city is None:
        city = random.choice(NJ_CITIES)
    
    street_num = random.randint(1, 9999)
    street = random.choice(STREET_NAMES)
    zip_code = f'0{random.randint(7001, 8999)}'
    
    return {
        'address': f'{street_num} {street}',
        'city': city,
        'state': 'NJ',
        'zip_code': zip_code
    }


def generate_owner():
    """Generate random owner information."""
    first = random.choice(FIRST_NAMES)
    last = random.choice(LAST_NAMES)
    
    # 20% chance of being an LLC/Company
    if random.random() < 0.2:
        suffixes = ['LLC', 'Properties LLC', 'Realty LLC', 'Investments LLC', 'Corp']
        return f'{last} {random.choice(suffixes)}'
    
    return f'{first} {last}'


def generate_property_data(city=None, count=1):
    """Generate mock property data."""
    properties = []
    
    for _ in range(count):
        addr = generate_address(city)
        
        prop = {
            **addr,
            'owner_name': generate_owner(),
            'owner_address': None,  # Same as property for most
            'property_type': random.choice(PROPERTY_TYPES),
            'year_built': random.randint(1900, 2023) if random.random() > 0.1 else None,
            'assessed_value': round(random.uniform(150000, 800000), 2) if random.random() > 0.1 else None,
            'square_footage': random.randint(800, 4000) if random.random() > 0.1 else None,
            'lot_size': round(random.uniform(0.1, 2.0), 2) if random.random() > 0.2 else None,
            'bedrooms': random.randint(1, 5) if random.random() > 0.1 else None,
            'bathrooms': round(random.uniform(1, 3.5), 1) if random.random() > 0.1 else None,
            'data_source': 'demo_collector'
        }
        
        # 10% chance owner has different mailing address
        if random.random() < 0.1:
            addr2 = generate_address()
            prop['owner_address'] = f"{addr2['address']}\n{addr2['city']}, {addr2['state']} {addr2['zip_code']}"
        
        properties.append(prop)
    
    return properties


def collect_sample_data(city=None, count=50):
    """
    Collect sample property data and save to database WITH SCORES.
    
    Args:
        city: Optional city to filter by
        count: Number of properties to generate
    
    Returns:
        List of created property IDs
    """
    from scorer import calculate_sell_score
    from database import Property
    
    session = get_session()
    properties = generate_property_data(city=city, count=count)
    
    created_ids = []
    for prop_data in properties:
        # Calculate score before saving
        temp_prop = Property(
            address=prop_data['address'],
            city=prop_data['city'],
            owner_name=prop_data['owner_name'],
            assessed_value=prop_data.get('assessed_value'),
            year_built=prop_data.get('year_built'),
            owner_address=prop_data.get('owner_address'),
            property_type=prop_data.get('property_type')
        )
        score, reasons = calculate_sell_score(temp_prop)
        prop_data['sell_score'] = score
        prop_data['score_reasons'] = reasons
        
        prop = add_property(session, **prop_data)
        created_ids.append(prop.id)
    
    session.close()
    return created_ids


def import_from_csv(file_path):
    """
    Placeholder for CSV import functionality.
    Expected columns: address, city, state, zip_code, owner_name
    """
    # TODO: Implement CSV import
    raise NotImplementedError("CSV import coming soon!")


def fetch_nj_property_records(city, county=None):
    """
    Placeholder for actual NJ property record fetching.
    This would integrate with:
    - NJ Property Tax Records
    - County Assessor Databases  
    - Public records APIs
    """
    # TODO: Implement real data fetching
    print(f"Would fetch records for {city}, NJ")
    return generate_property_data(city=city, count=25)


if __name__ == '__main__':
    # Demo: Generate some sample data
    print("Generating sample NJ property data...")
    
    # Import here to avoid circular imports
    from database import init_db
    init_db()
    
    # Generate 100 sample properties
    ids = collect_sample_data(count=100)
    print(f"Created {len(ids)} sample properties")
    print(f"Cities included: {', '.join(random.sample(NJ_CITIES, 5))}")