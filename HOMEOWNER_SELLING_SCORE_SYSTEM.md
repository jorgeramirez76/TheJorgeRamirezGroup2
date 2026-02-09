# Homeowner Selling Likelihood Scoring System
## New Jersey Real Estate Prospecting Model
### Target Counties: Union, Hudson, Middlesex, Morris, Essex

---

## Executive Summary

This scoring system predicts homeowner selling likelihood using 18 weighted factors across 5 categories. Properties scoring **70+ points** are considered "hot prospects" with elevated selling probability within 6-12 months.

**Scoring Scale:** 0-100 points  
**Hot Prospect Threshold:** 70+ points  
**Warm Prospect:** 50-69 points  
**Cold Prospect:** <50 points

---

## Category 1: Life Events (Max 35 Points)

### Factor 1: Divorce/Domestic Separation
| Attribute | Value |
|-----------|-------|
| **Weight** | 10/10 |
| **Max Points** | 10 |

**Data Points to Track:**
- Divorce filings in NJ Superior Court (Family Division)
- Legal separation notices
- Property ownership transfers related to divorce
- Spousal name removals from deeds

**Scoring Methodology:**
| Indicator | Points |
|-----------|--------|
| Divorce filed within 6 months | +10 |
| Divorce filed 6-12 months ago | +7 |
| Legal separation recorded | +5 |
| Spouse removed from deed (last 12mo) | +8 |

**Data Sources:**
- NJ Superior Court records (family division)
- County Clerk deed transfers
- PublicRecords.com / NETR Online
- NJ Judiciary Case Search

---

### Factor 2: Death of Property Owner
| Attribute | Value |
|-----------|-------|
| **Weight** | 9/10 |
| **Max Points** | 9 |

**Data Points to Track:**
- Death certificates indexed by county
- Probate court filings
- Estate transfers/deed changes
- Executor appointments
- Joint tenancy severance

**Scoring Methodology:**
| Indicator | Points |
|-----------|--------|
| Owner death within 90 days | +9 |
| Owner death 3-6 months ago | +7 |
| Probate case opened (last 6mo) | +6 |
| Joint tenant death (surviving spouse) | +5 |
| Estate executor appointed (last 90 days) | +8 |

**Data Sources:**
- NJ State Vital Statistics
- Surrogate Court probate records
- County Clerk estate deed transfers
- Obituary databases (Legacy.com, local papers)

---

### Factor 3: Marriage/New Partnership
| Attribute | Value |
|-----------|-------|
| **Weight** | 6/10 |
| **Max Points** | 6 |

**Data Points to Track:**
- Marriage licenses (county records)
- Deed additions (adding spouse)
- Co-habitation indicators
- Engagement announcements

**Scoring Methodology:**
| Indicator | Points |
|-----------|--------|
| Marriage + deed change (last 6mo) | +6 |
| Marriage recorded (last 3mo) | +4 |
| Adding partner to deed | +5 |

**Data Sources:**
- County marriage license records
- Deed transfer records
- Social media monitoring
- Local newspaper announcements

---

### Factor 4: New Child/Birth
| Attribute | Value |
|-----------|-------|
| **Weight** | 5/10 |
| **Max Points** | 5 |

**Data Points to Track:**
- Birth records (indirect indicators)
- Home size relative to family size
- School district changes
- Maternity/paternity announcements

**Scoring Methodology:**
| Indicator | Points |
|-----------|--------|
| Birth + current home <3BR | +5 |
| Birth announcement + outgrown space | +4 |
| Second child + <3BR home | +5 |
| Nursery addition permit | +3 |

**Data Sources:**
- Birth announcements (social/newspapers)
- Property characteristics (bedrooms)
- Building permits for nursery additions
- School registration trends

---

### Factor 5: Empty Nest (Children Leaving Home)
| Attribute | Value |
|-----------|-------|
| **Weight** | 6/10 |
| **Max Points** | 6 |

**Data Points to Track:**
- Household composition changes
- Age of owners (55-70 prime empty nest)
- Downsizing indicators
- College graduation years

**Scoring Methodology:**
| Indicator | Points |
|-----------|--------|
| Both children left (last 12mo) + age 55+ | +6 |
| Last child graduated college + 4BR home | +5 |
| Age 60+ with 4+ BR home | +4 |
| Recent college grad moved out | +3 |

**Data Sources:**
- Census demographic data
- Age estimation from voter records
- Property size vs. household size modeling
- School district departure patterns

