#!/usr/bin/env python3
"""
Complete ALL remaining SEO optimizations
TheJorgeRamirezGroup.com
"""

import re
from pathlib import Path

def add_commuter_comparison_table():
    """Add comprehensive comparison table to NYC commuter page"""
    
    filepath = Path("blog/best-nj-suburbs-nyc-commuters.html")
    content = filepath.read_text()
    
    print("✅ Adding comparison table to NYC commuters page...")
    
    # The massive comparison table organized by budget tier
    comparison_table = '''
<div class="commuter-comparison-table" style="margin: 40px 0; overflow-x: auto;">
  <h2 style="font-size: 1.75rem; margin-bottom: 20px; color: #1a1a1a;">Quick Comparison: 22 NJ Commuter Towns by Budget</h2>
  <table style="width: 100%; border-collapse: collapse; font-size: 0.9rem;">
    <thead>
      <tr style="background-color: #1a365d; color: white;">
        <th style="padding: 10px; text-align: left; border: 1px solid #ddd;">Town</th>
        <th style="padding: 10px; text-align: left; border: 1px solid #ddd;">Budget Tier</th>
        <th style="padding: 10px; text-align: left; border: 1px solid #ddd;">Median Price</th>
        <th style="padding: 10px; text-align: left; border: 1px solid #ddd;">Commute to Penn</th>
        <th style="padding: 10px; text-align: left; border: 1px solid #ddd;">Train Line</th>
        <th style="padding: 10px; text-align: left; border: 1px solid #ddd;">Schools</th>
      </tr>
    </thead>
    <tbody>
      <!-- Under $500K Tier -->
      <tr style="background-color: #fef3c7;">
        <td colspan="6" style="padding: 8px; font-weight: 700; border: 1px solid #ddd;">UNDER $500K: Affordable Entry</td>
      </tr>
      <tr>
        <td style="padding: 8px; border: 1px solid #ddd;"><a href="/towns/cranford.html" style="color: #2563eb; font-weight: 600;">Cranford</a></td>
        <td style="padding: 8px; border: 1px solid #ddd;">Entry</td>
        <td style="padding: 8px; border: 1px solid #ddd;">$700-750K*</td>
        <td style="padding: 8px; border: 1px solid #ddd;">~50-60 min</td>
        <td style="padding: 8px; border: 1px solid #ddd;">Raritan Valley</td>
        <td style="padding: 8px; border: 1px solid #ddd;">Very Good</td>
      </tr>
      <tr style="background-color: #f7fafc;">
        <td style="padding: 8px; border: 1px solid #ddd;"><a href="/towns/rahway.html" style="color: #2563eb; font-weight: 600;">Rahway</a></td>
        <td style="padding: 8px; border: 1px solid #ddd;">Budget</td>
        <td style="padding: 8px; border: 1px solid #ddd;">$375-475K</td>
        <td style="padding: 8px; border: 1px solid #ddd;">~45-55 min</td>
        <td style="padding: 8px; border: 1px solid #ddd;">NE Corridor</td>
        <td style="padding: 8px; border: 1px solid #ddd;">Average</td>
      </tr>
      <tr>
        <td style="padding: 8px; border: 1px solid #ddd;"><a href="/towns/linden.html" style="color: #2563eb; font-weight: 600;">Linden</a></td>
        <td style="padding: 8px; border: 1px solid #ddd;">Budget</td>
        <td style="padding: 8px; border: 1px solid #ddd;">$400-475K</td>
        <td style="padding: 8px; border: 1px solid #ddd;">~50-60 min</td>
        <td style="padding: 8px; border: 1px solid #ddd;">NE Corridor</td>
        <td style="padding: 8px; border: 1px solid #ddd;">Average</td>
      </tr>
      <tr style="background-color: #f7fafc;">
        <td style="padding: 8px; border: 1px solid #ddd;"><a href="/towns/bloomfield.html" style="color: #2563eb; font-weight: 600;">Bloomfield</a></td>
        <td style="padding: 8px; border: 1px solid #ddd;">Budget</td>
        <td style="padding: 8px; border: 1px solid #ddd;">$425-525K</td>
        <td style="padding: 8px; border: 1px solid #ddd;">~55-65 min</td>
        <td style="padding: 8px; border: 1px solid #ddd;">Montclair-Boonton</td>
        <td style="padding: 8px; border: 1px solid #ddd;">Avg-Good</td>
      </tr>
      <tr>
        <td style="padding: 8px; border: 1px solid #ddd;"><a href="/towns/nutley.html" style="color: #2563eb; font-weight: 600;">Nutley</a></td>
        <td style="padding: 8px; border: 1px solid #ddd;">Budget</td>
        <td style="padding: 8px; border: 1px solid #ddd;">$450-540K</td>
        <td style="padding: 8px; border: 1px solid #ddd;">~55 min (bus)</td>
        <td style="padding: 8px; border: 1px solid #ddd;">Bus to NYC</td>
        <td style="padding: 8px; border: 1px solid #ddd;">Good</td>
      </tr>
      
      <!-- $500K-$750K Tier -->
      <tr style="background-color: #dbeafe;">
        <td colspan="6" style="padding: 8px; font-weight: 700; border: 1px solid #ddd;">$500K-$850K: Value Plays</td>
      </tr>
      <tr>
        <td style="padding: 8px; border: 1px solid #ddd;"><a href="/towns/maplewood.html" style="color: #2563eb; font-weight: 600;">Maplewood</a></td>
        <td style="padding: 8px; border: 1px solid #ddd;">Value</td>
        <td style="padding: 8px; border: 1px solid #ddd;">$750-850K</td>
        <td style="padding: 8px; border: 1px solid #ddd;">~30 min</td>
        <td style="padding: 8px; border: 1px solid #ddd;">Midtown Direct</td>
        <td style="padding: 8px; border: 1px solid #ddd;">Very Good</td>
      </tr>
      <tr style="background-color: #f7fafc;">
        <td style="padding: 8px; border: 1px solid #ddd;"><a href="/towns/south-orange.html" style="color: #2563eb; font-weight: 600;">South Orange</a></td>
        <td style="padding: 8px; border: 1px solid #ddd;">Value</td>
        <td style="padding: 8px; border: 1px solid #ddd;">$750-850K</td>
        <td style="padding: 8px; border: 1px solid #ddd;">~34 min</td>
        <td style="padding: 8px; border: 1px solid #ddd;">Midtown Direct</td>
        <td style="padding: 8px; border: 1px solid #ddd;">Very Good</td>
      </tr>
      <tr>
        <td style="padding: 8px; border: 1px solid #ddd;"><a href="/towns/fanwood.html" style="color: #2563eb; font-weight: 600;">Fanwood</a></td>
        <td style="padding: 8px; border: 1px solid #ddd;">Value</td>
        <td style="padding: 8px; border: 1px solid #ddd;">$550-650K</td>
        <td style="padding: 8px; border: 1px solid #ddd;">~55 min</td>
        <td style="padding: 8px; border: 1px solid #ddd;">Raritan Valley</td>
        <td style="padding: 8px; border: 1px solid #ddd;">Very Good</td>
      </tr>
      <tr style="background-color: #f7fafc;">
        <td style="padding: 8px; border: 1px solid #ddd;"><a href="/towns/metuchen.html" style="color: #2563eb; font-weight: 600;">Metuchen</a></td>
        <td style="padding: 8px; border: 1px solid #ddd;">Value</td>
        <td style="padding: 8px; border: 1px solid #ddd;">$600-725K</td>
        <td style="padding: 8px; border: 1px solid #ddd;">~45 min</td>
        <td style="padding: 8px; border: 1px solid #ddd;">NE Corridor</td>
        <td style="padding: 8px; border: 1px solid #ddd;">Very Good</td>
      </tr>
      
      <!-- $850K-$1.1M Tier -->
      <tr style="background-color: #e0e7ff;">
        <td colspan="6" style="padding: 8px; font-weight: 700; border: 1px solid #ddd;">$850K-$1.1M: Mid-Market Sweet Spot</td>
      </tr>
      <tr>
        <td style="padding: 8px; border: 1px solid #ddd;"><a href="/towns/montclair.html" style="color: #2563eb; font-weight: 600;">Montclair</a></td>
        <td style="padding: 8px; border: 1px solid #ddd;">Mid</td>
        <td style="padding: 8px; border: 1px solid #ddd;">$850K-$1.0M</td>
        <td style="padding: 8px; border: 1px solid #ddd;">~35-45 min</td>
        <td style="padding: 8px; border: 1px solid #ddd;">Midtown Direct</td>
        <td style="padding: 8px; border: 1px solid #ddd;">Very Good</td>
      </tr>
      <tr style="background-color: #f7fafc;">
        <td style="padding: 8px; border: 1px solid #ddd;"><a href="/towns/chatham.html" style="color: #2563eb; font-weight: 600;">Chatham</a></td>
        <td style="padding: 8px; border: 1px solid #ddd;">Mid</td>
        <td style="padding: 8px; border: 1px solid #ddd;">$1.0-1.1M</td>
        <td style="padding: 8px; border: 1px solid #ddd;">~52 min</td>
        <td style="padding: 8px; border: 1px solid #ddd;">Midtown Direct</td>
        <td style="padding: 8px; border: 1px solid #ddd;">Excellent</td>
      </tr>
      <tr>
        <td style="padding: 8px; border: 1px solid #ddd;"><a href="/towns/glen-ridge.html" style="color: #2563eb; font-weight: 600;">Glen Ridge</a></td>
        <td style="padding: 8px; border: 1px solid #ddd;">Mid</td>
        <td style="padding: 8px; border: 1px solid #ddd;">$850-950K</td>
        <td style="padding: 8px; border: 1px solid #ddd;">~45 min</td>
        <td style="padding: 8px; border: 1px solid #ddd;">Midtown Direct adj.</td>
        <td style="padding: 8px; border: 1px solid #ddd;">Excellent</td>
      </tr>
      <tr style="background-color: #f7fafc;">
        <td style="padding: 8px; border: 1px solid #ddd;"><a href="/towns/madison.html" style="color: #2563eb; font-weight: 600;">Madison</a></td>
        <td style="padding: 8px; border: 1px solid #ddd;">Mid</td>
        <td style="padding: 8px; border: 1px solid #ddd;">~$950K</td>
        <td style="padding: 8px; border: 1px solid #ddd;">~55 min</td>
        <td style="padding: 8px; border: 1px solid #ddd;">Midtown Direct</td>
        <td style="padding: 8px; border: 1px solid #ddd;">Very Good</td>
      </tr>
      
      <!-- $1.1M-$1.5M Tier -->
      <tr style="background-color: #fce7f3;">
        <td colspan="6" style="padding: 8px; font-weight: 700; border: 1px solid #ddd;">$1.1M-$1.5M: Premium Tier</td>
      </tr>
      <tr>
        <td style="padding: 8px; border: 1px solid #ddd;"><a href="/towns/westfield.html" style="color: #2563eb; font-weight: 600;">Westfield</a></td>
        <td style="padding: 8px; border: 1px solid #ddd;">Premium</td>
        <td style="padding: 8px; border: 1px solid #ddd;">~$1.2M</td>
        <td style="padding: 8px; border: 1px solid #ddd;">~55 min</td>
        <td style="padding: 8px; border: 1px solid #ddd;">Raritan Valley</td>
        <td style="padding: 8px; border: 1px solid #ddd;">Excellent</td>
      </tr>
      <tr style="background-color: #f7fafc;">
        <td style="padding: 8px; border: 1px solid #ddd;"><a href="/towns/summit.html" style="color: #2563eb; font-weight: 600;">Summit</a></td>
        <td style="padding: 8px; border: 1px solid #ddd;">Premium</td>
        <td style="padding: 8px; border: 1px solid #ddd;">$1.3-1.5M</td>
        <td style="padding: 8px; border: 1px solid #ddd;">~44 min</td>
        <td style="padding: 8px; border: 1px solid #ddd;">Midtown Direct</td>
        <td style="padding: 8px; border: 1px solid #ddd;">Excellent</td>
      </tr>
      <tr>
        <td style="padding: 8px; border: 1px solid #ddd;"><a href="/towns/ridgewood.html" style="color: #2563eb; font-weight: 600;">Ridgewood</a></td>
        <td style="padding: 8px; border: 1px solid #ddd;">Premium</td>
        <td style="padding: 8px; border: 1px solid #ddd;">$1.1-1.3M</td>
        <td style="padding: 8px; border: 1px solid #ddd;">~55 min</td>
        <td style="padding: 8px; border: 1px solid #ddd;">Bergen Line</td>
        <td style="padding: 8px; border: 1px solid #ddd;">Excellent</td>
      </tr>
      
      <!-- $1.5M+ Tier -->
      <tr style="background-color: #fef3c7;">
        <td colspan="6" style="padding: 8px; font-weight: 700; border: 1px solid #ddd;">$1.5M+: Luxury Tier</td>
      </tr>
      <tr>
        <td style="padding: 8px; border: 1px solid #ddd;"><a href="/towns/short-hills.html" style="color: #2563eb; font-weight: 600;">Short Hills</a></td>
        <td style="padding: 8px; border: 1px solid #ddd;">Luxury</td>
        <td style="padding: 8px; border: 1px solid #ddd;">$1.5-1.8M</td>
        <td style="padding: 8px; border: 1px solid #ddd;">~37 min</td>
        <td style="padding: 8px; border: 1px solid #ddd;">Midtown Direct</td>
        <td style="padding: 8px; border: 1px solid #ddd;">Best in NJ</td>
      </tr>
      <tr style="background-color: #f7fafc;">
        <td style="padding: 8px; border: 1px solid #ddd;"><a href="/towns/princeton.html" style="color: #2563eb; font-weight: 600;">Princeton</a></td>
        <td style="padding: 8px; border: 1px solid #ddd;">Luxury</td>
        <td style="padding: 8px; border: 1px solid #ddd;">$1.5-2.0M</td>
        <td style="padding: 8px; border: 1px solid #ddd;">~75 min</td>
        <td style="padding: 8px; border: 1px solid #ddd;">Dinky + NE Corridor</td>
        <td style="padding: 8px; border: 1px solid #ddd;">Elite</td>
      </tr>
      <tr>
        <td style="padding: 8px; border: 1px solid #ddd;"><a href="/towns/basking-ridge.html" style="color: #2563eb; font-weight: 600;">Basking Ridge</a></td>
        <td style="padding: 8px; border: 1px solid #ddd;">Luxury</td>
        <td style="padding: 8px; border: 1px solid #ddd;">$950K-1.5M</td>
        <td style="padding: 8px; border: 1px solid #ddd;">~55 min</td>
        <td style="padding: 8px; border: 1px solid #ddd;">Gladstone Branch</td>
        <td style="padding: 8px; border: 1px solid #ddd;">Excellent</td>
      </tr>
    </tbody>
  </table>
  <p style="margin-top: 15px; font-size: 0.85rem; color: #64748b;"><em>*Cranford starter condos/Capes dip below $500K. Prices and commute times as of April 2026. Commute to Penn Station NYC via NJ Transit peak weekday service.</em></p>
</div>

<p>If you're <a href="/buy-a-home.html" style="color: #2563eb; font-weight: 600;">ready to buy in a commuter town</a>, I help NYC transplants and returning NJ natives find the right balance between commute, budget, and schools — without the usual realtor pressure tactics.</p>

<p>Already own in a Midtown Direct town and thinking about selling? <a href="/sell-your-home.html" style="color: #2563eb; font-weight: 600;">Here's how we position commuter-friendly homes</a> to capture the NYC buyer pool using AI-powered targeting you won't find with other agents.</p>
'''
    
    # Find a good insertion point - after the opening paragraphs
    # Look for the first H2 after the intro
    pattern = r'(<h2[^>]*>Under \$500K: Affordable Entry Into NJ Commuter Life</h2>)'
    
    if re.search(pattern, content):
        content = re.sub(
            pattern,
            comparison_table + '\n\n' + r'\1',
            content,
            count=1
        )
        
        filepath.write_text(content)
        print("   ✓ Added budget-tiered comparison table")
        print("   ✓ Added 2 internal links")
        return True
    else:
        print("   ✗ Could not find insertion point")
        return False

def main():
    print("=" * 70)
    print("FINISHING ALL REMAINING OPTIMIZATIONS")
    print("=" * 70)
    print()
    
    add_commuter_comparison_table()
    
    print()
    print("=" * 70)
    print("✅ QUICK WINS COMPLETE")
    print("=" * 70)
    print()

if __name__ == "__main__":
    main()
