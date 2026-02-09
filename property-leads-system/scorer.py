"""
Selling Likelihood Scoring Engine

Calculates a 0-100 score representing the likelihood that a property
owner will sell in the near future.

Factors considered:
- Years owned (longer = higher score)
- Property age (older = slightly higher)
- Equity position (more equity = higher)
- Market conditions
- Absentee ownership (different mailing address = higher)
- Property distress signals
"""

from datetime import datetime
from database import get_session, Property, update_property

# Scoring weights (should sum to 100)
WEIGHTS = {
    'years_owned': 15,        # Long-term owners more likely to sell
    'property_age': 10,       # Older properties
    'assessed_value': 10,     # Value trends
    'absentee_owner': 20,     # Out-of-state owners more likely to sell
    'property_type': 5,       # Multi-family/probate potential
    'market_timing': 15,      # Seasonal/lifecycle factors
    'distress_signals': 25,   # Tax delinquency, liens, etc.
}


def calculate_years_owned_score(property_record):
    """
    Score based on years owned.
    Owners who've held 5-15 years are most likely to sell.
    """
    # Since we don't have purchase date, use year built as proxy
    # with some randomization for demo
    import random
    
    if property_record.year_built:
        property_age = datetime.now().year - property_record.year_built
        
        # Randomize years "owned" for demo (in reality, use purchase date)
        years_owned = random.randint(2, min(property_age, 30))
        
        if years_owned >= 10 and years_owned <= 20:
            return 80 + random.randint(0, 20)
        elif years_owned >= 5:
            return 60 + random.randint(0, 20)
        elif years_owned >= 2:
            return 40 + random.randint(0, 20)
        else:
            return random.randint(10, 30)
    
    return 50  # Unknown


def calculate_property_age_score(property_record):
    """Score based on property age - older properties often need work."""
    import random
    
    if property_record.year_built:
        age = datetime.now().year - property_record.year_built
        
        if age > 50:
            return 70 + random.randint(0, 30)
        elif age > 30:
            return 50 + random.randint(0, 30)
        elif age > 15:
            return 30 + random.randint(0, 30)
        else:
            return random.randint(10, 40)
    
    return 50


def calculate_value_score(property_record):
    """Score based on assessed value relative to market."""
    import random
    
    if property_record.assessed_value:
        # Higher value properties often have more motivated sellers
        # looking to cash out equity
        if property_record.assessed_value > 500000:
            return 70 + random.randint(0, 30)
        elif property_record.assessed_value > 300000:
            return 50 + random.randint(0, 30)
        else:
            return 30 + random.randint(0, 30)
    
    return 50


def calculate_absentee_score(property_record):
    """Score based on whether owner lives at property."""
    import random
    
    if property_record.owner_address:
        # Owner has different mailing address = absentee
        return 75 + random.randint(0, 25)
    
    # Owner occupies - still possible but lower likelihood
    return 30 + random.randint(0, 30)


def calculate_property_type_score(property_record):
    """Score based on property type."""
    import random
    
    type_scores = {
        'Multi-Family': 80,
        'Commercial': 75,
        'Townhouse': 65,
        'Condo': 60,
        'Single Family': 50
    }
    
    base_score = type_scores.get(property_record.property_type, 50)
    return min(100, base_score + random.randint(-10, 20))


def calculate_market_timing_score(property_record):
    """Score based on market timing factors."""
    import random
    
    # Current month - spring/summer are popular selling times
    current_month = datetime.now().month
    
    if current_month in [3, 4, 5, 6]:  # Spring
        return 70 + random.randint(0, 30)
    elif current_month in [9, 10]:  # Fall
        return 60 + random.randint(0, 30)
    else:
        return 40 + random.randint(0, 30)


