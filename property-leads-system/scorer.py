from datetime import datetime
from typing import Dict, Tuple

def calculate_selling_likelihood(prop: Dict) -> Tuple[float, str]:
    score = 50.0
    reasons = []
    
    try:
        purchase_year = int(str(prop.get('purchase_date', ''))[:4])
        years_held = datetime.now().year - purchase_year
        
        if years_held >= 20:
            score += 20
            reasons.append(f"Long-term owner ({years_held} years)")
        elif years_held >= 10:
            score += 10
            reasons.append(f"Owned {years_held} years")
    except:
        pass
    
    try:
        purchase = float(prop.get('purchase_price', 0) or 0)
        current = float(prop.get('estimated_value', 0) or 0)
        if purchase > 0 and current > 0:
            gain = ((current - purchase) / purchase) * 100
            if gain > 100:
                score += 15
                reasons.append(f"High equity gain ({gain:.0f}%)")
            elif gain > 50:
                score += 10
    except:
        pass
    
    try:
        year_built = int(prop.get('year_built', 0) or 0)
        if year_built > 0:
            age = datetime.now().year - year_built
            if age > 50:
                score += 10
                reasons.append(f"Older home ({age} years)")
    except:
        pass
    
    return round(max(0, min(100, score)), 1), "; ".join(reasons) if reasons else "No indicators"

def get_score_category(score: float) -> str:
    if score >= 80: return "Hot"
    elif score >= 60: return "Warm"
    elif score >= 40: return "Cool"
    else: return "Cold"

def get_score_color(score: float) -> str:
    if score >= 80: return "#ff4444"
    elif score >= 60: return "#ff8800"
    elif score >= 40: return "#ffcc00"
    else: return "#888888"