---

### Factor 6: Job Change/Relocation
| Attribute | Value |
|-----------|-------|
| **Weight** | 8/10 |
| **Max Points** | 8 |

**Data Points to Track:**
- Employment location changes
- LinkedIn job updates
- New employer registrations
- Commute distance changes
- Corporate relocations

**Scoring Methodology:**
| Indicator | Points |
|-----------|--------|
| New job >50 miles away (last 90 days) | +8 |
| Remote work ending + long commute | +6 |
| Corporate transfer announced | +7 |
| New job 30-50 miles away | +5 |
| LinkedIn shows "Open to Work" + new location | +4 |

**Data Sources:**
- LinkedIn profile monitoring
- Corporate relocation announcements
- Professional license transfers
- NJ DOL employment data
- Social media location changes

---

### Factor 7: Retirement
| Attribute | Value |
|-----------|-------|
| **Weight** | 7/10 |
| **Max Points** | 7 |

**Data Points to Track:**
- Age 62+ (retirement age)
- Social Security claim records
- Pension income commencement
- Lifestyle location changes
- 55+ community interest

**Scoring Methodology:**
| Indicator | Points |
|-----------|--------|
| Age 65+ + large home (>3BR) | +7 |
| Retirement announcement + 2-story home | +6 |
| Age 62-64 + 15+ years in home | +5 |
| Pension income starts (public records) | +4 |
| Retired + home needs stairs navigation | +5 |

**Data Sources:**
- Voter registration age data
- Pension records (public employees)
- Property characteristics
- Medicare enrollment data (indirect)
- Social media retirement posts

---

## Category 2: Financial Stress (Max 30 Points)

### Factor 8: Property Tax Delinquency
| Attribute | Value |
|-----------|-------|
| **Weight** | 9/10 |
| **Max Points** | 9 |

**Data Points to Track:**
- NJ property tax payment status
- Tax lien records
- Municipal tax sale certificates
- Delinquency duration

**Scoring Methodology:**
| Indicator | Points |
|-----------|--------|
| Tax lien filed (last 6mo) | +9 |
| 6+ months delinquent | +7 |
| 3-6 months delinquent | +5 |
| Tax payment plan established | +4 |
| Previous year delinquency (resolved) | +2 |

**Data Sources:**
- County Tax Collector records
- NJ State tax lien database
- Municipal tax sale records
- PropertyShark / Regrid
- Local tax assessor offices

---

### Factor 9: Foreclosure Filings (Lis Pendens)
| Attribute | Value |
|-----------|-------|
| **Weight** | 10/10 |
| **Max Points** | 10 |

**Data Points to Track:**
- Lis Pendens filings
- Notice of Default records
- Sheriff sale schedules
- Loan modification attempts
- Bankruptcy filings related to home

**Scoring Methodology:**
| Indicator | Points |
|-----------|--------|
| Lis Pendens filed (last 90 days) | +10 |
| Notice of Default served | +9 |
| Scheduled for sheriff sale | +10 |
| Loan modification denied | +6 |
| Foreclosure dismissed + recent refinance | +4 |

**Data Sources:**
- County Clerk lis pendens records
- NJ Courts foreclosure filings
- RealtyTrac / Foreclosure.com
- Public Records Pro
- Sheriff's office sale lists

---

### Factor 10: Bankruptcy Filings
| Attribute | Value |
|-----------|-------|
| **Weight** | 8/10 |
| **Max Points** | 8 |

**Data Points to Track:**
- Federal bankruptcy court filings
- Chapter 7 vs Chapter 13
- Asset protection involving home
- Homestead exemption claims
- Discharge dates

**Scoring Methodology:**
| Indicator | Points |
|-----------|--------|
| Chapter 7 filed + home not exempt | +8 |
| Chapter 13 filed (last 6mo) | +6 |
| Bankruptcy + high equity in home | +7 |
| Discharged (last 12mo) + need to sell | +5 |
| Multiple filings (pattern) | +6 |

**Data Sources:**
- PACER (federal court records)
- NJ Bankruptcy Court records
- Legal newspaper notices
- Credit bureau indicators (indirect)

---

### Factor 11: Equity Position & Mortgage Changes
| Attribute | Value |
|-----------|-------|
| **Weight** | 7/10 |
| **Max Points** | 7 |

