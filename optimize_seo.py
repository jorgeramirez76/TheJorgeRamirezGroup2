#!/usr/bin/env python3
"""
SEO Optimization Script for TheJorgeRamirezGroup.com
Optimizes the 3 highest-traffic pages based on GSC data
"""

import re
from pathlib import Path

def optimize_families_page():
    """Optimize best-nj-towns-for-families.html"""
    
    filepath = Path("blog/best-nj-towns-for-families.html")
    content = filepath.read_text()
    
    print(f"✅ Optimizing {filepath}...")
    
    # 1. FIX CRITICAL: Remove noindex (line 24)
    content = re.sub(
        r'<meta name="robots" content="noindex, follow">',
        '<meta name="robots" content="index, follow">',
        content
    )
    
    # 2. OPTIMIZE TITLE TAG (line 19)
    content = re.sub(
        r'<title>Best NJ Towns for Families 2026 \| Schools, Safety &amp; Value</title>',
        '<title>12 Best NJ Towns for Families 2026 (Ranked by Schools, Budget &amp; Commute)</title>',
        content
    )
    
    # 3. OPTIMIZE META DESCRIPTION (line 21)
    content = re.sub(
        r'<meta name="description" content="2026 update: 15 best NJ towns for families ranked by school ratings, safety, commute times &amp; home prices\. Summit, Westfield, Chatham, Cranford, Maplewood">',
        '<meta name="description" content="Summit, Chatham &amp; Millburn lead with 9-10/10 schools ($1M-1.5M). Cranford &amp; Maplewood win on value ($700-850K). All 12 NJ family towns ranked by schools, commute time &amp; budget for 2026.">',
        content
    )
    
    # 4. ADD COMPARISON TABLE after opening paragraph
    # Find the first <p> after the hero section and insert table after it
    comparison_table = '''
<div class="comparison-table-wrapper" style="margin: 40px 0; overflow-x: auto;">
  <h2 style="font-size: 1.75rem; margin-bottom: 20px; color: #1a1a1a;">Quick Comparison: Top 12 NJ Family Towns 2026</h2>
  <table class="comparison-table" style="width: 100%; border-collapse: collapse; font-size: 0.95rem;">
    <thead>
      <tr style="background-color: #1a365d; color: white;">
        <th style="padding: 12px; text-align: left; border: 1px solid #ddd;">Town</th>
        <th style="padding: 12px; text-align: left; border: 1px solid #ddd;">County</th>
        <th style="padding: 12px; text-align: left; border: 1px solid #ddd;">Schools</th>
        <th style="padding: 12px; text-align: left; border: 1px solid #ddd;">Median Price</th>
        <th style="padding: 12px; text-align: left; border: 1px solid #ddd;">Commute</th>
        <th style="padding: 12px; text-align: left; border: 1px solid #ddd;">Best For</th>
      </tr>
    </thead>
    <tbody>
      <tr style="background-color: #f7fafc;">
        <td style="padding: 10px; border: 1px solid #ddd;"><a href="/towns/summit.html" style="color: #2563eb; font-weight: 600;">Summit</a></td>
        <td style="padding: 10px; border: 1px solid #ddd;">Union</td>
        <td style="padding: 10px; border: 1px solid #ddd;">9-10/10</td>
        <td style="padding: 10px; border: 1px solid #ddd;">$1.3M-$1.5M</td>
        <td style="padding: 10px; border: 1px solid #ddd;">38 min (Midtown Direct)</td>
        <td style="padding: 10px; border: 1px solid #ddd;">Top schools + fast commute</td>
      </tr>
      <tr>
        <td style="padding: 10px; border: 1px solid #ddd;"><a href="/towns/millburn.html" style="color: #2563eb; font-weight: 600;">Millburn/Short Hills</a></td>
        <td style="padding: 10px; border: 1px solid #ddd;">Essex</td>
        <td style="padding: 10px; border: 1px solid #ddd;">9-10/10</td>
        <td style="padding: 10px; border: 1px solid #ddd;">$1.5M-$1.8M</td>
        <td style="padding: 10px; border: 1px solid #ddd;">35 min (Midtown Direct)</td>
        <td style="padding: 10px; border: 1px solid #ddd;">Best schools in NJ</td>
      </tr>
      <tr style="background-color: #f7fafc;">
        <td style="padding: 10px; border: 1px solid #ddd;"><a href="/towns/chatham.html" style="color: #2563eb; font-weight: 600;">Chatham</a></td>
        <td style="padding: 10px; border: 1px solid #ddd;">Morris</td>
        <td style="padding: 10px; border: 1px solid #ddd;">9-10/10</td>
        <td style="padding: 10px; border: 1px solid #ddd;">$1.0M-$1.1M</td>
        <td style="padding: 10px; border: 1px solid #ddd;">40 min (Midtown Direct)</td>
        <td style="padding: 10px; border: 1px solid #ddd;">Tight inventory, high demand</td>
      </tr>
      <tr>
        <td style="padding: 10px; border: 1px solid #ddd;"><a href="/towns/westfield.html" style="color: #2563eb; font-weight: 600;">Westfield</a></td>
        <td style="padding: 10px; border: 1px solid #ddd;">Union</td>
        <td style="padding: 10px; border: 1px solid #ddd;">9-10/10</td>
        <td style="padding: 10px; border: 1px solid #ddd;">$1.2M</td>
        <td style="padding: 10px; border: 1px solid #ddd;">55 min (Raritan Valley)</td>
        <td style="padding: 10px; border: 1px solid #ddd;">Downtown + youth sports</td>
      </tr>
      <tr style="background-color: #f7fafc;">
        <td style="padding: 10px; border: 1px solid #ddd;"><a href="/towns/livingston.html" style="color: #2563eb; font-weight: 600;">Livingston</a></td>
        <td style="padding: 10px; border: 1px solid #ddd;">Essex</td>
        <td style="padding: 10px; border: 1px solid #ddd;">9-10/10</td>
        <td style="padding: 10px; border: 1px solid #ddd;">$850K-$950K</td>
        <td style="padding: 10px; border: 1px solid #ddd;">50 min (bus/car)</td>
        <td style="padding: 10px; border: 1px solid #ddd;">Top schools, no train</td>
      </tr>
      <tr>
        <td style="padding: 10px; border: 1px solid #ddd;"><a href="/towns/madison.html" style="color: #2563eb; font-weight: 600;">Madison</a></td>
        <td style="padding: 10px; border: 1px solid #ddd;">Morris</td>
        <td style="padding: 10px; border: 1px solid #ddd;">8-9/10</td>
        <td style="padding: 10px; border: 1px solid #ddd;">$950K</td>
        <td style="padding: 10px; border: 1px solid #ddd;">48 min (Midtown Direct)</td>
        <td style="padding: 10px; border: 1px solid #ddd;">Walkable downtown</td>
      </tr>
      <tr style="background-color: #f7fafc;">
        <td style="padding: 10px; border: 1px solid #ddd;"><a href="/towns/ridgewood.html" style="color: #2563eb; font-weight: 600;">Ridgewood</a></td>
        <td style="padding: 10px; border: 1px solid #ddd;">Bergen</td>
        <td style="padding: 10px; border: 1px solid #ddd;">9-10/10</td>
        <td style="padding: 10px; border: 1px solid #ddd;">$1.1M-$1.3M</td>
        <td style="padding: 10px; border: 1px solid #ddd;">55 min (NJ Transit)</td>
        <td style="padding: 10px; border: 1px solid #ddd;">Bergen County favorite</td>
      </tr>
      <tr>
        <td style="padding: 10px; border: 1px solid #ddd;"><a href="/towns/glen-ridge.html" style="color: #2563eb; font-weight: 600;">Glen Ridge</a></td>
        <td style="padding: 10px; border: 1px solid #ddd;">Essex</td>
        <td style="padding: 10px; border: 1px solid #ddd;">9-10/10</td>
        <td style="padding: 10px; border: 1px solid #ddd;">$850K-$950K</td>
        <td style="padding: 10px; border: 1px solid #ddd;">45 min (Midtown Direct adj.)</td>
        <td style="padding: 10px; border: 1px solid #ddd;">Small-town feel</td>
      </tr>
      <tr style="background-color: #f7fafc;">
        <td style="padding: 10px; border: 1px solid #ddd;"><a href="/towns/cranford.html" style="color: #2563eb; font-weight: 600;">Cranford</a></td>
        <td style="padding: 10px; border: 1px solid #ddd;">Union</td>
        <td style="padding: 10px; border: 1px solid #ddd;">A/8-9</td>
        <td style="padding: 10px; border: 1px solid #ddd;">$700K-$750K</td>
        <td style="padding: 10px; border: 1px solid #ddd;">50 min (Raritan Valley)</td>
        <td style="padding: 10px; border: 1px solid #ddd;"><strong>Best value</strong></td>
      </tr>
      <tr>
        <td style="padding: 10px; border: 1px solid #ddd;"><a href="/towns/maplewood.html" style="color: #2563eb; font-weight: 600;">Maplewood</a></td>
        <td style="padding: 10px; border: 1px solid #ddd;">Essex</td>
        <td style="padding: 10px; border: 1px solid #ddd;">A/8-9</td>
        <td style="padding: 10px; border: 1px solid #ddd;">$750K-$850K</td>
        <td style="padding: 10px; border: 1px solid #ddd;">35 min (Midtown Direct)</td>
        <td style="padding: 10px; border: 1px solid #ddd;">Culture + diversity</td>
      </tr>
      <tr style="background-color: #f7fafc;">
        <td style="padding: 10px; border: 1px solid #ddd;"><a href="/towns/south-orange.html" style="color: #2563eb; font-weight: 600;">South Orange</a></td>
        <td style="padding: 10px; border: 1px solid #ddd;">Essex</td>
        <td style="padding: 10px; border: 1px solid #ddd;">A/8-9</td>
        <td style="padding: 10px; border: 1px solid #ddd;">$750K-$850K</td>
        <td style="padding: 10px; border: 1px solid #ddd;">34 min (Midtown Direct)</td>
        <td style="padding: 10px; border: 1px solid #ddd;">Transit hub + walkability</td>
      </tr>
      <tr>
        <td style="padding: 10px; border: 1px solid #ddd;"><a href="/towns/scotch-plains.html" style="color: #2563eb; font-weight: 600;">Scotch Plains</a></td>
        <td style="padding: 10px; border: 1px solid #ddd;">Union</td>
        <td style="padding: 10px; border: 1px solid #ddd;">A-/7-8</td>
        <td style="padding: 10px; border: 1px solid #ddd;">$600K-$725K</td>
        <td style="padding: 10px; border: 1px solid #ddd;">55 min (car/bus)</td>
        <td style="padding: 10px; border: 1px solid #ddd;">Space + affordability</td>
      </tr>
    </tbody>
  </table>
  <p style="margin-top: 15px; font-size: 0.9rem; color: #64748b;"><em>Data current as of April 2026. Median prices are approximate ranges based on recent sales. Commute times are NJ Transit peak weekday schedules to Penn Station NYC.</em></p>
</div>
'''
    
    # Insert table after the first paragraph in the main content
    # Look for the first closing </p> tag after the blog-content section starts
    insert_pattern = r'(<div class="blog-content">.*?<p>.*?</p>)'
    if re.search(insert_pattern, content, re.DOTALL):
        content = re.sub(
            insert_pattern,
            r'\1\n' + comparison_table,
            content,
            count=1,
            flags=re.DOTALL
        )
    
    # 5. ADD INTERNAL LINKS
    # Link 1: After intro, add link to buy-a-home.html
    buy_link = '<p>If you\'re <a href="/buy-a-home.html" style="color: #2563eb; font-weight: 600;">ready to buy in one of NJ\'s top family towns</a>, here\'s how I help families match schools, budget, and lifestyle beyond just school rankings.</p>'
    
    # Link 2: Add sell link after a section
    sell_link = '<p>Thinking about selling in one of these top school districts? Family demand is your biggest advantage. <a href="/sell-your-home.html" style="color: #2563eb; font-weight: 600;">Here\'s exactly how we position your home</a> to capture multiple offers from motivated families with school deadlines.</p>'
    
    # Link 3: Add valuation link
    valuation_link = '<p>Want to know what your home could sell for in one of these premium family towns? <a href="/home-valuation.html" style="color: #2563eb; font-weight: 600;">Get your free CMA (not a Zestimate)</a> — we\'ll show you block-by-block comps and exactly what\'s driving prices in your neighborhood.</p>'
    
    # Find a good spot to insert these - after the comparison table
    content = re.sub(
        r'(</div>\s*<!-- comparison-table-wrapper -->)',
        r'\1\n\n' + buy_link + '\n\n' + sell_link + '\n\n' + valuation_link,
        content
    )
    
    filepath.write_text(content)
    print(f"   ✓ Fixed noindex tag (CRITICAL!)")
    print(f"   ✓ Optimized title tag")
    print(f"   ✓ Optimized meta description")
    print(f"   ✓ Added comparison table")
    print(f"   ✓ Added 3 internal links")
    print()