def calculate_distress_score(property_record):
    """
    Score based on distress signals.
    In production, this would check:
    - Tax delinquency
    - Foreclosure filings
    - Liens
    - Probate records
    - Divorce filings
    """
    import random
    
    # Demo: Randomly assign distress signals
    # In production, query public records
    distress_roll = random.random()
    
    if distress_roll > 0.9:  # 10% high distress
        reasons = ['Potential tax delinquency', 'Recent probate filing', 'High equity position']
        return 85 + random.randint(0, 15), random.choice(reasons)
    elif distress_roll > 0.7:  # 20% moderate distress
        reasons = ['Long-term ownership', 'Absentee landlord', 'Market timing favorable']
        return 60 + random.randint(0, 20), random.choice(reasons)
    else:
        return 30 + random.randint(0, 30), 'Standard market conditions'


def calculate_sell_score(property_record):
    """
    Calculate overall selling likelihood score.
    
    Returns:
        tuple: (score 0-100, reasons string)
    """
    import random
    
    # Calculate individual factor scores
    years_score = calculate_years_owned_score(property_record)
    age_score = calculate_property_age_score(property_record)
    value_score = calculate_value_score(property_record)
    absentee_score = calculate_absentee_score(property_record)
    type_score = calculate_property_type_score(property_record)
    market_score = calculate_market_timing_score(property_record)
    distress_score, distress_reason = calculate_distress_score(property_record)
    
    # Weighted average
    weighted_score = (
        years_score * WEIGHTS['years_owned'] / 100 +
        age_score * WEIGHTS['property_age'] / 100 +
        value_score * WEIGHTS['assessed_value'] / 100 +
        absentee_score * WEIGHTS['absentee_owner'] / 100 +
        type_score * WEIGHTS['property_type'] / 100 +
        market_score * WEIGHTS['market_timing'] / 100 +
        distress_score * WEIGHTS['distress_signals'] / 100
    )
    
    # Add some randomness for demo
    final_score = min(100, max(0, int(weighted_score + random.randint(-5, 5))))
    
    # Generate reasons string
    reasons = [distress_reason]
    
    if absentee_score > 70:
        reasons.append('Absentee owner')
    if years_score > 70:
        reasons.append('Long ownership period')
    if age_score > 70:
        reasons.append('Older property - potential renovation needs')
    if value_score > 70:
        reasons.append('High value - equity position favorable')
    
    return final_score, '; '.join(reasons[:3])


def score_property(property_id):
    """Score a single property by ID."""
    session = get_session()
    prop = session.query(Property).filter(Property.id == property_id).first()
    
    if not prop:
        session.close()
        return None
    
    score, reasons = calculate_sell_score(prop)
    prop.sell_score = score
    prop.score_reasons = reasons
    session.commit()
    session.close()
    
    return score


def score_all_properties():
    """Score all un-scored properties in the database."""
    session = get_session()
    properties = session.query(Property).all()
    
    scored_count = 0
    for prop in properties:
        if prop.sell_score == 0 or prop.sell_score is None:
            score, reasons = calculate_sell_score(prop)
            prop.sell_score = score
            prop.score_reasons = reasons
            scored_count += 1
    
    session.commit()
    session.close()
    
    return scored_count


def rescore_all_properties():
    """Re-score all properties (even if already scored)."""
    session = get_session()
    properties = session.query(Property).all()
    
    for prop in properties:
        score, reasons = calculate_sell_score(prop)
        prop.sell_score = score
        prop.score_reasons = reasons
    
    session.commit()
    session.close()
    
    return len(properties)


def get_high_value_targets(min_score=70, limit=50):
    """Get the highest-scored leads for outreach."""
    session = get_session()
    
    properties = session.query(Property).filter(
        Property.sell_score >= min_score
    ).order_by(Property.sell_score.desc()).limit(limit).all()
    
    session.close()
    return properties


if __name__ == '__main__':
    # Demo scoring
    from database import init_db, get_all_properties
    
    init_db()
    
    print("Scoring properties...")
    count = score_all_properties()
    print(f"Scored {count} properties")
    
    # Show top 5
    session = get_session()
    top_props = get_all_properties(session, limit=5)
    
    print("\nTop Scored Properties:")
    for prop in top_props:
        print(f"  {prop.address}, {prop.city} - Score: {prop.sell_score}")
        print(f"    Reasons: {prop.score_reasons}")
    
    session.close()