**Data Points to Track:**
- Loan-to-value ratio (LTV)
- Mortgage origination date
- HELOC activity
- Cash-out refinances
- Multiple mortgages
- Negative equity indicators

**Scoring Methodology:**
| Indicator | Points |
|-----------|--------|
| <10% equity (underwater risk) | +7 |
| ARM reset imminent (within 12mo) | +6 |
| HELOC maxed out + rate increases | +5 |
| Recent cash-out refinance (debt consolidation) | +4 |
| 95%+ LTV with payment stress | +6 |
| Paid-off mortgage + age 65+ | +3 |

**Data Sources:**
- County mortgage/deed records
- Credit data (opt-in)
- Property value estimates
- Mortgage origination dates from records
- CoreLogic / Black Knight (if available)

---

## Category 3: Property Indicators (Max 20 Points)

### Factor 12: Years Owned / Ownership Duration
| Attribute | Value |
|-----------|-------|
| **Weight** | 6/10 |
| **Max Points** | 6 |

**Data Points to Track:**
- Purchase date from deed records
- Previous sale price
- Average ownership for area
- Equity accumulation

**Scoring Methodology:**
| Indicator | Points |
|-----------|--------|
| Owned 20+ years (prime selling window) | +6 |
| Owned 15-20 years | +5 |
| Owned 10-15 years + market peak | +4 |
| Owned 5-10 years + growing family | +3 |
| Owned <3 years (flip/job change risk) | +2 |

**Data Sources:**
- County deed records
- Property transaction history
- NJ MOD-IV system
- CoreLogic property records

---

### Factor 13: Expired/Withdrawn Listings
| Attribute | Value |
|-----------|-------|
| **Weight** | 8/10 |
| **Max Points** | 8 |

**Data Points to Track:**
- MLS expired listings
- Withdrawn listings
- Failed sales attempts
- Days on market before expiry
- Price reduction history

**Scoring Methodology:**
| Indicator | Points |
|-----------|--------|
| Expired listing (last 30 days) | +8 |
| Expired listing (31-90 days) | +6 |
| Withdrawn + no re-list (last 60 days) | +5 |
| 2+ expired listings (last 2 years) | +7 |
| Expired at high price + market shifted | +5 |

**Data Sources:**
- Garden State MLS (GSMLS)
- Hudson County MLS
- Monmouth/Ocean MLS (for relevant areas)
- Zillow/Redfin listing history
- Realtor.com property history

---

### Factor 14: FSBO Attempts (For Sale By Owner)
| Attribute | Value |
|-----------|-------|
| **Weight** | 7/10 |
| **Max Points** | 7 |

**Data Points to Track:**
- FSBO listings (Zillow, Craigslist, Facebook)
- "For Sale By Owner" signs
- Flat-fee MLS listings
- FSBO duration
- Price changes during FSBO

**Scoring Methodology:**
| Indicator | Points |
|-----------|--------|
| Active FSBO (current) | +7 |
| FSBO failed (last 60 days) | +6 |
| FSBO >60 days no sale | +5 |
| FSBO then expired + no relist | +5 |
| Multiple FSBO attempts | +6 |

**Data Sources:**
- Zillow FSBO section
- Craigslist housing listings
- Facebook Marketplace
- FSBO.com
- ForSaleByOwner.com
- Driving for dollars (physical signs)

---

### Factor 15: Building Permits/Renovation Activity
| Attribute | Value |
|-----------|-------|
| **Weight** | 5/10 |
| **Max Points** | 5 |

**Data Points to Track:**
- Building permits filed
- Renovation types (kitchen, bath, addition)
- Permit dates
- Contractor liens
- Pre-sale renovations

**Scoring Methodology:**
| Indicator | Points |
|-----------|--------|
| Pre-sale reno pattern (cosmetic) | +5 |
| Kitchen/bath reno completed (last 6mo) | +4 |
| Exterior paint + landscaping permits | +3 |
| Major addition (growing, not selling) | -2 |
| Repair permits (roof, HVAC) + aging owner | +3 |
| Permit + listing preparation indicators | +4 |

**Data Sources:**
- Municipal building departments
- County permit databases
- Contractor license lookups
- Lien records
- DataTree / BuildFax

---

## Category 4: Market Conditions (Max 10 Points)

### Factor 16: Interest Rate Sensitivity
| Attribute | Value |
|-----------|-------|
| **Weight** | 5/10 |
| **Max Points** | 5 |