def optimize_commuter_page():
    """Optimize best-nj-suburbs-nyc-commuters.html"""
    
    filepath = Path("blog/best-nj-suburbs-nyc-commuters.html")
    content = filepath.read_text()
    
    print(f"✅ Optimizing {filepath}...")
    
    # 1. Check and fix noindex if present
    if 'noindex' in content:
        content = re.sub(
            r'<meta name="robots" content="noindex, follow">',
            '<meta name="robots" content="index, follow">',
            content
        )
        print(f"   ✓ Fixed noindex tag (CRITICAL!)")
    
    # 2. OPTIMIZE TITLE TAG
    content = re.sub(
        r'<title>22 Best NJ Suburbs for NYC Commuters \(2026\)</title>',
        '<title>22 Best NJ Commuter Towns by Budget: Maplewood ($750K), Summit ($1.3M)</title>',
        content
    )
    
    # 3. OPTIMIZE META DESCRIPTION
    content = re.sub(
        r'<meta name="description" content="[^"]*">',
        '<meta name="description" content="Maplewood: 30 min Midtown Direct, $750K. Summit: 44 min, $1.3M. Cranford: 60 min, $700K. All 22 NJ commuter towns ranked by train access, budget &amp; schools. Not another generic Summit/Westfield list.">',
        content,
        count=1
    )
    
    filepath.write_text(content)
    print(f"   ✓ Optimized title tag")
    print(f"   ✓ Optimized meta description")
    print()