**Data Points to Track:**
- Current mortgage rate vs. market rate
- Rate lock expirations
- Refinance activity
- Adjustable-rate mortgage resets
- Fed rate changes

**Scoring Methodology:**
| Indicator | Points |
|-----------|--------|
| Current rate <4% + moving to 7%+ (lock loss) | +5 |
| ARM reset +2% or more (next 12mo) | +4 |
| Rate sensitive + recent job change | +3 |
| Purchased at 3% + life event occurs | +4 |

**Data Sources:**
- Mortgage origination records
- Freddie Mac PMMS rates
- Fed policy announcements
- Refinance application data
- Mortgage banker reports

---

### Factor 17: Local Market Appreciation/Velocity
| Attribute | Value |
|-----------|-------|
| **Weight** | 5/10 |
| **Max Points** | 5 |

**Data Points to Track:**
- YoY price appreciation by ZIP
- Days on market trends
- Inventory levels
- Price per sqft changes
- Sales volume

**Scoring Methodology:**
| Indicator | Points |
|-----------|--------|
| 15%+ appreciation (peak selling) | +5 |
| Inventory <2 months (seller's market) | +4 |
| DOM declining rapidly | +3 |
| Recent comp sales at record highs | +4 |
| Price per sqft +10% YoY | +3 |

**Data Sources:**
- Zillow Home Value Index
- Redfin Data Center
- CoreLogic HPI
- GSMLS market reports
- NJ Realtors monthly reports
- Federal Housing Finance Agency

---

## Category 5: Demographics (Max 10 Points)

### Factor 18: Age & Household Composition
| Attribute | Value |
|-----------|-------|
| **Weight** | 6/10 |
| **Max Points** | 6 |

**Data Points to Track:**
- Head of household age
- Household size
- Generational cohort
- Life stage indicators
- Multi-generational living changes

**Scoring Methodology:**
| Indicator | Points |
|-----------|--------|
| Age 65+ + large home (>2,500 sqft) | +6 |
| Age 30-35 + starter home + child on way | +4 |
| Single owner + 3BR home | +3 |
| Multi-gen household splitting | +5 |
| Age 55-60 + home equity peak | +4 |

**Data Sources:**
- Voter registration records
- Census demographic estimates
- Consumer databases (Acxiom, Experian)
- Public records age inference
- Marketing data providers

---

### Factor 19: Income Changes
| Attribute | Value |
|-----------|-------|
| **Weight** | 4/10 |
| **Max Points** | 4 |

**Data Points to Track:**
- Income growth/decline indicators
- Job loss patterns
- Industry changes
- Employer growth/decline
- Lifestyle inflation signals

**Scoring Methodology:**
| Indicator | Points |
|-----------|--------|
| Significant income increase + upgrade potential | +3 |
| Income decrease + home affordability stress | +4 |
| Industry decline + local layoffs | +3 |
| Recent promotion + LinkedIn update | +2 |
| Two-income to one-income household | +4 |

**Data Sources:**
- LinkedIn job changes
- Industry employment data
- Consumer marketing data
- Professional license status
- Credit capacity indicators (indirect)

---

## Scoring Algorithm

### Total Possible: 100 Points

| Category | Max Points | Weight % |
|----------|-----------|----------|
| Life Events | 35 | 35% |
| Financial Stress | 30 | 30% |
| Property Indicators | 20 | 20% |
| Market Conditions | 10 | 10% |
| Demographics | 10 | 10% |

### Composite Score Formula

```
Selling Likelihood Score = 
  (Life Events Score) +
  (Financial Stress Score) +
  (Property Indicators Score) +
  (Market Conditions Score) +
  (Demographics Score)
```

### Prospect Classification

| Score Range | Classification | Action Priority |
|-------------|---------------|-----------------|
| 85-100 | **Critical** | Contact within 24-48 hours |
| 70-84 | **Hot** | Contact within 1 week |
| 50-69 | **Warm** | Add to nurture campaign |
| 30-49 | **Cool** | Long-term follow-up |
| 0-29 | **Cold** | Market monitoring only |

---

## County-Specific Data Sources

### Union County
- **Tax Records:** union.nj.us (Tax Board)
- **Clerk:** Union County Clerk, Elizabeth
- **Courts:** Union County Courthouse
- **MLS:** Garden State MLS

### Hudson County
- **Tax Records:** hudsoncountynj.gov (Tax Board)
- **Clerk:** Hudson County Clerk, Jersey City
- **Courts:** Hudson County Administration Building
- **MLS:** Hudson County MLS + GSMLS

### Middlesex County
- **Tax Records:** co.middlesex.nj.us
- **Clerk:** Middlesex County Clerk, New Brunswick
- **Courts:** Middlesex County Courthouse
- **MLS:** Garden State MLS

### Morris County
- **Tax Records:** co.morris.nj.us
- **Clerk:** Morris County Clerk, Morristown
- **Courts:** Morris County Courthouse
- **MLS:** Garden State MLS

### Essex County
- **Tax Records:** essexcountynj.org
- **Clerk:** Essex County Clerk, Newark
- **Courts:** Essex County Courthouse
- **MLS:** Garden State MLS

---

## Recommended Data Providers

### Tier 1 (Essential)
| Provider | Data Type | Cost Est. |
|----------|-----------|-----------|
| PropertyShark | Tax, ownership, liens | $$$ |
| Regrid | Parcel data, ownership | $$ |
| RealtyTrac | Foreclosure data | $$$ |
| GSMLS | Listing data | $$$$ |

### Tier 2 (Valuable)
| Provider | Data Type | Cost Est. |
|----------|-----------|-----------|
| PropStream | Comprehensive prop data | $$$ |
| BatchLeads | Skip tracing, data | $$ |
| ListSource | Targeted lists | $$ |
| DataTree | Public records | $$$ |

### Tier 3 (Supplementary)
| Provider | Data Type | Cost Est. |
|----------|-----------|-----------|
| PACER | Bankruptcy records | $ (pay per use) |
| NETR Online | Deeds, records | Free-$ |
| Zillow API | Market data | Free tier |
| CoreLogic | Analytics | $$$$ |

---

## Implementation Checklist

### Phase 1: Data Infrastructure (Weeks 1-2)
- [ ] Subscribe to core data providers (PropertyShark, GSMLS)
- [ ] Set up automated data feeds
- [ ] Create database schema for scoring
- [ ] Establish county-specific record access

### Phase 2: Scoring System Build (Weeks 3-4)
- [ ] Program scoring algorithm
- [ ] Build prospect dashboard
- [ ] Set up automated alerts (70+ scores)
- [ ] Create list segmentation

### Phase 3: Outreach Automation (Weeks 5-6)
- [ ] Design mail campaigns by score tier
- [ ] Set up CRM integration
- [ ] Create follow-up sequences
- [ ] Train team on scoring interpretation

### Phase 4: Optimization (Ongoing)
- [ ] Track conversion rates by score
- [ ] Adjust factor weights based on results
- [ ] A/B test outreach messaging
- [ ] Refine data sources

---

## Sample Scored Prospect

**Property:** 123 Main St, Westfield, NJ (Union County)

| Factor | Indicator | Points |
|--------|-----------|--------|
| Divorce | None | 0 |
| Death | None | 0 |
| Job Change | New job in NYC (commute concern) | +5 |
| Retirement | Age 64, considering | +4 |
| Tax Delinquency | None | 0 |
| Foreclosure | None | 0 |
| Bankruptcy | None | 0 |
| Equity Position | 78% LTV, $280k equity | +2 |
| Years Owned | 22 years | +6 |
| Expired Listing | Expired 45 days ago | +6 |
| FSBO Attempt | None | 0 |
| Building Permits | Kitchen reno completed | +4 |
| Interest Rate | 3.25% current (no urgency) | 0 |
| Market Conditions | +12% appreciation | +4 |
| Age/Household | Age 64, empty nest | +5 |
| Income | Stable | 0 |

**TOTAL SCORE: 36** (Warm Prospect - Add to nurture campaign)

---

## Notes & Limitations

### Data Availability
- Some factors require inference from indirect indicators
- Privacy laws limit certain data access (financial, health)
- Data freshness varies by source

### Legal Considerations
- Ensure compliance with FDCPA, TCPA, CAN-SPAM
- Respect Do Not Call registry
- Follow NJ real estate advertising regulations
- Consider privacy when using life event data

### Model Accuracy
- Scoring is probabilistic, not deterministic
- Market conditions significantly impact accuracy
- Regular recalibration recommended (quarterly)
- Track actual conversion rates vs. predicted

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-02-09 | Initial release for 5-county NJ system |

---

*Document maintained by: [Your Name/Organization]*  
*Last Updated: February 9, 2025*