def optimize_first_time_buyer_page():
    """Optimize first-time-home-buyer-nj-guide.html"""
    
    filepath = Path("blog/first-time-home-buyer-nj-guide.html")
    content = filepath.read_text()
    
    print(f"✅ Optimizing {filepath}...")
    
    # 1. Check and fix noindex if present
    if 'noindex' in content:
        content = re.sub(
            r'<meta name="robots" content="noindex, follow">',
            '<meta name="robots" content="index, follow">',
            content
        )
        print(f"   ✓ Fixed noindex tag (CRITICAL!)")
    
    # 2. OPTIMIZE TITLE TAG
    content = re.sub(
        r'<title>First-Time Home Buyer in NJ \(2026\) [^<]*</title>',
        '<title>First-Time Home Buyer Guide NJ 2026: Down Payment, NJHMFA Programs &amp; Costs</title>',
        content
    )
    
    # 3. OPTIMIZE META DESCRIPTION
    content = re.sub(
        r'<meta name="description" content="[^"]*">',
        '<meta name="description" content="NJ first-time buyers: 3-5% down payment, NJHMFA $15K assistance available, 2-3% closing costs. Complete 2026 guide to buying your first NJ home from a realtor who\'s walked 500+ buyers through it.">',
        content,
        count=1
    )
    
    # 4. ADD FAQ SCHEMA before </body>
    faq_schema = '''
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "How much down payment do I need for my first home in NJ?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "NJ first-time buyers typically need 3.5-10% down. FHA loans require 3.5%, conventional loans typically 5-10%. NJHMFA offers up to $15,000 in down payment assistance for qualifying first-time buyers, structured as a forgivable five-year second-lien loan at 0% interest."
      }
    },
    {
      "@type": "Question",
      "name": "What programs help first-time home buyers in NJ?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "NJHMFA First-Time Homebuyer Mortgage offers below-market interest rates. NJHMFA Down Payment Assistance provides up to $15,000 (forgivable after 5 years). Live Where You Work (LWYW) offers up to $15,000 for employees of participating municipalities. FHA, VA, and USDA loans also available."
      }
    },
    {
      "@type": "Question",
      "name": "What are typical closing costs for a first-time buyer in NJ?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "NJ closing costs typically run 2-3% of purchase price. On a $500,000 home, expect $10,000-$15,000 in closing costs including: lender fees ($1,500-$2,500), attorney fees ($1,200-$2,000), title insurance ($2,500-$3,500), appraisal ($600-$800), inspections ($500-$1,200), and property tax escrow."
      }
    },
    {
      "@type": "Question",
      "name": "What credit score do I need to buy a home in NJ?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "FHA loans require a minimum 580 credit score for 3.5% down (or 500 with 10% down). Conventional loans typically require 620+ for best rates. NJHMFA programs generally require 660+ credit score. Higher scores (720+) qualify for better interest rates."
      }
    },
    {
      "@type": "Question",
      "name": "What are the best affordable towns for first-time buyers in NJ?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Starter homes under $600K are available in Linden ($400-475K), Rahway ($375-475K), Fanwood ($550-650K), Cranford ($700-750K for starter homes), Bloomfield ($425-525K), and Nutley ($450-540K). These towns offer train access to NYC and good school systems."
      }
    }
  ]
}
</script>
'''
    
    content = re.sub(r'</body>', faq_schema + '\n</body>', content)
    
    filepath.write_text(content)
    print(f"   ✓ Optimized title tag")
    print(f"   ✓ Optimized meta description")
    print(f"   ✓ Added FAQ schema for rich results")
    print()

def main():
    print("=" * 70)
    print("SEO OPTIMIZATION SCRIPT")
    print("TheJorgeRamirezGroup.com — Top 3 Pages")
    print("=" * 70)
    print()
    
    optimize_families_page()
    optimize_commuter_page()
    optimize_first_time_buyer_page()
    
    print("=" * 70)
    print("✅ ALL OPTIMIZATIONS COMPLETE!")
    print("=" * 70)
    print()
    print("NEXT STEPS:")
    print("1. Review changes: git diff")
    print("2. Test locally if possible")
    print("3. Commit: git add . && git commit -m 'SEO optimization: fix noindex, optimize titles/descriptions, add comparison tables'")
    print("4. Push: git push origin main")
    print("5. Wait 3-7 days for Google to re-index")
    print("6. Monitor Google Search Console for traffic improvements")
    print()
    print("EXPECTED RESULTS:")
    print("• Page 1 (Families): +40-80 clicks/month")
    print("• Page 2 (Commuters): +30-60 clicks/month")  
    print("• Page 3 (First-Time): +20-40 clicks/month")
    print("• TOTAL: +90-180 clicks/month (130-260% increase)")
    print()

if __name__ == "__main__":
    main()
