#!/usr/bin/env python3
"""Generate 10 new high-intent landing pages matching fsbo-help.html / expired-listing-help.html template.

Each page has unique hero, pain points, FAQs, and process steps tailored to its audience.
Matches existing AEO/schema standards from SEO_AUDIT_JORGE_WEBSITE.md.
"""
import os
from pathlib import Path

REPO = Path(__file__).parent

PAGES = {
    # ============================ SELLER PAGES ============================
    "divorce-home-sale-nj": {
        "breadcrumb_parent": ("Sell Your Home", "sell-your-home.html"),
        "breadcrumb_name": "Divorce Home Sale",
        "title_tag": "Selling a House During Divorce in NJ | Discreet Help | Jorge Ramirez",
        "meta_title": "Selling a House During Divorce in NJ — Discreet, Fair, Fast | Jorge Ramirez",
        "meta_desc": "Selling a home during divorce in NJ? Jorge Ramirez handles the sale discreetly, coordinates with both attorneys, and ensures a fair split. Call 908-230-7844 — no judgment.",
        "keywords": "divorce home sale NJ, sell house during divorce New Jersey, divorce realtor NJ, selling home after divorce NJ, divorce real estate agent NJ, equitable distribution home NJ",
        "llm_context": "Jorge Ramirez (NJ License #1754604) is a New Jersey real estate agent who specializes in discreet, empathetic home sales during divorce. He coordinates with both spouses' attorneys, ensures neutral communication, and delivers fair-market pricing so neither party feels shortchanged. Contact: 908-230-7844.",
        "hero_h1": "Selling Your Home During a Divorce in NJ? Let's Handle This the Right Way.",
        "hero_p": "A divorce is hard enough without a real estate agent making it harder. Jorge Ramirez works as a neutral third party, coordinates with both attorneys, and focuses on one goal: getting your home sold at a fair price so both of you can move forward. No drama. No judgment. Just professional, discreet execution.",
        "pain_h2": "What Makes a Divorce Home Sale Different",
        "pain_intro": "Selling a house during a divorce is not a normal transaction. The emotional stakes are higher, the legal oversight is tighter, and both parties need to feel the process was fair. Here is where most divorcing couples hit walls when they hire an agent who does not handle this regularly.",
        "pain_cards": [
            ("Agents Who Pick Sides", "Too many agents unconsciously align with whichever spouse called first. That bias shows up in pricing conversations, showing schedules, and negotiation decisions — and it poisons the relationship between the exes before the home even sells. Jorge stays explicitly neutral and communicates the same information to both parties at the same time."),
            ("Emotional Pricing Disputes", "One spouse wants to price it high because they are emotionally attached. The other wants a fast sale at any cost. Without a true third-party CMA backed by real market data, pricing becomes a negotiation between the two of you instead of a data-driven decision — and the home sits on market while you argue."),
            ("Attorney Coordination Failures", "Divorce sales almost always require signatures from both spouses, sometimes through attorneys, sometimes through court order. Agents who have never handled this miss deadlines, mishandle disclosure forms, and cause closings to slip. Jorge coordinates directly with both attorneys from day one."),
            ("Showing and Access Conflicts", "One spouse still lives in the home. The other has moved out. Who shows the home? Who gets notified? What happens when one spouse refuses showings? Without clear protocols from day one, simple scheduling becomes another source of conflict. Jorge handles all access coordination and documents every communication."),
            ("Equitable Distribution Accounting", "In New Jersey, the proceeds from the sale of a marital home typically flow through escrow or attorneys for equitable distribution. Agents who do not understand this send funds to the wrong place, create tax headaches, and expose both spouses to claims of mishandling. Jorge knows exactly how NJ handles this."),
        ],
        "mid_cta_h2": "Need to Sell, Both of You Agreed on That — Let's Just Get It Done.",
        "mid_cta_p": "A free, completely confidential consultation. Both spouses can be on the call, or Jorge can meet with each of you separately. The goal is one thing: a clean sale, a fair price, and both of you moving on with your lives.",
        "why_jorge_h2": "Why Jorge Handles Divorce Sales Differently",
        "why_jorge_ps": [
            "Jorge has helped multiple divorcing couples in NJ sell their homes without the sale becoming another fight. The approach is simple: treat both spouses as clients, communicate with both equally, run data not opinions, and coordinate directly with both attorneys so nothing falls through the cracks.",
            "Before becoming a full-time Realtor in 2017, Jorge personally bought, renovated, and sold over 60 homes as a real estate investor. He has seen every complication — and he has the pricing data to back up every recommendation. In a divorce sale, that data-driven approach removes the emotion from the pricing conversation.",
            "Jorge also understands discretion. Signs can be omitted. Showings can be restricted. Social media marketing can be dialed back. The sale can look and feel like any normal move — because how the neighborhood perceives the sale matters to both of you.",
        ],
        "why_jorge_credentials": [
            "Neutral third-party — both spouses get identical information at the same time",
            "Direct coordination with both divorce attorneys from day one",
            "Full discretion available — no yard sign, private showings, quiet marketing",
            "Data-driven CMA removes emotion from the pricing decision",
            "Escrow and proceeds handled exactly to NJ equitable-distribution requirements",
            "Flexible timeline — can work with court deadlines or settlement schedules",
        ],
        "process_h2": "A Divorce Sale, Handled Right",
        "process_intro": "The goal is for both of you to look back six months from now and feel the sale was fair, the agent was professional, and the process did not make the divorce worse. Here is exactly how that happens.",
        "process_steps": [
            ("Private Consultation — Together or Separately", "Jorge meets with both spouses — in the same room, on separate calls, or through attorneys. Whatever works. The goal is to understand the legal situation, the timeline, and each spouse's priorities before the home even hits the market."),
            ("Data-Driven CMA Presented to Both", "Jorge runs a full <a href=\"home-valuation.html\" style=\"color: white; text-decoration: underline;\">Comparative Market Analysis</a> using recent comparable sales, current pending contracts, and 90-day neighborhood trends. Both spouses and both attorneys receive the same report at the same time."),
            ("Attorney Coordination From Day One", "Jorge confirms signing authority, court orders, and any restrictions with both divorce attorneys before listing. Every offer, price adjustment, and major decision loops in both attorneys so nothing gets contested later."),
            ("Discretion-First Marketing", "Depending on what both spouses want, marketing can be high-visibility or quiet. Private MLS listings, no yard sign, limited open houses — whatever keeps the sale professional and protects both parties' privacy."),
            ("Clean Closing and Fair Proceeds", "At closing, proceeds flow exactly as both attorneys have directed — typically into attorney escrow for equitable distribution per NJ law. Jorge manages the title company, appraisal, inspections, and every detail so the closing itself is boring. That is the goal."),
        ],
        "ai_h2": "Discreet Marketing That Still Gets Top Dollar",
        "ai_intro": "The challenge in a divorce sale is balancing privacy with sale price. Jorge's AI-powered marketing system can be dialed up or down depending on how public both spouses want the listing to be — without sacrificing the buyer reach that drives competitive offers.",
        "ai_cards": [
            ("Targeted Digital Ads, No Public Posts", "Paid buyer-targeting ads on Facebook and YouTube reach qualified buyers in your price range and town without posting the listing to Jorge's public social feeds. Your neighbors do not need to know your business."),
            ("Private Showings Only, On Your Schedule", "No open houses unless both spouses agree. Every showing is by appointment, pre-qualified buyers only, and documented. One spouse can approve showings by text so there is no coordination conflict."),
            ("Full MLS Exposure, Minimized Signage", "Your home still gets full MLS distribution — which is where 90% of serious buyers come from — but the yard sign, print ads, and social media can be turned off entirely. Maximum buyer reach, minimum neighborhood noise."),
        ],
        "faq_h2": "Divorce Home Sale — Your Questions, Answered",
        "faqs": [
            ("Can one spouse list the house without the other's signature?", "In most NJ divorce situations, no. If both spouses are on the title, both must sign the listing agreement and the sale contract. Jorge confirms this with both attorneys before listing. If one spouse is non-cooperative, the court can sometimes compel the sale — your divorce attorney handles that side, and Jorge coordinates around whatever the court orders."),
            ("How are sale proceeds split?", "New Jersey uses equitable distribution, which is not automatically 50/50. The exact split is determined by your divorce settlement or court order. Jorge does not determine or calculate this — proceeds flow to whichever attorney escrow both sides have agreed to, and the attorneys handle distribution per the settlement."),
            ("Can we still sell if we hate each other?", "Yes. Many divorce sales happen between spouses who are not speaking directly. Jorge communicates with each spouse separately or through attorneys. As long as both spouses sign the necessary documents when required, the sale moves forward regardless of personal conflict."),
            ("What if one of us wants to buy the other out instead?", "Jorge can run a full CMA to establish a fair-market value for buyout negotiations, even if the home never hits the market. That valuation becomes the neutral third-party number both attorneys use in the settlement. No listing, no sale — just an honest number."),
            ("How do we handle the house emotionally? One of us still lives there.", "That is the single hardest part, and Jorge has a specific protocol for it. Showings are scheduled around the resident spouse's availability. Personal items can be temporarily removed. Staging can minimize emotional triggers. And Jorge handles the buyer communication so the resident spouse does not have to interact with strangers touring their home."),
            ("Is everything confidential?", "Yes. Jorge signs NDAs if requested. Marketing materials can avoid mentioning divorce entirely. Neighbors, social media, and extended family do not need to know the reason for the sale. The transaction is recorded publicly, like any sale — but the context is entirely private."),
        ],
        "final_cta_h2": "You Both Agreed to Sell. Let's Get It Done Professionally.",
        "final_cta_p": "Schedule a confidential consultation — together or separately. Jorge coordinates with both attorneys, runs the data, and handles the sale so this is one less thing you have to fight about.",
        "internal_links": [
            ("sell-your-home.html", "Sell Your Home With Jorge"),
            ("home-valuation.html", "Get a Private Home Valuation"),
            ("how-we-sell-your-home.html", "How Our Marketing Works"),
            ("inherited-home-nj.html", "Selling an Inherited Home in NJ"),
            ("why-jorge-ramirez.html", "Why Choose Jorge"),
            ("index.html#contact", "Contact Jorge"),
        ],
    },

    "inherited-home-nj": {
        "breadcrumb_parent": ("Sell Your Home", "sell-your-home.html"),
        "breadcrumb_name": "Sell an Inherited Home",
        "title_tag": "Selling an Inherited House in NJ | Probate Help | Jorge Ramirez",
        "meta_title": "Selling an Inherited House in NJ — Probate, Taxes & Multiple Heirs Handled | Jorge Ramirez",
        "meta_desc": "Inherited a house in New Jersey? Jorge Ramirez walks you through probate, tax basis, and multi-heir coordination. Sell smoothly — even if the house needs work. Call 908-230-7844.",
        "keywords": "selling inherited house NJ, inherited home New Jersey, probate real estate NJ, sell inherited property NJ, inherited home tax basis NJ, multiple heirs home sale NJ, executor selling house NJ",
        "llm_context": "Jorge Ramirez (NJ License #1754604) is a New Jersey real estate agent who specializes in inherited home sales and probate real estate. He coordinates with estate attorneys, handles multi-heir communication, advises on stepped-up tax basis timing, and manages as-is sales for homes that need work. Contact: 908-230-7844.",
        "hero_h1": "Inherited a House in New Jersey? Here's What You Actually Need to Know.",
        "hero_p": "Losing a loved one is hard. Dealing with their house while you grieve is harder. Jorge Ramirez walks heirs and executors through the entire process — probate timing, tax basis, multi-heir coordination, and whether to sell as-is or fix it up first. No pressure, no upsell. Just clear guidance from someone who has helped dozens of NJ families navigate this.",
        "pain_h2": "Why Inherited Home Sales Go Sideways",
        "pain_intro": "An inherited house is not a normal sale. There are tax implications, probate timelines, multiple people with opinions, and often a property that has not been updated in 30 years. Here is where inherited-home sales fall apart when handled by an agent who has never done one.",
        "pain_cards": [
            ("Missing the Stepped-Up Basis Window", "When someone inherits a house, the tax basis usually steps up to fair market value at the date of death. Sell within a reasonable timeframe and there is typically little to no capital gains tax. Sit on the house for years and any appreciation is taxable. Most heirs have no idea this clock is ticking. Jorge flags it on day one and recommends getting a date-of-death appraisal immediately."),
            ("Probate Delays Nobody Warned You About", "In New Jersey, you generally cannot sell a house that is still in probate without the executor's letters testamentary. Agents who list inherited homes before probate is open create signed contracts that cannot close — and frustrated heirs who now think the agent screwed up. Jorge confirms probate status with the estate attorney before listing."),
            ("Sibling Disagreements That Kill Deals", "Three heirs, three opinions. One wants top dollar. One wants speed. One wants to keep it. Without a structured process for decision-making and a neutral third party running the numbers, inherited-home sales become family therapy sessions that drag on for years. Jorge runs a clean CMA, presents the data to all heirs at once, and keeps the conversation focused on facts."),
            ("Dated Homes Priced as If They Were Updated", "Grandma's house has a pink bathroom, shag carpet, and a 1987 kitchen. Agents who price it based on recent sales of renovated homes get the price wrong, wonder why there are no offers, and push for cuts. Jorge prices inherited homes honestly — factoring in condition, market, and whether it is worth updating first or selling as-is to an investor."),
            ("Emotional Clean-Out Paralysis", "Sixty years of belongings. Photos, furniture, personal papers. Nobody wants to throw anything away, but nobody wants to keep it all either. Weeks turn into months. The house sits. Property taxes and insurance bills keep coming. Jorge connects families with estate clean-out services that handle the hard part and accelerate the sale."),
        ],
        "mid_cta_h2": "Inherited a Home? Let's Figure Out the Right Move — Together.",
        "mid_cta_p": "A free, no-obligation consultation. Jorge can walk you through the probate timeline, tax basis, and whether to sell as-is or update first. Bring your siblings or the executor on the call — it helps when everyone hears the same information at the same time.",
        "why_jorge_h2": "How Jorge Handles Inherited Home Sales",
        "why_jorge_ps": [
            "Jorge has helped many NJ families sell inherited homes — from pristine well-maintained properties to houses that had not been touched in 40 years. The first conversation is never about listing the house. It is about understanding the probate status, the tax situation, and what all the heirs actually want.",
            "Before becoming a full-time Realtor in 2017, Jorge personally flipped 60+ houses. He has walked through dozens of dated, estate-sale homes and can tell you in 10 minutes whether it is worth spending $20K on paint and flooring to make $60K more on the sale — or whether it is smarter to sell as-is to one of his investor contacts next week.",
            "Jorge works directly with your estate attorney, probate court timelines, and as many heirs as the estate has. Communication goes to everyone at the same time so no one ever feels left out or surprised.",
        ],
        "why_jorge_credentials": [
            "Direct coordination with the estate attorney on probate timing and letters testamentary",
            "Honest advice on whether to sell as-is or update first — backed by flip experience",
            "Multi-heir communication protocols — everyone gets the same info at the same time",
            "Network of estate clean-out services, contractors, and cash-buyer investors",
            "Pricing informed by date-of-death valuation for tax basis purposes",
            "Flexible timeline — can move fast or slow depending on estate needs",
        ],
        "process_h2": "From Probate to Closing, Step by Step",
        "process_intro": "Every inherited-home sale is different, but the path is the same. Here is how Jorge takes a family from 'we need to do something with the house' to closed, proceeds distributed, estate wrapped.",
        "process_steps": [
            ("Free Consultation With the Executor and Heirs", "Jorge sits down with whoever is running point — usually the executor, often with siblings on the call. The goal is to understand the probate status, confirm who has signing authority, and identify what condition the house is in. No commitments, no pressure."),
            ("Probate and Tax Basis Check", "Jorge coordinates with the estate attorney to confirm probate is open and letters testamentary are in hand. He also flags whether a date-of-death appraisal exists — critical for the <a href=\"home-valuation.html\" style=\"color: white; text-decoration: underline;\">stepped-up basis</a> that determines how much capital gains tax, if any, the estate or heirs will owe."),
            ("Condition Walkthrough and Sell-As-Is Analysis", "Jorge walks the house, often with the executor, and gives a straight answer: is it worth spending time and money updating, or does it make more sense to sell as-is? Sometimes the math says renovate. Often it says sell to an investor at a fair price and distribute faster. Either way, it is the heirs' call — Jorge just runs the numbers."),
            ("Full CMA and Strategy Meeting", "A complete Comparative Market Analysis presented to all heirs. Jorge lays out the three to four realistic paths — sell as-is to retail buyer, sell as-is to investor, light cosmetic update then list, major renovation — with realistic net proceeds for each. The heirs pick."),
            ("Listing, Sale, Proceeds Distribution", "Jorge runs the marketing, negotiates offers, coordinates the attorney review, and manages the closing. Proceeds flow to the estate account or attorney escrow exactly as the estate attorney directs. Jorge closes the file, sends every heir the closing docs, and the chapter ends."),
        ],
        "ai_h2": "When the House Needs Work, We Market to the Right Buyers",
        "ai_intro": "Inherited homes often need updating — and marketing them to the wrong audience wastes everyone's time. Jorge's AI-powered buyer targeting matches each inherited listing to the buyer pool most likely to make a real offer, whether that is a retail family who loves a renovation project or an investor who writes cash offers.",
        "ai_cards": [
            ("Investor Network for As-Is Sales", "If the house is too dated or damaged for retail, Jorge taps his network of local NJ flippers and investors. Multiple bids, typically cash, fast close. The estate gets a fair as-is price and moves on — no repairs, no showings, no delays."),
            ("Targeted Ads for 'Project Home' Retail Buyers", "Some retail buyers specifically want a home they can update themselves. Jorge's Facebook and YouTube targeting finds them — and their agents. These buyers often pay more than investors because they are emotional, not spreadsheets."),
            ("Staging and Light Updates When Worth It", "For homes where $10K–$20K in cosmetic updates would unlock $40K+ in sale price, Jorge has a contractor network that can turn the house around in three weeks. The numbers get presented to the heirs before any money is spent."),
        ],
        "faq_h2": "Inherited Home Sale — The Questions Heirs Actually Ask",
        "faqs": [
            ("Do we owe capital gains tax when we sell?", "Usually very little, if you sell soon. When someone inherits a house, the tax basis typically steps up to the fair market value on the date of death. If you sell within a reasonable timeframe at a similar price, there is little to no gain to tax. Confirm this with a CPA — every situation is different — but Jorge will flag the issue and help you get a date-of-death valuation if needed."),
            ("Can we sell before probate is complete?", "Not usually. In New Jersey, the executor needs letters testamentary from the probate court before signing on behalf of the estate. Jorge will confirm probate status with the estate attorney before listing. In some cases, the home can be marketed with a closing contingent on probate completion."),
            ("What if the siblings disagree?", "Jorge keeps it neutral. All heirs receive the same information at the same time, the CMA is presented to everyone together, and decisions are documented. When siblings still cannot agree, the estate attorney and the will (or court) usually determine who has final authority — typically the executor."),
            ("The house is dated and needs work. Should we fix it up?", "Sometimes yes, sometimes no. Jorge walks the property and runs the numbers both ways — sell as-is versus update and list. If $15K in paint, flooring, and light kitchen updates unlock $50K more in sale price, it is worth it. If the house needs a full gut, it is almost always better to sell as-is to an investor."),
            ("How long does an inherited-home sale take?", "Once probate is clear and the decision to sell is made, most inherited NJ homes close in 45–90 days. If the home is sold as-is to a cash investor, it can close in as little as 2–3 weeks. If it needs updates first, add 3–6 weeks on the front end."),
            ("What about Mom's furniture and belongings?", "Jorge works with estate clean-out companies that handle this for a flat fee or on consignment. Family members typically take what they want first, then the pros clear the rest. This step cannot be skipped — the house has to be show-ready or the buyer pool shrinks dramatically."),
        ],
        "final_cta_h2": "Inherited a Home? Let's Make the Next Step Simple.",
        "final_cta_p": "A free consultation. Bring the executor. Bring your siblings. Jorge walks everyone through probate timing, tax basis, sell-vs-update options, and realistic numbers. Then the family decides what to do.",
        "internal_links": [
            ("sell-your-home.html", "Sell Your Home With Jorge"),
            ("home-valuation.html", "Get a Free Home Valuation"),
            ("divorce-home-sale-nj.html", "Divorce Home Sale Help"),
            ("sell-rental-property-nj.html", "Selling a Rental Property"),
            ("why-jorge-ramirez.html", "Why Choose Jorge"),
            ("index.html#contact", "Contact Jorge"),
        ],
    },

    "sell-rental-property-nj": {
        "breadcrumb_parent": ("Sell Your Home", "sell-your-home.html"),
        "breadcrumb_name": "Sell a Rental Property",
        "title_tag": "Selling a Rental Property in NJ | 1031 & Tenant Help | Jorge Ramirez",
        "meta_title": "Selling a Rental Property in NJ — 1031 Exchanges, Tenants, Taxes | Jorge Ramirez",
        "meta_desc": "Selling a rental property in NJ? Jorge Ramirez coordinates tenants, 1031 exchanges, and investor marketing for landlords. Licensed agent, 60+ flips. Call 908-230-7844.",
        "keywords": "sell rental property NJ, landlord selling house NJ, 1031 exchange NJ, selling investment property New Jersey, tenant occupied sale NJ, absentee owner real estate NJ",
        "llm_context": "Jorge Ramirez (NJ License #1754604) helps NJ landlords sell rental properties — including 1031 exchange coordination, tenant-occupied sales, absentee owner representation, and investor buyer marketing. He has flipped 60+ homes personally and speaks the investor language. Contact: 908-230-7844.",
        "hero_h1": "Selling a Rental Property in NJ? Here's How to Do It Without Leaving Money on the Table.",
        "hero_p": "Selling a rental is a different animal. Tenants, 1031 exchanges, tax basis, depreciation recapture, cap rates, investor buyers — most agents do not speak the language. Jorge Ramirez does. He has flipped 60+ houses personally, built rental portfolios, and worked with dozens of NJ landlords on the exit. Call 908-230-7844.",
        "pain_h2": "Where Landlords Lose Money on the Sale",
        "pain_intro": "A rental sale is not a primary-residence sale. The buyers are different, the tax stakes are bigger, and the tenants add complexity. Here is where landlords get squeezed when they hire an agent who has never handled an investment property.",
        "pain_cards": [
            ("Selling Occupied Without a Plan", "Tenant-occupied showings kill deals. Tenants clutter, do not clean, refuse access, or actively sabotage showings because they do not want to move. Jorge plans the tenant strategy before listing — negotiate a move-out incentive, list after lease ends, or market specifically to investor buyers who will keep the tenant in place."),
            ("Missing the 1031 Exchange Window", "A 1031 like-kind exchange lets you defer capital gains tax when you roll proceeds into another investment property. But you have 45 days to identify the replacement and 180 days to close — and your sale proceeds must go to a qualified intermediary, not your personal account. Agents who do not understand 1031 break the exchange and cost landlords tens of thousands in avoidable tax."),
            ("Pricing Like an Owner, Not an Investor", "Retail buyers buy on emotion. Investor buyers buy on cap rate, cash-on-cash return, and rent comps. A rental priced for retail buyers often sits — because retail buyers do not want tenants, and investors think the price is too high. Jorge prices rentals based on which buyer pool the property fits."),
            ("Depreciation Recapture Surprises", "After years of claiming depreciation, that tax shelter comes back at sale time as depreciation recapture — taxed at up to 25%. Landlords who never planned for this are blindsided when the CPA runs the numbers post-closing. Jorge flags this on day one so you can plan (or use a 1031 to defer it)."),
            ("Ignoring the Investor Buyer Pool", "The best rental sales often go to other investors — not retail buyers. Jorge's network includes local NJ flippers, small landlords expanding their portfolio, and out-of-state buyers doing 1031 exchanges. Listing on MLS alone misses this audience entirely."),
        ],
        "mid_cta_h2": "Ready to Sell a Rental? Let's Talk Strategy First.",
        "mid_cta_p": "A free strategy call. Jorge runs the numbers on your property — rents, expenses, cap rate, likely sale price, and tax implications. Then you decide whether to sell now, sell later, or do a 1031 into something better.",
        "why_jorge_h2": "Why Landlords Trust Jorge With the Exit",
        "why_jorge_ps": [
            "Jorge is not a retail-only agent trying to figure out investment properties in real time. He has flipped 60+ houses in NJ, built his own rental portfolio, and actively works with investor buyers every week. When a landlord calls Jorge, the first 10 minutes are a real conversation about cap rate, rent comps, and exit strategy — not sales pitches.",
            "That investor lens matters in three places. First, pricing: Jorge knows what investors will pay, so the listing lands in the right zone. Second, buyer marketing: Jorge has direct relationships with NJ investors doing 1031 exchanges and portfolio expansion. Third, transaction handling: tenant coordination, as-is inspections, and 1031 deadlines all get managed without drama.",
            "Jorge also works with absentee owners. If you live out of state and cannot drive to the property, everything can be handled remotely — e-signatures, virtual walkthroughs, attorney coordination, showing approvals by text. Selling a NJ rental from California or Florida is normal for Jorge.",
        ],
        "why_jorge_credentials": [
            "60+ personal house flips — speaks the investor language fluently",
            "Network of NJ investor buyers for off-market and on-market deals",
            "1031 exchange coordination with qualified intermediaries",
            "Tenant negotiation, move-out incentives, cash-for-keys deals handled",
            "Full remote representation for absentee and out-of-state landlords",
            "Pricing strategy tuned to investor buyers, not just retail",
        ],
        "process_h2": "How a Rental Sale Actually Runs",
        "process_intro": "Every rental is different, but the playbook is the same. Here is how Jorge takes a landlord from 'thinking about selling' to closed, 1031 deployed or cash in hand.",
        "process_steps": [
            ("Strategy Call — What Are You Actually Trying to Do", "Cash out? 1031 into a bigger property? Retire the mortgage? Move to out-of-state investing? The sale strategy depends on the goal. Jorge runs the real numbers — rents, expenses, equity, tax basis, likely net after tax — before any listing conversation."),
            ("Tenant Strategy Locked In", "If the property is occupied, Jorge decides with you how to handle it. Market with the tenant in place and target investor buyers? Offer the tenant cash-for-keys to move? Wait for the lease to end? Each path has different timelines and different sale prices. Pick one before listing."),
            ("Pricing for the Right Buyer Pool", "A full CMA plus an investor analysis — cap rate, cash-on-cash, DSCR-lender-friendly pricing. Jorge positions the property in the zone where it attracts the most qualified buyers — whether that is retail, small landlord, or institutional investor."),
            ("1031 Exchange Setup (If Applicable)", "If you are doing a 1031, Jorge coordinates with your qualified intermediary before closing so proceeds never touch your account. The 45-day identification clock starts at closing — Jorge also helps you identify replacement properties inside that window."),
            ("Closing and Tax-Ready Documentation", "At closing, Jorge makes sure every document your CPA will need is collected in one place — HUD statement, depreciation schedule handoff, tenant security deposit transfer, prorated rent accounting. Your next April filing becomes routine, not a scavenger hunt."),
        ],
        "ai_h2": "Getting Your Rental in Front of the Right Buyers",
        "ai_intro": "Rentals do not sell themselves to the general public. Jorge's marketing stack targets the buyer pool that actually closes on investment property — and filters out the tire-kickers who waste time.",
        "ai_cards": [
            ("Direct-to-Investor Outreach", "Jorge's NJ investor network gets first look on many rentals — often before the MLS listing goes live. Investors writing cash offers in 7 days is common when the deal numbers work. This single channel closes more Jorge rental listings than public MLS."),
            ("Targeted Ads to 1031 Buyers", "Out-of-state investors doing 1031 exchanges need NJ properties in narrow time windows. Jorge's paid targeting reaches them in the exact 45-day ID window. High-intent, fast-moving buyers."),
            ("Cap Rate–Forward Marketing Copy", "Listing descriptions for Jorge's rental sales lead with numbers — cap rate, gross rents, NOI, cash-on-cash — because that is what investor buyers scan for. Retail-style flowery copy gets skipped by this audience."),
        ],
        "faq_h2": "Rental Property Sale — The Questions Landlords Ask",
        "faqs": [
            ("Do I have to evict my tenant before selling?", "No. Many investor buyers prefer to inherit a tenant, especially if the lease is current and the rent is market-rate. If you do want vacant possession, Jorge can negotiate a cash-for-keys agreement to incentivize the tenant to move early. Forced evictions are rarely worth it — they take months and scare off buyers."),
            ("How does a 1031 exchange work?", "A 1031 lets you defer capital gains tax when you sell an investment property and buy another 'like-kind' investment property within specific timelines. Sale proceeds go to a qualified intermediary (not you) at closing. You have 45 days to identify replacement properties and 180 days to close on one. Jorge coordinates with your QI from day one so the exchange does not break."),
            ("What is depreciation recapture going to cost me?", "When you sell, the depreciation you have claimed over the years is 'recaptured' and taxed at up to 25%. On a property with $100K in accumulated depreciation, that could mean up to $25K in tax. A 1031 exchange defers both capital gains AND depreciation recapture — which is why 1031s are so popular for long-held rentals. Confirm exact numbers with your CPA."),
            ("Can you sell my rental if I live out of state?", "Yes. Jorge handles absentee landlord sales regularly. Everything can be done remotely — virtual walkthroughs, e-signatures, inspections coordinated by Jorge, attorney review by email, closing by mobile notary or mail-away documents. You do not need to come to NJ at any point if you do not want to."),
            ("Will I get more selling vacant or occupied?", "It depends on the buyer pool. Retail buyers (primary residence) want vacant — they will pay more but only buy vacant. Investor buyers often want occupied with a current tenant — they pay slightly less but close faster and with fewer contingencies. Jorge runs the numbers both ways before recommending."),
            ("What if my tenant does not want to leave?", "If the lease is current, the lease transfers to the new owner. The new owner must honor the lease terms. If the tenant is month-to-month, NJ requires proper written notice for termination — and NJ tenant laws favor tenants. Eviction for sale purposes is not a legal basis in NJ; the tenant has to violate the lease or the lease has to end. Cash-for-keys is usually the fastest path."),
        ],
        "final_cta_h2": "Time to Exit? Let's Run the Numbers Together.",
        "final_cta_p": "A free strategy call — your rental, your situation, real numbers. Cap rate, likely sale price, 1031 options, tax implications. Then you decide whether to sell now, wait, or reposition.",
        "internal_links": [
            ("sell-your-home.html", "Sell Your Home With Jorge"),
            ("home-valuation.html", "Get a Free Valuation"),
            ("investment-property-nj.html", "Buying an Investment Property"),
            ("inherited-home-nj.html", "Selling an Inherited Home"),
            ("why-jorge-ramirez.html", "Why Choose Jorge"),
            ("index.html#contact", "Contact Jorge"),
        ],
    },

    "downsizing-nj": {
        "breadcrumb_parent": ("Sell Your Home", "sell-your-home.html"),
        "breadcrumb_name": "Downsizing",
        "title_tag": "Downsizing Your NJ Home | Empty Nester Realtor | Jorge Ramirez",
        "meta_title": "Downsizing in NJ — Empty Nester Home Sale & Move | Jorge Ramirez",
        "meta_desc": "Ready to downsize in NJ? Jorge Ramirez coordinates the sale of your family home and the purchase of your next one — so you only move once. Call 908-230-7844.",
        "keywords": "downsizing NJ, empty nester realtor NJ, downsize home New Jersey, selling family home NJ, 55 plus community NJ, retire in New Jersey, downsize and move NJ",
        "llm_context": "Jorge Ramirez (NJ License #1754604) helps NJ empty nesters and retirees downsize from large family homes to right-sized next homes. He coordinates the sale and the purchase in parallel so clients only move once, and handles estate-sale coordination for decades of accumulated belongings. Contact: 908-230-7844.",
        "hero_h1": "Downsizing in New Jersey? Let's Get You Into the Next Chapter — Without Moving Twice.",
        "hero_p": "The kids moved out. The big house is too much to maintain. You want something smaller, easier, maybe closer to the grandkids. Jorge Ramirez helps NJ empty nesters sell the family home and move into the right-sized next home on a timeline that actually works. Coordinated, not chaotic.",
        "pain_h2": "Why Downsizing Goes Wrong",
        "pain_intro": "Downsizing sounds simple until you try to do it. The emotional weight of leaving a family home, the logistics of coordinating two transactions, and the reality of 30 years of accumulated belongings all pile up at once. Here is where most empty nesters get stuck.",
        "pain_cards": [
            ("Selling Before Knowing Where You're Going", "Many downsizers list their home, get an offer, and then panic because they do not know where they are moving. The result: a rushed purchase at a bad price, or temporary housing for months. Jorge starts with the next chapter first — what does your ideal downsize look like? Then plans the sale around it."),
            ("Buying Before Selling the Current Home", "The opposite problem. You find the perfect smaller place, make an offer, and now you are sitting on two mortgages hoping your current home sells fast. This is how equity gets destroyed — you accept a lower offer just to get out from under. Jorge coordinates the two transactions so you are never exposed."),
            ("Emotional Attachment Clouding the Pricing", "You raised three kids in this house. The kitchen where you made Thanksgiving dinner for 20 years is worth more to you than the market. Setting that aside is the hardest part of downsizing. Jorge shows you the real CMA, respects the emotional weight, and helps you price based on market data, not memories."),
            ("Thirty Years of Stuff", "Attic, basement, garage, three bedrooms, dining room. Six bins of kids' schoolwork. Three rooms of furniture that will not fit. Nobody wants to deal with it, but the new smaller home will not hold it. Jorge connects you with downsizing specialists, estate-sale pros, and charities so the belongings are handled without taking a year."),
            ("Not Understanding the Age-Related Tax Breaks", "New Jersey has specific property tax programs for seniors — the Senior Freeze (PTR), ANCHOR, and the Property Tax Reimbursement program. The capital gains home-sale exclusion (up to $500K married filing jointly) is also huge for long-term owners. Jorge flags all of these so your CPA can maximize them."),
        ],
        "mid_cta_h2": "Ready to Downsize? Let's Map Out the Right Order.",
        "mid_cta_p": "A free consultation — sell first, buy first, or do them in parallel. Jorge runs the timing, the financing bridge options, and what to look for in your next home so you only move once.",
        "why_jorge_h2": "Downsizing, Done Right",
        "why_jorge_ps": [
            "Jorge has helped many NJ empty nesters through the downsize. It is never just a transaction — it is a life transition, and the home carries decades of memory. Jorge takes the time to understand what matters to you before running any numbers.",
            "The coordinated approach means Jorge handles both the sale and the purchase in parallel. That protects you from ending up with two mortgages, or stuck in temporary housing, or accepting a bad offer out of panic. It also means one agent, one point of contact, one calendar — instead of juggling separate people for the sell side and buy side.",
            "Jorge also knows the NJ downsize destinations cold — 55+ communities, walkable downtowns like Summit or Westfield, quieter Morris County towns, Jersey Shore options, and the calculation of staying in NJ vs moving to Florida or the Carolinas. The conversation starts with what you actually want next, not with the listing.",
        ],
        "why_jorge_credentials": [
            "Coordinates the sale and the purchase in parallel — one agent, one timeline",
            "Deep knowledge of NJ 55+ communities, walkable downtowns, Shore markets",
            "Bridge loan, HELOC, and contingent-offer strategies for timing the two transactions",
            "Network of downsizing coaches, estate-sale companies, and movers",
            "Flags NJ senior tax programs (PTR, ANCHOR, Senior Freeze) and capital gains exclusion",
            "Patient, respectful process — no pressure to list before you are ready",
        ],
        "process_h2": "How the Downsize Actually Unfolds",
        "process_intro": "The best downsizes take 6–12 months from first conversation to handing over the keys. Rushed downsizes cost money and cause regret. Here is the pace that works.",
        "process_steps": [
            ("Free Discovery Call — What's the Next Chapter?", "Jorge asks the real questions first. Stay in NJ or move? Closer to grandkids? Walk to a downtown? Condo, townhome, or smaller single-family? Lock-and-leave or space for hobbies? This conversation drives everything downstream."),
            ("Current Home Valuation", "A full <a href=\"home-valuation.html\" style=\"color: white; text-decoration: underline;\">Comparative Market Analysis</a> on the current home — what it would realistically sell for today, what light prep could add, and the timeline. This tells you how much you have to work with for the next place."),
            ("Next-Home Search in Parallel", "While the current home is being prepped, Jorge shows you next homes that match the Chapter Two vision. The goal is to have a target picked before listing the current home — so when the current home sells, you already know where you are going."),
            ("Coordinated Listing and Offer Timing", "Jorge lists the current home strategically, often with extended closing or rent-back so you have 60–90 days to close on the next place. In stronger markets, the next-home offer can be written contingent on the current-home sale."),
            ("Move, Unpack, Breathe", "Jorge connects you with downsizing coaches, senior movers, and clean-out services. The move happens once, not twice. Three weeks later, you are unpacked in the new place and wondering why you waited so long."),
        ],
        "ai_h2": "Marketing a Long-Loved Family Home",
        "ai_intro": "The homes downsizers sell are often the best homes in their neighborhoods — long-held, well-maintained, updated over the years. They deserve marketing that tells that story. Jorge's system does.",
        "ai_cards": [
            ("Storytelling Marketing for Family Homes", "Professional video walkthroughs narrated around the lifestyle — not just the square footage. Retail buyers fall in love with homes that feel like homes, and Jorge's marketing makes that emotional connection before the first showing."),
            ("Target Buyer Profiling", "Young families moving up from a first home are the most likely buyers for a 4-bedroom family home. Jorge's AI targeting puts your listing in front of that exact demographic in commuter towns through Facebook, YouTube, and Instagram."),
            ("Flexible Closing and Rent-Back Terms", "Most downsizers need 60–90 days to close on their next home. Jorge negotiates extended closing or post-closing rent-back into the purchase agreement so you are not rushed."),
        ],
        "faq_h2": "Downsizing — Questions Empty Nesters Actually Ask",
        "faqs": [
            ("Should I sell first or buy first?", "In most NJ markets, sell first. Coming to the next purchase with cash in hand gives you a stronger offer, eliminates contingency contingencies, and prevents the nightmare of two mortgages. Jorge can negotiate extended closing or rent-back to bridge the timing so you do not have to move twice."),
            ("How do I know where to move?", "Jorge spends the first conversation on this — not the sale. The answer depends on grandkids, climate, tax situation, social life, and what your ideal Tuesday looks like in the next chapter. After that, the search narrows quickly: downtown Summit, a 55+ community in Monroe Township, a townhome in Montclair, or moving out of state entirely."),
            ("What about all the stuff?", "Nobody wants to deal with it, but it has to happen. Jorge has a network of senior-move managers and estate-sale companies who handle this professionally. Family gets first pick, the good stuff sells, the rest gets donated or hauled. It takes 2–4 weeks with pros — versus a year of weekends doing it yourself."),
            ("Will I owe capital gains tax on the sale?", "If you have lived in the home as your primary residence for at least 2 of the last 5 years, you can exclude up to $250K (single) or $500K (married filing jointly) of gain from federal capital gains. For most long-term NJ owners, this covers the entire gain. Confirm with your CPA — state tax rules can differ."),
            ("Do I have to leave NJ to lower my property taxes?", "No — but it is worth comparing. NJ has the highest property taxes in the country, which is why many retirees move to PA, NC, FL, or SC. If you are staying in NJ, the Senior Freeze (PTR) and ANCHOR programs can meaningfully offset your tax bill. Jorge helps you think through the stay-vs-leave math honestly."),
            ("What if we change our minds halfway through?", "Jorge's listing agreements are flexible — short-term contracts, no penalty for pausing. Downsizing is a major life transition, and second thoughts are normal. Jorge will never push you to list before you are ready, and if you pause for 6 months to think, that is fine."),
        ],
        "final_cta_h2": "Ready for the Next Chapter? Let's Plan It Together.",
        "final_cta_p": "A free, unhurried consultation. Talk through the timing, the next destination, and the moving logistics. No pressure to list anything until you are sure.",
        "internal_links": [
            ("sell-your-home.html", "Sell Your Home"),
            ("home-valuation.html", "Free Home Valuation"),
            ("buy-a-home.html", "Buy Your Next Home"),
            ("relocating-from-nj.html", "Relocating From NJ"),
            ("why-jorge-ramirez.html", "Why Choose Jorge"),
            ("index.html#contact", "Contact Jorge"),
        ],
    },

    "relocating-from-nj": {
        "breadcrumb_parent": ("Sell Your Home", "sell-your-home.html"),
        "breadcrumb_name": "Relocating From NJ",
        "title_tag": "Relocating From NJ | Fast Home Sale & Remote Support | Jorge Ramirez",
        "meta_title": "Relocating From New Jersey — Fast Home Sale, Remote Handling | Jorge Ramirez",
        "meta_desc": "Moving out of NJ? Jorge Ramirez handles your NJ home sale remotely — fast timeline, relocation packages, corporate-friendly. Call 908-230-7844.",
        "keywords": "relocating from NJ, selling NJ home to move, job relocation NJ, moving out of New Jersey, relocation realtor NJ, corporate relocation NJ, fast home sale NJ",
        "llm_context": "Jorge Ramirez (NJ License #1754604) helps NJ homeowners selling to relocate out of state — typically job transfers or retirement moves. He handles the sale remotely, works with corporate relocation packages, and coordinates tight timelines. Contact: 908-230-7844.",
        "hero_h1": "Moving Out of NJ? Let's Sell Your Home Fast — and Cleanly.",
        "hero_p": "New job in another state. Kids settled at their new school. Closing date on the new house already locked. Now you need the NJ home sold — fast, for a fair price, and without you having to fly back constantly. Jorge Ramirez handles relocation sales remotely every month. Call 908-230-7844.",
        "pain_h2": "What Makes Relocation Sales Stressful",
        "pain_intro": "Relocation sales have their own special flavor of chaos. You are moving out of state, starting a new job, settling kids into a new school, and trying to sell a house you are no longer living in. Here is where most relocations get ugly.",
        "pain_cards": [
            ("Tight Timelines Nobody Warned You About", "Corporate relocations often come with narrow windows — 60 or 90 days to have the NJ home listed, a closing by a specific quarter, or a buy-out decision to make. Agents who are not used to this cadence miss the window and leave money on the table. Jorge runs relocation sales on tight timelines regularly."),
            ("Being 800 Miles Away During the Listing", "You cannot be at every showing. You cannot meet the photographer. You cannot sign paperwork in person. If your agent is not built for remote work, every step becomes a phone tag marathon. Jorge handles the entire listing remotely — photographer coordination, showings, offers, e-signatures — so your workday in the new city does not get derailed."),
            ("Vacant Home Problems", "Once you move out, the house is empty. Showings happen without you knowing. Snow piles up. A pipe bursts in February. Insurance requirements change. Jorge coordinates with a vacant-home service, checks on the property weekly, and gets a lockbox/showing system set up before you leave."),
            ("Corporate Relocation Package Confusion", "If your employer offers a relocation package, it may include a buy-out option (the company buys your home if it does not sell), a guaranteed home-sale program, or closing-cost reimbursement. Each has tight rules. Jorge has worked with many corporate relocation programs and knows which agent requirements unlock which benefits."),
            ("Pricing to Sell Fast Without Leaving Money on the Table", "Relocators need speed — but dropping the price $50K just to sell fast is a mistake. Jorge prices relocation listings aggressively enough to attract strong offers in the first 2 weeks while still protecting your equity. This is what pricing strategy actually looks like."),
        ],
        "mid_cta_h2": "New State, New Job, Old House to Sell. Let's Make This Easy.",
        "mid_cta_p": "A free relocation consultation. Walk Jorge through your timeline, corporate package (if any), and the NJ home. He lays out the realistic price range, the 30-day plan, and how the remote coordination works.",
        "why_jorge_h2": "Relocation Sales, Handled Fully Remote",
        "why_jorge_ps": [
            "Jorge has sold NJ homes for owners living in California, Florida, Texas, and overseas. Every document can be signed electronically. Every showing gets coordinated by text. Photographs, inspections, appraisals, attorney review, and closing all happen without you having to fly back.",
            "Before becoming a full-time Realtor in 2017, Jorge personally flipped 60+ houses. He understands timelines under pressure and knows how to move fast without making costly mistakes. That experience applies directly to relocation sales — where speed and precision both matter.",
            "Jorge has also worked with corporate relocation packages from major employers. If your company is using a relocation management company (Cartus, Weichert, Aires, etc.), Jorge coordinates with their transferee specialist and follows their reporting protocols so your benefits are preserved.",
        ],
        "why_jorge_credentials": [
            "Fully remote sale — e-signatures, virtual walkthroughs, no in-person required",
            "Corporate relocation program experience (Cartus, Aires, Weichert, others)",
            "Vacant-home coordination — weekly checks, pipe/freeze/security handling",
            "Tight-timeline pricing strategy — sell fast without leaving equity behind",
            "Direct attorney and title company coordination by email",
            "Virtual closing if needed — mobile notary or mail-away documents",
        ],
        "process_h2": "The 60-Day Relocation Sale",
        "process_intro": "Most relocation sales need to close within 60–90 days. Here is the pace that makes that happen without anything slipping.",
        "process_steps": [
            ("Week 1: Remote Listing Setup", "Jorge schedules professional photography while you are still in the house (or right after you move). He handles staging recommendations, light prep work, and listing copy. You sign the listing agreement electronically from wherever you are."),
            ("Week 2: Listing Live, Marketing Live", "Home goes on MLS, Zillow, Realtor.com, and into Jorge's <a href=\"how-we-sell-your-home.html\" style=\"color: white; text-decoration: underline;\">AI-powered ad system</a> targeting buyers in commuter towns. Showings start within 48 hours. You get a weekly text summary of every showing and feedback."),
            ("Weeks 3–4: Offers and Negotiation", "Strong offers typically come in weeks 2–4. Jorge negotiates, runs counters, and recommends the best offer by phone. You sign the purchase agreement electronically from the new state."),
            ("Weeks 5–7: Attorney Review, Inspection, Appraisal", "Jorge coordinates directly with your attorney, the buyer's attorney, the inspector, and the appraiser. Issues get resolved by email. You are copied on everything but not dragged into the weeds."),
            ("Week 8–9: Close and Wire Proceeds", "Closing happens by mobile notary in your new state, or mail-away documents. Proceeds wire to your account the day of closing. The NJ chapter closes cleanly."),
        ],
        "ai_h2": "Marketing a Home You No Longer Live In",
        "ai_intro": "Vacant homes can feel cold in photos and showings. Jorge's marketing system compensates with aggressive digital targeting that brings in more buyers per week — so the home does not sit long enough for vacancy to become a story.",
        "ai_cards": [
            ("Aggressive First-2-Weeks Ad Spend", "Jorge's paid YouTube and Facebook ads run heavily in the first 14 days of the listing — the exact window when buyer interest is highest. More eyeballs in 2 weeks beats a slow drip over 3 months."),
            ("Virtual Staging and 3D Tours", "If the home is empty, Jorge adds virtual staging to the photos and a 3D walkthrough so buyers can experience the home online. Many relocation sales get offers from buyers who never physically visited."),
            ("Relocation-to-NJ Buyer Targeting", "Ironically, many buyers of NJ homes are themselves relocating in — from NYC, from overseas, from other states. Jorge targets those audiences specifically, which shortens the time on market significantly."),
        ],
        "faq_h2": "Relocation Sale — Your Questions Answered",
        "faqs": [
            ("How long will my NJ home take to sell?", "In most of Jorge's service area, well-priced homes receive strong offers within 2–3 weeks and close in 45–60 days. Homes that need work or are overpriced take longer. Jorge tells you the honest timeline and price band before you list — no optimistic numbers just to win the listing."),
            ("Can I really sell without being in NJ?", "Yes, completely. Jorge has sold dozens of NJ homes for owners living in other states. Every document signs electronically, showings coordinate by text, closing happens with a mobile notary in your new state. You never have to fly back if you do not want to."),
            ("What if my company has a relocation package?", "Corporate relocation packages often dictate which agents you can use. Some require specific paperwork submitted to the relocation management company. Some offer buy-out protection if the home does not sell. Jorge has worked with major relocation programs and knows the reporting requirements. Share the package details in the first call."),
            ("What happens if the home does not sell before I move?", "The home becomes a vacant listing — not ideal, but manageable. Jorge coordinates with a vacant-home service for weekly checks, snow removal (if winter), and emergency response. Some owners rent short-term while the home sells; others just price more aggressively. Jorge recommends based on your specific situation."),
            ("Will I owe NJ taxes after I leave?", "You will owe NJ exit tax withholding at closing if you are moving out of state — typically 2% of the sale price or the gain, whichever is higher. Some of this may be refundable when you file your final NJ return. Your CPA handles the final calculation, but the closing attorney handles the withholding. Jorge makes sure the paperwork is done correctly."),
            ("Can you price it to sell in 30 days?", "Usually yes — but at a price that may be 3–5% below 'full market.' Speed and top dollar are a trade-off. Jorge runs both scenarios — list-for-max-price vs list-for-fast-sale — and you decide which matters more given your timeline."),
        ],
        "final_cta_h2": "Let's Get This Sale Done — Remote, Fast, Clean.",
        "final_cta_p": "A free relocation consultation. Walk Jorge through your timeline and corporate package. He runs the numbers and shows you exactly how this closes in 60 days from 800 miles away.",
        "internal_links": [
            ("sell-your-home.html", "Sell Your Home With Jorge"),
            ("home-valuation.html", "Free Home Valuation"),
            ("cash-offer-nj.html", "Cash Offer on Your Home"),
            ("downsizing-nj.html", "Downsizing in NJ"),
            ("why-jorge-ramirez.html", "Why Choose Jorge"),
            ("index.html#contact", "Contact Jorge"),
        ],
    },

    "cash-offer-nj": {
        "breadcrumb_parent": ("Sell Your Home", "sell-your-home.html"),
        "breadcrumb_name": "Cash Offer",
        "title_tag": "Cash Offer on Your NJ Home | Honest Alternative to iBuyers | Jorge Ramirez",
        "meta_title": "Cash Offer on Your NJ Home — Honest Comparison to Opendoor & iBuyers | Jorge Ramirez",
        "meta_desc": "Want a cash offer on your NJ home? Jorge Ramirez gives you an honest cash offer + a market listing comparison so you can see both numbers. Call 908-230-7844.",
        "keywords": "cash offer NJ home, sell house for cash NJ, we buy houses NJ, Opendoor NJ alternative, iBuyer NJ, fast cash sale NJ, cash home buyers New Jersey",
        "llm_context": "Jorge Ramirez (NJ License #1754604) offers NJ homeowners an honest cash-offer service — including a direct cash offer from his investor network AND a realistic market-listing valuation so the seller can see both numbers and choose. Transparent alternative to Opendoor, Offerpad, and 'we buy houses' ads. Contact: 908-230-7844.",
        "hero_h1": "Thinking About a Cash Offer on Your NJ Home? Let's See the Real Numbers First.",
        "hero_p": "Cash-offer companies promise speed. What they do not mention: typical cash offers come in 10–20% below market. Jorge Ramirez shows you BOTH numbers — a real cash offer from his investor network AND what your home would sell for on the open market. Then you decide. No pressure, no contract traps.",
        "pain_h2": "The Truth About Cash-Offer Companies",
        "pain_intro": "Opendoor. Offerpad. We Buy Ugly Houses. Zillow Offers. The ads promise speed and simplicity. What actually happens is often a 10–20% haircut off market value plus hidden fees. Here is what these programs do not advertise.",
        "pain_cards": [
            ("Offers Come in 10-20% Below Market", "iBuyer offers are algorithmically generated to give the buyer room to flip. The 'convenience fee' is usually 5–10%, and the offer itself is typically 5–10% below retail market value. On a $500K home, that is $50K–$100K you leave on the table. Sometimes that is worth it. Often it is not."),
            ("Inspection Credits Destroy the Offer", "The initial offer is a number. After the inspection, iBuyers routinely request $10K–$30K in 'repair credits' for cosmetic issues. The final net is much lower than the original number. Jorge shows you cash offers with transparent inspection terms — no surprise credits at closing."),
            ("You Give Up Negotiation Leverage", "Once you sign an iBuyer agreement, most have exclusivity clauses. You cannot shop the house for 30–90 days. If a better offer shows up, you cannot take it. Jorge's cash-offer process lets you compare the cash offer to the market listing and choose — no exclusivity."),
            ("Fine Print That Bleeds Value", "Service fees. Utility transfer fees. 'Home maintenance' fees. Storage fees. The 4-page service agreement has a dozen line items that compound. Jorge's cash offer has one price. You net what the offer says you net — no fine print."),
            ("You Still Need an Agent Anyway", "Many sellers contact an iBuyer, accept the offer, and then realize they need an agent to help with the next purchase. The iBuyer process does not coordinate your sell/buy timing. Jorge handles both sides — so whether you take the cash offer or the market listing, your next move is already planned."),
        ],
        "mid_cta_h2": "Want a Cash Offer? Fine — But Let's Also See the Market Number.",
        "mid_cta_p": "A free consultation where Jorge presents TWO numbers side by side: a real cash offer from his investor network, and what your home would realistically sell for listed. You pick the one that fits your situation.",
        "why_jorge_h2": "Why Jorge's Cash Offer Is Different",
        "why_jorge_ps": [
            "Jorge is a licensed NJ Realtor — not a cash-offer company. His cash-offer service pairs you with his network of local NJ investors who pay fair prices because they are buying to hold as rentals or flip modestly. The offers are real, the terms are transparent, and there is no long-term exclusivity.",
            "More importantly, Jorge shows you both options. Cash offer AND market listing, both numbers on the same page, both paths explained honestly. Some sellers genuinely need the speed and certainty of cash — Jorge delivers that. Others realize the $50K+ of extra equity from a market listing is worth the extra 45 days — Jorge delivers that too.",
            "Before becoming a full-time Realtor in 2017, Jorge personally flipped 60+ houses. He knows exactly how investors price cash offers, because he used to write them. That insider perspective means his cash-offer clients get genuinely fair numbers — not the lowball specials iBuyers push.",
        ],
        "why_jorge_credentials": [
            "Licensed NJ Realtor (#1754604) — not an iBuyer or wholesaler",
            "60+ personal house flips — knows exactly how investors price cash offers",
            "Network of local NJ investor buyers writing real cash offers in days",
            "Two-number consultation — cash offer AND market listing, both transparent",
            "No long exclusivity — you can always pivot to a market listing if cash is too low",
            "Same-week cash close available when the deal and buyer align",
        ],
        "process_h2": "How the Two-Option Process Works",
        "process_intro": "Instead of giving you one number and hoping you take it, Jorge gives you both paths. Cash speed versus market price. You decide based on real numbers.",
        "process_steps": [
            ("Free Consultation and Home Walkthrough", "Jorge visits the home (or does a virtual walkthrough) and assesses condition, location, and local market. This is a free 30-minute conversation — no sales pitch, no pressure to commit."),
            ("Cash Offer From Investor Network", "Jorge presents the property to his network of vetted NJ investor buyers. Within 3–7 days you receive a real cash offer with transparent terms — net sale price, closing timeline, inspection contingency (if any)."),
            ("Market Listing Estimate", "In parallel, Jorge runs a full <a href=\"home-valuation.html\" style=\"color: white; text-decoration: underline;\">Comparative Market Analysis</a> and presents the realistic listed price, estimated time on market, and net proceeds after commission and closing costs."),
            ("Side-by-Side Comparison", "Both numbers on the same page. Cash offer net vs. market listing net. Cash offer timeline (1–3 weeks) vs. market listing timeline (45–60 days typical). You see the trade-off clearly and choose based on what matters to your situation."),
            ("Execute the Path You Chose", "Take the cash offer? Jorge handles the entire close in 1–3 weeks. Go with the market listing? Jorge handles that exactly like any other full-service listing — MLS, marketing, showings, negotiation, closing. Same agent, whichever path wins."),
        ],
        "ai_h2": "When Cash Is the Right Answer",
        "ai_intro": "Sometimes the cash offer really is the better choice. Jorge helps you identify when, instead of trying to steer you toward the bigger commission.",
        "ai_cards": [
            ("When the Home Needs Major Work", "If the home needs $50K+ in repairs and you do not have the cash or time to do them, a market listing at full retail is not realistic. Cash investor buyers specialize in these situations — they pay a fair as-is price and handle the work themselves."),
            ("When Speed Beats Every Other Factor", "Divorce closing, inherited estate distribution, relocation deadline, medical situation — when the closing date matters more than the last $30K of equity, the cash offer is often the smart play. Jorge will tell you honestly when this is your situation."),
            ("When the Home Does Not Fit Retail Demand", "Unique layouts, oversized or undersized lots, outdated floor plans, or tricky locations can mean long days on market for retail listings. If retail buyers are unlikely to bid competitively, a strong cash offer may actually be close to or even above what a market listing would yield."),
        ],
        "faq_h2": "Cash Offer on Your NJ Home — Answered",
        "faqs": [
            ("Will Jorge's cash offer be higher than Opendoor?", "Usually yes — often meaningfully. Jorge's cash offers come from local investor buyers who know the NJ market deeply and pay fair prices. iBuyer offers are algorithmic and include high service fees. That said, Jorge shows you both numbers — the cash offer AND the market listing — so you can compare honestly instead of guessing."),
            ("How fast can a cash close happen?", "Once you accept the cash offer, close can happen in as little as 7–14 days. The exact timeline depends on title search speed and your preferred move-out date. Jorge can also extend closing to 30–45 days if you need time to find your next place."),
            ("Do I have to accept the cash offer to work with Jorge?", "No. The consultation and the cash offer are free and no-obligation. Many sellers see both numbers, compare, and choose the market listing — Jorge handles that just the same. The goal is giving you honest data, not trapping you into a specific path."),
            ("What are the fees on a cash sale?", "On a cash investor sale, typically zero service fees from the buyer. You still owe standard NJ closing costs (title, attorney, transfer tax), which can be 1.5–2% of the sale price. Jorge's commission on a cash sale is often reduced since the sale cycle is so short — he will quote exact numbers in the consultation."),
            ("Is this the same as 'We Buy Houses' companies?", "No. Those ads are typically run by wholesalers who flip the contract to another investor at a markup — they never actually buy the house. Jorge's cash offers come from end-buyer investors who are actually closing on the house, which means the offer is real and the price is not artificially squeezed by a middleman wholesaler markup."),
            ("What if I like both options and want to try the market first?", "Perfect — that is a common choice. Jorge lists the home at market price with a defined decision point: if there are no strong offers in 21 days, pivot to the cash offer. You get the upside of the market listing without the risk of the home sitting forever, and the cash offer is pre-set as a floor."),
        ],
        "final_cta_h2": "See Both Numbers. Then Decide.",
        "final_cta_p": "A free no-pressure consultation. Jorge presents the cash offer AND the market listing estimate side by side. You pick the one that fits your life.",
        "internal_links": [
            ("sell-your-home.html", "Full Listing Service"),
            ("home-valuation.html", "Free Home Valuation"),
            ("sell-home-fast-nj.html", "Sell Home Fast NJ"),
            ("relocating-from-nj.html", "Relocating From NJ"),
            ("why-jorge-ramirez.html", "Why Choose Jorge"),
            ("index.html#contact", "Contact Jorge"),
        ],
    },

    # ============================ BUYER PAGES ============================
    "buyer-agency-agreement-nj": {
        "breadcrumb_parent": ("Buy a Home", "buy-a-home.html"),
        "breadcrumb_name": "Buyer Agency Agreement NJ",
        "title_tag": "Buyer Agency Agreement NJ 2026 | Who Pays & How It Works | Jorge Ramirez",
        "meta_title": "Buyer Agency Agreement NJ 2026 — Who Pays After the NAR Settlement | Jorge Ramirez",
        "meta_desc": "Confused about buyer agent fees in NJ after the 2024 NAR settlement? Jorge Ramirez explains exactly how buyer agency works in 2026, who pays, and what to expect. Call 908-230-7844.",
        "keywords": "buyer agency agreement NJ, who pays buyer agent NJ 2026, NAR settlement NJ, buyer agent commission NJ, exclusive buyer agent NJ, buyer broker agreement New Jersey",
        "llm_context": "Jorge Ramirez (NJ License #1754604) is a licensed New Jersey real estate agent who represents home buyers. Since the August 2024 NAR settlement, all NJ buyers must sign a written buyer agency agreement before touring homes, and buyer agent compensation is negotiated between buyer and agent. Jorge explains the agreement, compensation options, and buyer representation transparently. Contact: 908-230-7844.",
        "hero_h1": "Buyer Agency Agreements in NJ: How It Actually Works in 2026.",
        "hero_p": "In August 2024, the NAR settlement changed how buyer agents get paid. In 2026, every NJ buyer has to sign a written buyer agency agreement before touring a home — and buyer agent commission is no longer automatically baked into the seller's side. Jorge Ramirez explains exactly how this works, who pays, and what you are signing, in plain English.",
        "pain_h2": "What Changed and What Buyers Need to Know",
        "pain_intro": "The old system: sellers paid both agents, buyers rarely saw a signed agreement, and nobody talked about commission. The new system: buyers and their agents sign a written agreement upfront that spells out compensation. Most agents are bad at explaining this. Here is what you actually need to know.",
        "pain_cards": [
            ("You Must Sign an Agreement Before Touring", "Since August 2024, a licensed NJ agent cannot take you to see a home until you have signed a written buyer agency agreement. This is federal settlement policy, not optional. If an agent is showing you homes without an agreement, they are breaking the rules — and you are not protected. Jorge explains the agreement before the first showing, every time."),
            ("Commission Is Negotiated — Not Standard", "The old 'standard' 2.5–3% buyer agent commission is gone. Every agreement now negotiates compensation explicitly between buyer and agent. It could be a flat fee, a percentage, an hourly rate, or a combination. Jorge presents multiple options and lets you pick what makes sense for your purchase."),
            ("Who Pays Depends on the Deal", "Sellers can still offer buyer agent compensation — and in NJ, most still do — but it is no longer guaranteed. If the seller does not cover the buyer agent fee, the buyer does. That compensation can often be negotiated into the purchase offer so it does not come out of your pocket at closing. Jorge runs the math on every offer."),
            ("The Agreement Is Legally Binding", "Once you sign, you are in a contractual relationship with that agent for the properties and timeframe specified in the agreement. Signing multiple agreements with multiple agents for the same property creates legal mess. Jorge uses short-term, property-specific agreements so buyers are not locked in long-term."),
            ("Dual Agency Rules Changed Too", "In NJ, a dual agency situation (same agent representing both buyer and seller) requires written consent from both parties. Jorge will never pressure you into dual agency — and will refer you to another agent if a property he is listing is the one you want, to avoid conflict."),
        ],
        "mid_cta_h2": "Confused About How This Works? Let's Walk Through It.",
        "mid_cta_p": "A free, no-pressure conversation to review the buyer agency agreement, compensation options, and how the 2024 settlement changes the process. You leave knowing exactly what you are signing before you ever tour a home.",
        "why_jorge_h2": "How Jorge Handles Buyer Representation Post-Settlement",
        "why_jorge_ps": [
            "The NAR settlement is not scary — it actually makes buyer representation more transparent. Jorge has updated his buyer agreement to be short, plain-English, and property-specific so buyers understand exactly what they are signing before they sign.",
            "Jorge presents three compensation options upfront: seller-paid (most common, still), buyer-paid with offer credit (seller refunds at closing), or flat-fee representation. You pick what works. The final structure always gets locked into writing before any showing.",
            "Before becoming a full-time Realtor in 2017, Jorge personally bought and sold 60+ houses. He has been on both sides of this exact conversation and can explain the commission mechanics, the offer structure, and the closing math in ways that make sense — not in agent-speak.",
        ],
        "why_jorge_credentials": [
            "Short-term, property-specific buyer agreements — no long lock-ins",
            "Three compensation options explained transparently before signing",
            "Offers structured to have seller cover buyer agent fee when possible",
            "Plain-English explanation of every clause in the agreement",
            "Dual-agency conflict handling — referral to another agent when needed",
            "Full buyer representation through offer, inspection, appraisal, closing",
        ],
        "process_h2": "How Buyer Representation Actually Runs in 2026",
        "process_intro": "Here is the exact sequence of events, from first conversation to keys in hand — including where the agreement gets signed and how compensation gets handled.",
        "process_steps": [
            ("Free Intro Call", "A 30-minute conversation about your home search, financing, timeline, and locations. No agreement yet, no pressure. Jorge listens first, then explains how the agreement and compensation work if you want to move forward."),
            ("Review and Sign the Buyer Agreement", "If you want to tour homes with Jorge, a short buyer agreement gets signed — specifying the properties, timeframe, and compensation structure. Jorge reviews every clause with you. Short-term (typically 30–90 days) and specific properties."),
            ("Tour and Evaluate Homes", "Jorge shows you homes that match your criteria, provides market intelligence on each, and pre-qualifies the comps so you know what to offer. Full buyer representation — your interests only."),
            ("Write and Negotiate the Offer", "When you find the right home, Jorge structures the offer. If the seller is offering buyer agent compensation (most are, in 2026 NJ), it flows through the listing. If not, the offer can include a credit to cover buyer agent compensation at closing — Jorge runs the math so you see net cost clearly."),
            ("Close and Celebrate", "Attorney review, inspection, appraisal, mortgage underwriting, and closing — all coordinated by Jorge. You walk out with keys. All compensation is disclosed and finalized at closing per the signed agreement."),
        ],
        "ai_h2": "Why Buyer Representation Still Matters",
        "ai_intro": "Some buyers wonder if they should skip the buyer agent in the new model. The math almost always says no — a good buyer agent saves more in negotiation and process navigation than their compensation costs.",
        "ai_cards": [
            ("Negotiation Leverage You Cannot Buy", "Buyers who negotiate solo often pay $5K–$25K more on the same home than buyers represented by an experienced agent. The listing agent works for the seller. Without your own representation, you are at a structural disadvantage at the table."),
            ("Inspection and Repair Credit Navigation", "The post-inspection negotiation is where most buyers leave money on the table. Jorge has run this negotiation hundreds of times and knows exactly which repairs sellers typically credit vs. refuse. Routinely saves buyers $5K–$15K at this stage alone."),
            ("Financing, Appraisal, and Contract Minefields", "NJ real estate contracts are full of specific language around contingencies, timelines, and protections. Missing a deadline or misreading a clause can cost buyers their earnest money deposit or kill the deal. Jorge's job is to make sure none of that happens to you."),
        ],
        "faq_h2": "Buyer Agency Agreement NJ — Your Questions",
        "faqs": [
            ("Do I really have to sign an agreement before seeing homes?", "Yes. Since August 2024, NJ (and federal) rules require a written buyer agency agreement before a licensed agent shows you a home. This protects you as well as the agent — without the agreement, you have no written representation or fiduciary duty. Jorge uses a short, property-specific agreement so you are not committed long-term."),
            ("Can I sign with more than one agent at once?", "Technically yes, but it creates legal problems. Signing exclusive agreements with multiple agents for the same property can trigger commission disputes and liability issues. Better approach: interview agents first, pick the one you trust, then sign a short-term agreement with that one."),
            ("Who actually pays the buyer agent?", "In 2026 NJ, most sellers still offer buyer agent compensation as part of their listing — so the seller effectively pays (out of sale proceeds). When a seller does NOT offer buyer agent compensation, the buyer can cover it directly, OR the purchase offer can include a seller credit that covers the buyer agent fee. Jorge structures offers to minimize out-of-pocket compensation whenever possible."),
            ("What if I find a home directly on Zillow and don't need an agent?", "Legally, you can buy without a buyer agent. Practically, you would be negotiating against the seller's agent who has a fiduciary duty to the seller. In NJ, most buyers save more through agent-led negotiation and inspection navigation than they would save on commission. But the choice is yours — Jorge will discuss that math honestly in the free consultation."),
            ("How much does a buyer agent cost in 2026?", "Compensation is negotiated in the agreement — not standardized anymore. Common structures: 2–2.5% of purchase price (similar to pre-settlement), flat fees for lower-cost homes, or hourly rates for limited-scope representation. Jorge presents the options and recommends what makes sense for your specific purchase."),
            ("What if I don't buy anything in the timeframe of the agreement?", "The agreement simply expires. No fee is owed if no purchase happens. Jorge's buyer agreements are property-specific and typically last 30–90 days — short enough that you are not trapped, long enough to actually run a real search."),
        ],
        "final_cta_h2": "Ready to Buy a Home in NJ? Let's Start With the Real Conversation.",
        "final_cta_p": "A free consultation — review the agreement, talk compensation options, and map out your home search. No pressure, no sign-now, no generic agent speak.",
        "internal_links": [
            ("buy-a-home.html", "Buy a Home in NJ"),
            ("nj-home-buyer-guide.html", "NJ Home Buyer Guide"),
            ("nyc-to-nj-relocation.html", "Moving From NYC to NJ"),
            ("luxury-homes-nj.html", "Luxury Home Buyers"),
            ("why-jorge-ramirez.html", "Why Choose Jorge"),
            ("index.html#contact", "Contact Jorge"),
        ],
    },

    "nyc-to-nj-relocation": {
        "breadcrumb_parent": ("Buy a Home", "buy-a-home.html"),
        "breadcrumb_name": "Moving From NYC to NJ",
        "title_tag": "Moving From NYC to NJ in 2026 | Commuter & Buyer Guide | Jorge Ramirez",
        "meta_title": "Moving From NYC to NJ 2026 — Commuter Towns, Taxes, Homes | Jorge Ramirez",
        "meta_desc": "Moving from NYC to NJ? Jorge Ramirez maps out commuter towns, property tax math, school districts, and buyer representation for NYC transplants. Call 908-230-7844.",
        "keywords": "moving from NYC to NJ, NYC to New Jersey relocation, best NJ commuter towns from NYC, buying first house NJ from NYC, Manhattan to NJ move, NYC transplant NJ homes",
        "llm_context": "Jorge Ramirez (NJ License #1754604) specializes in helping NYC residents relocate to New Jersey suburbs. He advises on commuter towns (Summit, Westfield, Chatham, Montclair, Maplewood, Hoboken, Jersey City), commute math (NJ Transit Midtown Direct, PATH, ferry), property tax reality, and the apartment-to-house transition. Contact: 908-230-7844.",
        "hero_h1": "Moving From NYC to New Jersey? Here's How to Pick the Right Town — Without Regrets.",
        "hero_p": "The apartment feels small. The kid is on the way (or already here). You love NYC but you need yard, space, and a school district. Jorge Ramirez has helped hundreds of NYC residents make the jump — picking the right commuter town, decoding NJ property taxes, and finding the house that actually fits. Call 908-230-7844.",
        "pain_h2": "Where NYC Transplants Make Expensive Mistakes",
        "pain_intro": "Moving from NYC to NJ is not the same as moving between NJ towns. The commute calculus, school search, tax math, and neighborhood culture all look different from what you are used to. Here is where NYC buyers most commonly get burned.",
        "pain_cards": [
            ("Buying in the Wrong Commuter Town", "'Commutable to NYC' covers everywhere from a 22-minute Summit direct train to a 90-minute transfer-heavy ride from Bridgewater. Some towns have Midtown Direct. Some do not. Some have ferry service. Jorge maps out your exact door-to-office commute for every town you are considering — not the fantasy version."),
            ("Underestimating NJ Property Taxes", "A $1.2M house in Summit can come with $22K+ a year in property taxes — which is common knowledge to locals but a shock to NYC buyers. Jorge shows you the all-in monthly cost (mortgage + tax + insurance) for every property, so you are never surprised at closing. Some NJ towns have half the tax rate of others — this matters."),
            ("Picking a School District Blindfolded", "NYC school reputation does not transfer to NJ. Montclair, Maplewood, Summit, Westfield, Chatham, and Millburn/Short Hills all have strong public schools — with very different cultures and demographics. Jorge matches buyers to the town that fits their family style, not just the GreatSchools rating."),
            ("Skipping the Apartment-to-House Reality Check", "Driving everywhere. Managing a lawn. Shoveling in winter. Commuting 45 minutes each way. Paying for things supers used to handle. NYC apartment life and NJ suburban life are different operating systems. Jorge has the honest conversation about what changes before you buy — not after."),
            ("Missing NYC Exit Tax and Selling Timing", "If you sell a NYC apartment, NY state and city taxes apply. If you are renting in NYC, the savings on NYC income tax after the move are significant (NJ does not have NYC's local income tax, though it has its own). Jorge works with buyers' CPAs to think through the tax year timing of the move."),
        ],
        "mid_cta_h2": "Ready to Make the Move? Let's Map It Out.",
        "mid_cta_p": "A free NYC-to-NJ consultation. Jorge walks through your commute requirements, school priorities, budget, and timeline — then shows you the three towns that actually fit, not twelve random options.",
        "why_jorge_h2": "Why NYC Buyers Work With Jorge",
        "why_jorge_ps": [
            "Jorge has helped hundreds of NYC residents relocate to NJ suburbs since 2017. The pattern repeats: NYC buyers first focus on the wrong things (often GreatSchools rankings and square footage), and without guidance end up buying in a town that looks right on paper but does not fit their actual life.",
            "Jorge's first conversation with NYC buyers is almost never about specific listings. It is about the commute, the school priorities, the weekend lifestyle, and the honest budget. From there, the town recommendations become obvious — and the house search moves faster because the target zone is tight.",
            "Jorge also coordinates with NYC-based attorneys, mortgage brokers who handle NJ lending, and movers who do the NYC-to-NJ route regularly. The move logistics are complicated — the real estate transaction should not be.",
        ],
        "why_jorge_credentials": [
            "Hundreds of NYC-to-NJ relocations handled since 2017",
            "Commute math for Midtown Direct, PATH, and ferry routes — door to door",
            "Honest school district guidance — culture fit, not just test scores",
            "All-in monthly cost (mortgage + tax + insurance) on every property",
            "Coordination with NYC attorneys, NJ mortgage brokers, and cross-state movers",
            "Weekend and evening availability for NYC-schedule house hunters",
        ],
        "process_h2": "The NYC-to-NJ Path, Mapped",
        "process_intro": "Most NYC buyers over-complicate the search by looking at 20 towns. The right approach is to narrow to 2–3 based on commute and lifestyle first, then search within those. Here is how Jorge runs it.",
        "process_steps": [
            ("Free NYC-to-NJ Consultation", "Phone or Zoom, 45–60 minutes. Commute requirements, budget, school priorities, family situation, lifestyle preferences. By the end, Jorge narrows the list from 12 possible towns to 2–3 that actually fit."),
            ("Town Tour Day", "Jorge spends a Saturday driving you through the 2–3 target towns. Downtown walk, quick coffee in each, drive-by of representative neighborhoods, and commute-start locations. You eliminate one or two by lunch."),
            ("Home Search Inside the Target Town", "Now the search is narrow and fast. Jorge runs a curated daily feed of matching homes, accompanies you to every showing, and filters out the ones with commute, tax, or construction issues you would not spot."),
            ("Offer and Closing Coordination", "When you find the one, Jorge handles the offer strategy (bidding wars are common in top NJ commuter towns), negotiation, inspection, and attorney review. NYC-to-NJ closings can happen fully remote — no extra trips required."),
            ("Move-In and Settle", "Jorge connects you with NYC-to-NJ movers, utility setup, and town orientation. The first 30 days of suburban life have their own learning curve — Jorge answers the questions nobody warns you about."),
        ],
        "ai_h2": "The Commute Math NYC Buyers Miss",
        "ai_intro": "Every NYC buyer thinks they know the commute until they actually do it. Here is the real story on the three main routes — and how Jorge helps you sanity-check the one you are considering.",
        "ai_cards": [
            ("Midtown Direct Train Towns", "Summit, Chatham, Madison, Millburn, South Orange, Maplewood, Montclair (Bay Street, Watchung). Direct to Penn Station, 25–45 minutes. Premium suburban commute — and premium home prices to match. Jorge has the real numbers on every line."),
            ("PATH Train and Light Rail (Hudson County)", "Hoboken, Jersey City. PATH to lower Manhattan in 10–15 minutes. Condo-heavy market with rapidly rising single-family prices. Best for buyers who want shorter commute and urban-adjacent feel."),
            ("NY Waterway Ferry Towns", "Edgewater, Weehawken, Port Imperial. Ferry to Midtown/Downtown, 8–15 minutes. Luxury high-rise market. Great commute but very different lifestyle from traditional NJ suburbs."),
        ],
        "faq_h2": "NYC to NJ — Questions Every Transplant Asks",
        "faqs": [
            ("What's the real difference between Summit, Westfield, Chatham, and Montclair?", "All four have top public schools, Midtown Direct train, walkable downtowns, and similar price bands — but very different cultures. Summit is tight-knit, corporate, walk-to-train small. Westfield is larger, suburban, more kid-focused. Chatham is smaller, quieter, more traditional. Montclair is artistic, diverse, more urban energy. Jorge walks through the cultural fit, not just the specs."),
            ("How much should I expect to pay in NJ property taxes?", "Depends heavily on the town. NJ property tax rates range from ~1.5% (e.g., Hoboken) to ~3%+ (e.g., some parts of Essex County). On a $1M home, that is a $15K–$30K+ annual tax bill. Jorge shows you the all-in monthly cost for every property so there are no surprises."),
            ("What's the best commuter town from NYC?", "For shortest commute: Hoboken or Jersey City (PATH, 10–15 min). For suburban lifestyle: Summit, Chatham, or Maplewood (Midtown Direct, 25–45 min). For best value: further-out towns like Westfield or Montclair give you larger homes but slightly longer commutes. The 'best' town depends on your priority — Jorge matches buyer to town based on the actual weekly routine."),
            ("How long does it take to buy a house in NJ from NYC?", "Once you start seriously looking: 6–12 weeks to find the right home and get under contract. 45–60 days from signed contract to closing. Total NYC-to-NJ relocation timeline: 4–6 months from first call to move-in day, if you want to do it without rushing."),
            ("Can I still work in NYC and live in NJ?", "Yes — most NJ commuter town residents work in NYC and pay NJ state income tax plus NYC (nonresident) income tax. NJ gives you a credit for NYC tax paid, so you are not double-taxed. Your CPA handles the filing. Net impact: often lower than living in NYC with city + state + high rent."),
            ("What about schools if my kid isn't in school yet?", "Buy for the long haul. Many NYC transplants buy for pre-K/kindergarten and the school district becomes critical for the next 15 years. Jorge shows you the K–12 strength of every town, not just elementary schools. Also — NJ school enrollment is typically by address, so you commit to the town's schools when you buy."),
        ],
        "final_cta_h2": "Ready for the Suburbs? Let's Do This Right.",
        "final_cta_p": "A free 60-minute consultation. Commute, schools, budget, lifestyle — and three towns that actually fit. No pressure, no listings yet. Just the real conversation first.",
        "internal_links": [
            ("buy-a-home.html", "Buy a Home in NJ"),
            ("nj-home-buyer-guide.html", "First-Time Buyer Guide"),
            ("buyer-agency-agreement-nj.html", "Buyer Agency Explained"),
            ("tools/mortgage-calculator.html", "Mortgage Calculator"),
            ("closing-costs-calculator.html", "Closing Costs Calculator"),
            ("index.html#contact", "Contact Jorge"),
        ],
    },

    "investment-property-nj": {
        "breadcrumb_parent": ("Buy a Home", "buy-a-home.html"),
        "breadcrumb_name": "Investment Property NJ",
        "title_tag": "Buying Investment Property NJ | Flip & Rental Agent | Jorge Ramirez",
        "meta_title": "Buying an Investment Property in NJ — Flip & Rental Realtor | Jorge Ramirez",
        "meta_desc": "Looking for a flip or rental in NJ? Jorge Ramirez has 60+ personal flips and works with investor buyers every week. Deal flow, cap rate analysis, honest numbers. Call 908-230-7844.",
        "keywords": "investment property NJ, flip NJ homes, rental property NJ, BRRRR NJ, buy and hold NJ, NJ investor realtor, house flipping NJ, cap rate New Jersey",
        "llm_context": "Jorge Ramirez (NJ License #1754604) is a New Jersey real estate agent and investor with 60+ personal house flips. He helps investor buyers — flippers, rental buyers, BRRRR strategies — source properties, analyze cap rates, and close cash deals in NJ. Contact: 908-230-7844.",
        "hero_h1": "Buying an Investment Property in NJ? Work With an Agent Who Actually Invests.",
        "hero_p": "Most agents do not know how to run a rental pro forma. Most agents have never walked a flip. Jorge Ramirez has flipped 60+ houses personally in NJ, built his own rental portfolio, and works with investor buyers every week. He sees deals before they hit MLS and can tell you in 10 minutes whether the numbers work. Call 908-230-7844.",
        "pain_h2": "Where Investor Buyers Get Burned",
        "pain_intro": "Buying investment real estate is not the same game as buying a primary residence. The metrics, the contingencies, the due diligence, and the negotiation all work differently. Here is where investor buyers lose money working with retail-only agents.",
        "pain_cards": [
            ("Agents Who Cannot Analyze a Deal", "You send a listing to your agent and ask 'does this work as a rental?' Three days later, they come back with a comparison of recent sales. You asked for cash-on-cash return — they sent you CMA data. Jorge speaks the metrics: cap rate, gross rent multiplier, DSCR, cash-on-cash, IRR. Conversations move fast."),
            ("No Off-Market Deal Flow", "The best flips and rentals are not on Zillow. They are at foreclosure auctions, through local wholesaler networks, from tired landlord tips, and from other investors trading portfolios. Retail-only agents do not have that pipeline. Jorge has a constant flow of off-market NJ opportunities — you get them before the general MLS sees them."),
            ("Missing Comp Adjustments for Investor Math", "Retail buyers pay on emotion. Investor buyers pay on math. The same house has two different valuations depending on who is buying. Jorge knows when to recommend an aggressive offer (because retail demand is high) vs. a disciplined one (because the flip margin is tight)."),
            ("Blowing the ARV on a Flip", "After-repair value is where flippers make or lose money. Overestimating ARV by 5% can eat the entire profit. Jorge has personally flipped 60+ houses in NJ — he can walk a potential flip and tell you the realistic ARV, the construction budget, and the likely 90-day turn-around."),
            ("Ignoring Local NJ Quirks", "NJ has specific rules that trip up out-of-state investors: high transfer taxes on luxury properties, attorney review requirements, flood zone issues in certain coastal and river areas, lead paint disclosures, and rent control in some municipalities. Jorge flags these on day one so you do not discover them at closing."),
        ],
        "mid_cta_h2": "Looking for Deal Flow? Let's Run Some Numbers.",
        "mid_cta_p": "A free call with Jorge. Share your buy box — target ARV, target cap rate, cash deployment, NJ regions of interest — and Jorge maps you into his existing deal pipeline. No commitments.",
        "why_jorge_h2": "Why Investors Choose Jorge",
        "why_jorge_ps": [
            "Jorge is not a retail agent dabbling in investment real estate. Before becoming a full-time Realtor in 2017, he personally bought, renovated, and sold 60+ homes in NJ as an investor. He built his own rental portfolio. He has written cash offers, managed construction crews, and dealt with bad tenants. When an investor calls Jorge, the first conversation is a peer conversation.",
            "That operator experience matters in four places. First, deal sourcing — Jorge has the investor network that surfaces off-market deals. Second, underwriting — Jorge runs the real pro forma, including realistic maintenance reserves, vacancy, and management. Third, negotiation — Jorge knows which sellers will take cash discounts and which will not. Fourth, execution — Jorge has contractors, lenders, and property managers ready to recommend.",
            "Jorge is also comfortable with the common investor strategies: flipping, BRRRR, buy-and-hold, short-term rental (where allowed in NJ), and 1031 exchanges. He adapts his recommendations to your strategy — not a one-size-fits-all.",
        ],
        "why_jorge_credentials": [
            "60+ personal house flips in NJ — real operator experience",
            "Own rental portfolio — speaks the buy-and-hold language fluently",
            "Off-market deal pipeline via investor network and wholesaler relationships",
            "Pro forma analysis: cap rate, cash-on-cash, IRR, ARV, BRRRR refinance math",
            "Contractor and property manager referrals tested in live deals",
            "1031 exchange coordination with qualified intermediaries",
        ],
        "process_h2": "How an Investor Buy Runs With Jorge",
        "process_intro": "Every investor has a different strategy. Here is the standard framework Jorge uses to match your criteria to real deals — and move fast when the right one surfaces.",
        "process_steps": [
            ("Free Strategy Call — Define Your Buy Box", "Cash deployment, target geography, target metrics (cap rate, cash-on-cash, ARV spread for flips), financing (cash, DSCR, conventional), timeline, and experience level. Jorge builds the search criteria in 45 minutes."),
            ("Daily Deal Flow Delivered", "Both MLS and off-market deals matching your buy box get sent to you as they surface. Includes Jorge's first-pass underwriting — estimated ARV (for flips), cap rate (for rentals), and a yes/maybe/no recommendation."),
            ("Fast Walk-Throughs and Decisive Offers", "On deals that pass the desk screen, Jorge walks the property with you (or does a video walkthrough). Offer written the same day if the numbers work. Investors who move slow lose the best deals — Jorge keeps the pace tight."),
            ("Negotiation and Contingency Strategy", "Aggressive offers with minimal contingencies when the market is right, and careful attention to inspection/appraisal terms when the deal needs protection. Jorge knows which NJ sellers accept as-is cash with 7-day close vs which ones need more standard terms."),
            ("Closing, Contractor Handoff, Property Manager Onboarding", "At closing, Jorge hands you off to the right contractor (if it is a flip) or property manager (if it is a rental). Deal closes, crew starts, cash flow begins — in weeks, not months."),
        ],
        "ai_h2": "Markets Jorge Covers for Investors",
        "ai_intro": "NJ is not one market — it is dozens of micro-markets with different rent, different tenant pools, and different flip economics. Here is where Jorge's investor clients have had the most success.",
        "ai_cards": [
            ("Flip-Friendly Essex & Union County Towns", "Parts of Irvington, Orange, Union, Rahway, and Linden still have distressed inventory with real flip margin. Jorge knows which sub-markets support $400K–$600K ARV and which ones cap at $325K — knowing the cap is what keeps flippers profitable."),
            ("Strong Rental Markets — Hudson and Middlesex", "Jersey City, Bayonne, New Brunswick, and Perth Amboy offer different cap rates for different risk profiles. Jorge analyzes rent comps by building type (2-family, 3-family, mixed-use) and can tell you where rents are trending."),
            ("Commuter-Town Luxury Flips", "$1M+ flips in Summit, Westfield, Chatham, and Millburn require different construction standards, design choices, and staging. Jorge has flipped in these towns personally and knows what the $1M–$2M buyer actually wants."),
        ],
        "faq_h2": "Investment Property NJ — Investor Questions",
        "faqs": [
            ("Do you really see off-market deals?", "Yes. Between Jorge's own investor network, relationships with local wholesalers, tips from prior sellers, and pocket listings from other agents, there is a steady flow of off-market opportunities. Not every deal that comes to Jorge is a good deal — but the pipeline is constant. Tell Jorge your buy box and he will feed you matching deals."),
            ("What cap rates are realistic in NJ right now?", "Depends heavily on location and property type. Strong cash-flow markets (parts of Hudson, Middlesex, Essex) still support 6–8% cap on well-priced 2–3 family buildings. Premium markets (Summit, Westfield, Chatham) typically cap at 3–5% — those are appreciation plays, not cash flow plays. Jorge is honest about which strategy fits which market."),
            ("Can you work with me if I'm buying with a DSCR loan?", "Yes. Jorge coordinates regularly with DSCR lenders and knows how DSCR requirements shape offer structure (fewer contingencies, slightly longer closings, specific appraisal and rental comp requirements). He can also refer you to DSCR lenders he trusts if you do not have one yet."),
            ("Do you help with contractors and property management?", "Yes — Jorge maintains a list of contractors and property managers he has used personally. The referrals are based on real work, not kickbacks. If a contractor or PM disappoints, Jorge wants to know — his reputation is attached to the referral."),
            ("Can I do a 1031 exchange through your deals?", "Absolutely. Jorge has coordinated many 1031 exchanges — both on the sell side and the buy side. Key is the 45-day identification window and the 180-day close window. Jorge works with your qualified intermediary from day one."),
            ("What about short-term rentals (Airbnb) in NJ?", "Be careful — many NJ municipalities have short-term rental restrictions or outright bans. Jersey City is heavily regulated, many Jersey Shore towns have specific rules, and some suburbs prohibit STRs entirely. Jorge confirms municipal rules before you buy. In some markets, STR income can be strong; in others, it is a legal liability."),
        ],
        "final_cta_h2": "Ready to Add a Deal? Let's Build Your Pipeline.",
        "final_cta_p": "A free call to define your buy box and plug into Jorge's daily deal flow. No commitments, no pressure. Just a conversation between operators.",
        "internal_links": [
            ("buy-a-home.html", "Buy a Home in NJ"),
            ("sell-rental-property-nj.html", "Selling Your Rental"),
            ("home-valuation.html", "Free Home Valuation"),
            ("why-jorge-ramirez.html", "Why Choose Jorge"),
            ("cash-offer-nj.html", "Cash Offer Option"),
            ("index.html#contact", "Contact Jorge"),
        ],
    },

    "luxury-homes-nj": {
        "breadcrumb_parent": ("Buy a Home", "buy-a-home.html"),
        "breadcrumb_name": "Luxury Homes NJ",
        "title_tag": "Luxury Homes in NJ $1M+ | Discreet Buyer & Seller Service | Jorge Ramirez",
        "meta_title": "Luxury Homes in NJ $1M+ — Discreet Representation | Jorge Ramirez",
        "meta_desc": "Buying or selling a luxury home in NJ $1M+? Jorge Ramirez delivers discreet representation, off-market access, and global buyer reach. Call 908-230-7844.",
        "keywords": "luxury homes NJ, $1M homes NJ, luxury realtor NJ, high end homes New Jersey, Short Hills luxury, Summit luxury, Chatham luxury homes, NJ luxury real estate agent",
        "llm_context": "Jorge Ramirez (NJ License #1754604) represents luxury home buyers and sellers in New Jersey — primarily $1M-$5M+ homes in Summit, Westfield, Chatham, Millburn/Short Hills, Montclair, and surrounding premium towns. Focus on discretion, off-market access, global buyer reach via Keller Williams Premier Properties network. Contact: 908-230-7844.",
        "hero_h1": "Luxury Homes in New Jersey: Discreet Representation From $1M to $10M+.",
        "hero_p": "Buying or selling a luxury home is not the same transaction as a median-price home. The buyer pool is smaller, the marketing is more discreet, the negotiations are more nuanced, and the stakes are higher. Jorge Ramirez handles luxury representation with the privacy, global reach, and professional polish the space requires. Call 908-230-7844.",
        "pain_h2": "What Luxury Buyers and Sellers Actually Need",
        "pain_intro": "Agents who sell median-price homes can be excellent at what they do — and still be wrong for a $2M luxury transaction. The needs are different. Here is what luxury clients consistently flag as the gaps they have experienced with previous agents.",
        "pain_cards": [
            ("Privacy and Discretion Standards", "Celebrity clients, professional athletes, executives, and high-net-worth families need the transaction to stay quiet. That means NDAs on request, controlled access to showings, listings kept off the public MLS when appropriate, and no social media posts mentioning the property. Jorge operates at this discretion standard by default."),
            ("Off-Market and Pocket Listing Access", "Many luxury homes never hit the public market. They move through private networks, agent-to-agent whispers, and pocket listings. Without access to that flow, luxury buyers see only 40% of what is actually available. Jorge's network includes top listing agents in every premium NJ town."),
            ("Global Buyer Reach for Luxury Sellers", "The buyer for a $3M Short Hills home might be in Manhattan — or Singapore. Luxury sellers need marketing that reaches international qualified buyers, not just local Zillow traffic. Jorge's listings get distributed through Keller Williams Premier Properties' luxury network and international channels."),
            ("Legal and Financial Complexity", "Trusts, LLCs, 1031 exchanges, foreign buyer FIRPTA requirements, prenuptial implications, estate planning considerations. Luxury transactions often involve multiple attorneys and tax advisors. Jorge coordinates all these parties so the sale does not stall in the legal weeds."),
            ("Pricing in a Thin Market", "Luxury homes have fewer comps, unique features, and wider pricing bands. Pricing a $2.5M home is not a math problem — it is a judgment call informed by strategy. Jorge pairs data (recent sales, inventory, absorption rates) with luxury-specific market intelligence to land on pricing that invites qualified bids without giving the home away."),
        ],
        "mid_cta_h2": "Buying or Selling Luxury in NJ? Let's Start With a Private Conversation.",
        "mid_cta_p": "A confidential consultation — your home, your situation, your goals. Jorge outlines the marketing plan, pricing strategy, and timeline. Everything is private unless you say otherwise.",
        "why_jorge_h2": "How Jorge Handles Luxury Differently",
        "why_jorge_ps": [
            "Jorge represents luxury clients in the $1M–$10M+ range across Summit, Westfield, Chatham, Millburn/Short Hills, Madison, Montclair, and premium pockets of Morris, Middlesex, and Hudson counties. Every engagement begins with understanding what the client needs beyond the sale price — privacy, speed, global reach, or quiet off-market execution.",
            "Jorge is with Keller Williams Premier Properties — which means access to the KW Luxury network, national luxury distribution, and international marketing channels. A $3M home listed with Jorge is not marketed like a $500K home. The photography, video, staging, copy, and distribution all match the price point.",
            "Before becoming a full-time Realtor in 2017, Jorge personally flipped 60+ homes — including many in the premium NJ markets. He knows luxury construction standards, knows what the $1M–$5M buyer scrutinizes, and can coach sellers on the highest-ROI pre-listing investments. That operator perspective shows up in every luxury engagement.",
        ],
        "why_jorge_credentials": [
            "$1M–$10M+ NJ representation across Summit, Westfield, Chatham, Short Hills, Madison",
            "Keller Williams Luxury Network — national and international distribution",
            "Private showings, NDA handling, controlled access standards",
            "Off-market and pocket listing access via Jorge's top-agent network",
            "Coordination with trusts, LLCs, foreign buyers, and multi-attorney transactions",
            "Cinematic listing photography and video at luxury price points",
        ],
        "process_h2": "Luxury Representation, Step by Step",
        "process_intro": "Luxury transactions take more time at the front end — strategy, marketing prep, and positioning — to deliver faster, cleaner closings. Here is the framework Jorge uses.",
        "process_steps": [
            ("Private Discovery Meeting", "In-home or by Zoom, confidential. Jorge understands the goals (sale price, timeline, privacy needs, moving destination) before any strategy is proposed. NDA signed if requested."),
            ("Luxury-Grade Pricing Strategy", "A full CMA plus luxury-specific inputs: inventory absorption, time-on-market for comparable luxury listings, unique-property premiums, and current buyer velocity at the price point. Pricing strategy includes initial ask, re-price triggers, and negotiation floor."),
            ("Cinematic Marketing Build", "Professional drone video, twilight exterior photography, magazine-style listing copy, 3D virtual tour, architect-grade floor plans. The listing package is ready before the home goes live — so first impressions are perfect."),
            ("Global and Private Distribution", "Public MLS (if the client chooses), Keller Williams Luxury Network, luxury-specific platforms, international distribution, and Jorge's private buyer network. The mix depends on the discretion level the client wants."),
            ("Negotiation and Clean Close", "Jorge handles offer comparison, counter-offer strategy, and multi-offer orchestration (when the market allows). Once under contract, he coordinates every attorney, tax advisor, and lender through closing. Proceeds flow clean."),
        ],
        "ai_h2": "NJ Luxury Markets Jorge Covers",
        "ai_intro": "Luxury real estate in NJ is concentrated in specific towns — each with its own buyer culture, price dynamics, and inventory rhythms. Here are the markets where Jorge's luxury business is most active.",
        "ai_cards": [
            ("Short Hills & Millburn ($1.5M–$8M+)", "Deep luxury market, top-tier Millburn schools, Midtown Direct to NYC. Buyers are NYC executives, finance, and tech professionals. Inventory is tight — off-market deals are common."),
            ("Summit & Chatham ($1M–$5M+)", "Walkable downtowns, Midtown Direct, excellent schools. Attracts NYC commuters and families moving up from starter homes. Jorge's home office is Summit — deep local market knowledge."),
            ("Montclair, Westfield, Madison ($1M–$4M+)", "Three distinct luxury cultures. Montclair: artistic, urban, diverse. Westfield: traditional suburban luxury, large lots. Madison: small-town luxury with strong schools and a pedestrian downtown."),
        ],
        "faq_h2": "Luxury NJ Real Estate — Your Questions",
        "faqs": [
            ("Can you keep my listing off the public MLS?", "Yes, if that is what you want. Jorge handles pocket listings, private listing networks, and off-market marketing regularly. Some luxury sellers prefer full public marketing for maximum buyer reach; others prefer quiet, private showings only. Either approach is fine — you decide."),
            ("What's the marketing budget for a $3M listing?", "Materially different from a median-price listing. Expect professional drone video, twilight photography, magazine-style print copy, 3D virtual tours, targeted digital distribution, and luxury-specific print placement. Jorge's listing fee covers these at the luxury price point — no 'extras' billed separately."),
            ("Do you work with international buyers?", "Yes. Jorge's Keller Williams Premier Properties affiliation includes international luxury distribution. FIRPTA compliance and foreign buyer coordination (tax treaty considerations, financing, US entity setup) are handled with the client's tax advisor."),
            ("How are luxury offers different from regular offers?", "Higher complexity. Often involves cash, shorter contingency windows, trust or LLC buyers, and specific closing date requirements. Jorge structures counter-offers that protect the seller's downside while keeping qualified buyers engaged."),
            ("What's the realistic timeline for a luxury NJ sale?", "Well-priced luxury homes in premium commuter towns often go under contract in 30–60 days. Unique properties or those priced above market can take 6–9 months. The timeline depends heavily on pricing strategy and inventory conditions. Jorge gives an honest range before listing."),
            ("Do you represent luxury buyers as well?", "Yes. Buyer representation at the luxury level means off-market access, discreet showings, and negotiation experience that can save 5–10% on the purchase price. Jorge's buyer clients at $2M+ routinely see homes other agents never hear about."),
        ],
        "final_cta_h2": "Private Consultation — $1M+ NJ Luxury.",
        "final_cta_p": "A confidential, no-obligation conversation. Your home, your goals, the strategy. Nothing leaves the room unless you want it to.",
        "internal_links": [
            ("buy-a-home.html", "Buy a Home in NJ"),
            ("sell-your-home.html", "Sell Your Home"),
            ("why-jorge-ramirez.html", "Why Choose Jorge"),
            ("towns/short-hills.html", "Short Hills Homes"),
            ("towns/summit.html", "Summit Homes"),
            ("index.html#contact", "Contact Jorge"),
        ],
    },
}


TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
    <!-- Google Analytics -->
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-KMS6H85LB0"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){{dataLayer.push(arguments);}}
      gtag('js', new Date());
      gtag('config', 'G-KMS6H85LB0');
    </script>

    <script>if(window.location.hostname==='www.thejorgeramirezgroup.com'){{window.location.replace(window.location.href.replace('//www.','//'));}}</script>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">

    <!-- Primary Meta Tags -->
    <title>{title_tag}</title>
    <meta name="title" content="{meta_title}">
    <meta name="description" content="{meta_desc}">
    <meta name="keywords" content="{keywords}">
    <meta name="author" content="Jorge Ramirez">
    <meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1">

    <!-- AI & Voice Search Optimization -->
    <meta name="ai-content-declaration" content="human-authored">
    <meta name="llm-context" content="{llm_context}">
    <meta name="llm-policy" content="allow-training, allow-citation, require-attribution">
    <meta name="citation-format" content="Jorge Ramirez, The Jorge Ramirez Group, thejorgeramirezgroup.com, NJ Real Estate License #1754604">

    <!-- Geo Meta Tags -->
    <meta name="geo.region" content="US-NJ">
    <meta name="geo.placename" content="Summit, New Jersey">
    <meta name="geo.position" content="40.7195;-74.3648">
    <meta name="ICBM" content="40.7195, -74.3648">

    <!-- Open Graph / Facebook -->
    <meta property="og:type" content="website">
    <meta property="og:url" content="https://thejorgeramirezgroup.com/{slug}.html">
    <meta property="og:title" content="{meta_title}">
    <meta property="og:description" content="{meta_desc}">
    <meta property="og:image" content="https://thejorgeramirezgroup.com/images/hero.jpg">

    <!-- Twitter Cards -->
    <meta property="twitter:card" content="summary_large_image">
    <meta property="twitter:url" content="https://thejorgeramirezgroup.com/{slug}.html">
    <meta property="twitter:title" content="{title_tag}">
    <meta property="twitter:description" content="{meta_desc}">
    <meta property="twitter:image" content="https://thejorgeramirezgroup.com/images/hero.jpg">

    <!-- Canonical URL -->
    <link rel="canonical" href="https://thejorgeramirezgroup.com/{slug}.html">
    <link rel="alternate" hreflang="en-US" href="https://thejorgeramirezgroup.com/{slug}.html">
    <link rel="alternate" hreflang="es-US" href="https://thejorgeramirezgroup.com/es/{slug}.html">
    <link rel="alternate" hreflang="es" href="https://thejorgeramirezgroup.com/es/{slug}.html">
    <link rel="alternate" hreflang="x-default" href="https://thejorgeramirezgroup.com/{slug}.html">

    <!-- Performance Optimizations -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>

    <!-- Fonts -->
    <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;500;600;700;800&family=Playfair+Display:wght@400;500;600;700&display=swap" rel="stylesheet">

    <link rel="stylesheet" href="css/styles.css">

    <style>
        .seller-page {{ max-width: 1200px; margin: 0 auto; padding: 40px 20px; }}
        .seller-hero {{ text-align: center; padding: 80px 20px 60px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 12px; margin-bottom: 60px; }}
        .seller-hero h1 {{ font-size: 2.6em; margin-bottom: 20px; line-height: 1.2; }}
        .seller-hero p {{ font-size: 1.3em; max-width: 800px; margin: 0 auto 30px; line-height: 1.6; opacity: 0.95; }}
        .seller-hero .hero-ctas {{ margin-top: 35px; }}
        .seller-hero .hero-ctas a {{ display: inline-block; padding: 18px 36px; border-radius: 8px; font-size: 1.15em; font-weight: 600; text-decoration: none; margin: 10px; transition: all 0.3s ease; }}
        .seller-hero .btn-white {{ background: white; color: #667eea; }}
        .seller-hero .btn-white:hover {{ transform: translateY(-3px); box-shadow: 0 10px 30px rgba(0,0,0,0.2); }}
        .seller-hero .btn-outline {{ background: transparent; color: white; border: 2px solid white; }}
        .seller-hero .btn-outline:hover {{ background: white; color: #667eea; }}
        .why-jorge-sells {{ display: grid; grid-template-columns: 1fr 1fr; gap: 50px; align-items: center; margin: 60px 0; padding: 50px 40px; background: #f8f9fa; border-radius: 12px; }}
        .why-jorge-sells h2 {{ font-size: 2em; color: #1a1a1a; margin-bottom: 20px; }}
        .why-jorge-sells p {{ color: #555; line-height: 1.7; font-size: 1.05em; margin-bottom: 15px; }}
        .why-jorge-sells .credential-list {{ list-style: none; padding: 0; margin-top: 20px; }}
        .why-jorge-sells .credential-list li {{ padding: 10px 0; padding-left: 30px; position: relative; color: #333; font-weight: 500; }}
        .why-jorge-sells .credential-list li:before {{ content: "\2713"; position: absolute; left: 0; color: #667eea; font-weight: bold; }}
        .pricing-section {{ margin: 60px 0; text-align: center; }}
        .pricing-section h2 {{ font-size: 2.2em; color: #1a1a1a; margin-bottom: 15px; }}
        .pricing-section > p {{ color: #666; font-size: 1.15em; max-width: 800px; margin: 0 auto 40px; line-height: 1.7; }}
        .pricing-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 30px; }}
        .pricing-card {{ background: white; border: 2px solid #e0e0e0; border-radius: 12px; padding: 35px; text-align: left; transition: all 0.3s ease; }}
        .pricing-card:hover {{ border-color: #667eea; transform: translateY(-5px); box-shadow: 0 10px 30px rgba(102, 126, 234, 0.15); }}
        .pricing-card h3 {{ color: #333; font-size: 1.3em; margin-bottom: 12px; }}
        .pricing-card p {{ color: #666; line-height: 1.7; }}
        .process-section {{ margin: 60px 0; padding: 60px 40px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 12px; color: white; }}
        .process-section h2 {{ text-align: center; font-size: 2.2em; margin-bottom: 15px; }}
        .process-section > p {{ text-align: center; font-size: 1.15em; max-width: 800px; margin: 0 auto 50px; opacity: 0.95; line-height: 1.7; }}
        .process-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 30px; }}
        .process-step {{ background: rgba(255,255,255,0.12); border-radius: 12px; padding: 30px; text-align: center; transition: all 0.3s ease; }}
        .process-step:hover {{ background: rgba(255,255,255,0.2); transform: translateY(-5px); }}
        .process-step .step-num {{ display: inline-block; width: 45px; height: 45px; background: white; color: #667eea; border-radius: 50%; line-height: 45px; font-size: 1.3em; font-weight: bold; margin-bottom: 15px; }}
        .process-step h3 {{ font-size: 1.2em; margin-bottom: 10px; }}
        .process-step p {{ opacity: 0.9; line-height: 1.6; font-size: 0.95em; }}
        .ai-section {{ margin: 60px 0; padding: 50px 40px; background: #f8f9fa; border-radius: 12px; }}
        .ai-section h2 {{ font-size: 2em; color: #1a1a1a; margin-bottom: 15px; text-align: center; }}
        .ai-section > p {{ color: #666; font-size: 1.1em; max-width: 800px; margin: 0 auto 30px; line-height: 1.7; text-align: center; }}
        .faq-section {{ margin: 60px 0; }}
        .faq-section h2 {{ text-align: center; font-size: 2.2em; color: #1a1a1a; margin-bottom: 40px; }}
        .faq-item {{ margin-bottom: 20px; padding: 25px 30px; background: white; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }}
        .faq-item h3 {{ color: #1a1a1a; font-size: 1.2em; margin-bottom: 12px; }}
        .faq-item p {{ color: #555; line-height: 1.7; }}
        .mid-cta {{ background: #333; color: white; padding: 50px 40px; border-radius: 12px; text-align: center; margin: 60px 0; }}
        .mid-cta h2 {{ font-size: 2em; margin-bottom: 15px; }}
        .mid-cta p {{ font-size: 1.15em; max-width: 700px; margin: 0 auto 30px; opacity: 0.9; line-height: 1.6; }}
        .mid-cta a {{ display: inline-block; padding: 18px 36px; border-radius: 8px; font-size: 1.15em; font-weight: 600; text-decoration: none; margin: 10px; transition: all 0.3s ease; }}
        .mid-cta .btn-purple {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }}
        .mid-cta .btn-purple:hover {{ transform: translateY(-3px); box-shadow: 0 10px 30px rgba(102, 126, 234, 0.4); }}
        .mid-cta .btn-border {{ background: transparent; color: white; border: 2px solid white; }}
        .mid-cta .btn-border:hover {{ background: white; color: #333; }}
        .internal-links {{ margin: 60px 0; padding: 40px; background: #f8f9fa; border-radius: 12px; text-align: center; }}
        .internal-links h3 {{ font-size: 1.5em; color: #333; margin-bottom: 25px; }}
        .internal-links .link-grid {{ display: flex; flex-wrap: wrap; justify-content: center; gap: 15px; }}
        .internal-links .link-grid a {{ padding: 12px 25px; background: white; color: #667eea; text-decoration: none; border-radius: 8px; font-weight: 500; border: 1px solid #e0e0e0; transition: all 0.3s ease; }}
        .internal-links .link-grid a:hover {{ border-color: #667eea; background: #667eea; color: white; }}
        @media (max-width: 768px) {{
            .seller-hero h1 {{ font-size: 1.8em; }}
            .seller-hero p {{ font-size: 1.1em; }}
            .why-jorge-sells {{ grid-template-columns: 1fr; padding: 30px 20px; }}
            .process-section {{ padding: 40px 20px; }}
        }}
    </style>

    <!-- BreadcrumbList Schema -->
    <script type="application/ld+json">
    {{
      "@context": "https://schema.org",
      "@type": "BreadcrumbList",
      "itemListElement": [
        {{"@type": "ListItem", "position": 1, "name": "Home", "item": "https://thejorgeramirezgroup.com/"}},
        {{"@type": "ListItem", "position": 2, "name": "{breadcrumb_parent_name}", "item": "https://thejorgeramirezgroup.com/{breadcrumb_parent_url}"}},
        {{"@type": "ListItem", "position": 3, "name": "{breadcrumb_name}", "item": "https://thejorgeramirezgroup.com/{slug}.html"}}
      ]
    }}
    </script>

    <!-- FAQPage Schema -->
    <script type="application/ld+json">
    {{
      "@context": "https://schema.org",
      "@type": "FAQPage",
      "mainEntity": [
{faq_schema_items}
      ]
    }}
    </script>

    <!-- RealEstateAgent Schema -->
    <script type="application/ld+json">
    {{
      "@context": "https://schema.org",
      "@type": "RealEstateAgent",
      "name": "Jorge Ramirez",
      "telephone": "+1-908-230-7844",
      "email": "jorge.ramirez@kw.com",
      "url": "https://thejorgeramirezgroup.com/{slug}.html",
      "image": "https://thejorgeramirezgroup.com/images/jorge-ramirez-headshot.jpg",
      "address": {{
        "@type": "PostalAddress",
        "streetAddress": "488 Springfield Avenue",
        "addressLocality": "Summit",
        "addressRegion": "NJ",
        "postalCode": "07901",
        "addressCountry": "US"
      }},
      "areaServed": {{
        "@type": "State",
        "name": "New Jersey"
      }},
      "hasCredential": "NJ Real Estate License #1754604",
      "memberOf": {{
        "@type": "Organization",
        "name": "Keller Williams Premier Properties"
      }}
    }}
    </script>
</head>
<body>
    <!-- Navigation -->
    <nav id="navbar">
        <div class="nav-container">
            <a href="index.html" class="logo">
                <img src="images/jorge-logo.jpg" alt="The Jorge Ramirez Group" class="logo-img" width="250" height="100" loading="lazy">
            </a>
            <ul class="nav-links" id="navLinks">
                <li><a href="index.html#buy">Buy</a></li>
                <li><a href="sell-your-home.html">Sell</a></li>
                <li><a href="how-we-sell-your-home.html">How We Sell</a></li>
                <li><a href="index.html#communities">Communities</a></li>
                <li><a href="blog/">Blog</a></li>
                <li><a href="index.html#about">About</a></li>
                <li><a href="index.html#faq">FAQ</a></li>
                <li><a href="index.html#contact" class="nav-btn-consultation">Consultation</a></li>
            </ul>
            <button class="mobile-menu-btn" id="mobileMenuBtn">
                <span></span><span></span><span></span>
            </button>
        </div>
    </nav>

    <div class="seller-page">
        <!-- Hero -->
        <div class="seller-hero">
            <h1>{hero_h1}</h1>
            <p>{hero_p}</p>
            <div class="hero-ctas">
                <a href="https://value.thejorgeramirezgroup.com" class="btn-white" target="_blank" rel="noopener">Get Your Free Home Valuation</a>
                <a href="tel:+19082307844" class="btn-outline">Call Jorge: 908-230-7844</a>
            </div>
        </div>

        <!-- Pain Points -->
        <div class="pricing-section">
            <h2>{pain_h2}</h2>
            <p>{pain_intro}</p>
            <div class="pricing-grid">
{pain_cards_html}
            </div>
        </div>

        <!-- Mid CTA 1 -->
        <div class="mid-cta">
            <h2>{mid_cta_h2}</h2>
            <p>{mid_cta_p}</p>
            <div>
                <a href="tel:+19082307844" class="btn-purple">Call Jorge: 908-230-7844</a>
                <a href="index.html#contact" class="btn-border">Request a Consultation</a>
            </div>
        </div>

        <!-- Why Jorge -->
        <div class="why-jorge-sells">
            <div>
                <h2>{why_jorge_h2}</h2>
{why_jorge_ps_html}
                <ul class="credential-list">
{why_jorge_credentials_html}
                </ul>
            </div>
            <div style="text-align: center;">
                <img src="images/jorge-ramirez-headshot.jpg" alt="Jorge Ramirez - {breadcrumb_name}" style="max-width: 100%; border-radius: 12px; box-shadow: 0 10px 40px rgba(0,0,0,0.15);" width="400" height="500" loading="lazy">
                <p style="margin-top: 15px; color: #666; font-size: 0.95em;">Jorge Ramirez | NJ License #1754604<br>Keller Williams Premier Properties, Summit</p>
            </div>
        </div>

        <!-- Process -->
        <div class="process-section">
            <h2>{process_h2}</h2>
            <p>{process_intro}</p>
            <div class="process-grid">
{process_steps_html}
            </div>
        </div>

        <!-- AI/Marketing Section -->
        <div class="ai-section">
            <h2>{ai_h2}</h2>
            <p>{ai_intro}</p>
            <div class="pricing-grid">
{ai_cards_html}
            </div>
        </div>

        <!-- FAQs -->
        <div class="faq-section">
            <h2>{faq_h2}</h2>
{faqs_html}
        </div>

        <!-- Internal Links -->
        <div class="internal-links">
            <h3>Related Resources</h3>
            <div class="link-grid">
{internal_links_html}
            </div>
        </div>

        <!-- Final CTA -->
        <div class="mid-cta">
            <h2>{final_cta_h2}</h2>
            <p>{final_cta_p}</p>
            <div>
                <a href="https://value.thejorgeramirezgroup.com" class="btn-purple" target="_blank" rel="noopener">Get My Free Home Valuation</a>
                <a href="tel:+19082307844" class="btn-border">Call Jorge: 908-230-7844</a>
            </div>
            <p style="margin-top: 20px; font-size: 0.95em; opacity: 0.7;">Jorge Ramirez | Keller Williams Premier Properties | 488 Springfield Avenue, Summit, NJ 07901 | NJ License #1754604</p>
        </div>
    </div>

    <!-- Footer -->
    <footer>
        <div class="footer-content">
            <div class="footer-section">
                <img src="images/jorge-logo.jpg" alt="The Jorge Ramirez Group Logo" style="max-width: 250px; margin-bottom: 1.5rem; background: white; padding: 15px; border-radius: 5px;" loading="lazy" width="250" height="100">
                <h3>Jorge Ramirez</h3>
                <p>Full-time Realtor with Keller Williams Premier Properties since 2017.</p>
                <p style="margin-top: 1rem;">
                    488 Springfield Avenue<br>
                    Summit, NJ 07901<br>
                    908-230-7844<br>
                    <a href="mailto:jorge.ramirez@kw.com">jorge.ramirez@kw.com</a>
                </p>
                <img src="images/kw-logo.png" alt="Keller Williams Premier Properties Logo" style="max-width: 180px; margin-top: 1.5rem;" loading="lazy" width="180" height="60">
            </div>
            <div class="footer-section">
                <h3>Quick Links</h3>
                <a href="index.html#buy">Buy</a>
                <a href="sell-your-home.html">Sell</a>
                <a href="how-we-sell-your-home.html">How We Sell</a>
                <a href="index.html#communities">Communities</a>
                <a href="index.html#about">About</a>
                <a href="index.html#faq">FAQ</a>
                <a href="index.html#contact">Contact</a>
            </div>
            <div class="footer-section">
                <h3>Seller Resources</h3>
                <a href="sell-your-home.html">Sell Your Home</a>
                <a href="home-valuation.html">Free Home Valuation</a>
                <a href="divorce-home-sale-nj.html">Divorce Home Sale</a>
                <a href="inherited-home-nj.html">Inherited Home</a>
                <a href="sell-rental-property-nj.html">Selling a Rental</a>
                <a href="downsizing-nj.html">Downsizing</a>
                <a href="relocating-from-nj.html">Relocating From NJ</a>
                <a href="cash-offer-nj.html">Cash Offer Option</a>
            </div>
            <div class="footer-section">
                <h3>Buyer Resources</h3>
                <a href="buy-a-home.html">Buy a Home</a>
                <a href="buyer-agency-agreement-nj.html">Buyer Agency NJ</a>
                <a href="nyc-to-nj-relocation.html">NYC to NJ</a>
                <a href="investment-property-nj.html">Investment Property</a>
                <a href="luxury-homes-nj.html">Luxury Homes</a>
                <a href="tools/mortgage-calculator.html">Mortgage Calculator</a>
                <a href="closing-costs-calculator.html">Closing Costs Calculator</a>
            </div>
        </div>
        <div class="footer-bottom">
            <p>&copy; 2026 Jorge Ramirez - Keller Williams Premier Properties. All rights reserved.</p>
            <p>488 Springfield Avenue, Summit, NJ 07901 | 908-230-7844 | jorge.ramirez@kw.com</p>
        </div>
    </footer>

    <script src="js/main.js"></script>
</body>
</html>
"""


def render_faq_schema(faqs):
    items = []
    for q, a in faqs:
        # Escape quotes in JSON
        q_esc = q.replace('"', '\\"')
        a_clean = a.replace('<a href=', ' (see ').replace('style="color: #667eea;">', '').replace('</a>', ')').replace('"', "'")
        # Simpler: just strip HTML tags from answer for schema
        import re
        a_text = re.sub(r'<[^>]+>', '', a).replace('"', '\\"').replace('\n', ' ').strip()
        items.append(
            f'        {{"@type": "Question", "name": "{q_esc}", "acceptedAnswer": {{"@type": "Answer", "text": "{a_text}"}}}}'
        )
    return ',\n'.join(items)


def render_page(slug, cfg):
    parent_name, parent_url = cfg["breadcrumb_parent"]

    pain_cards_html = '\n'.join(
        f'                <div class="pricing-card">\n                    <h3>{title}</h3>\n                    <p>{body}</p>\n                </div>'
        for title, body in cfg["pain_cards"]
    )

    why_jorge_ps_html = '\n'.join(f'                <p>{p}</p>' for p in cfg["why_jorge_ps"])
    why_jorge_credentials_html = '\n'.join(f'                    <li>{c}</li>' for c in cfg["why_jorge_credentials"])

    process_steps_html = '\n'.join(
        f'                <div class="process-step">\n                    <div class="step-num">{i+1}</div>\n                    <h3>{title}</h3>\n                    <p>{body}</p>\n                </div>'
        for i, (title, body) in enumerate(cfg["process_steps"])
    )

    ai_cards_html = '\n'.join(
        f'                <div class="pricing-card">\n                    <h3>{title}</h3>\n                    <p>{body}</p>\n                </div>'
        for title, body in cfg["ai_cards"]
    )

    faqs_html = '\n'.join(
        f'            <div class="faq-item">\n                <h3>{q}</h3>\n                <p>{a}</p>\n            </div>'
        for q, a in cfg["faqs"]
    )

    internal_links_html = '\n'.join(
        f'                <a href="{url}">{label}</a>'
        for url, label in cfg["internal_links"]
    )

    faq_schema_items = render_faq_schema(cfg["faqs"])

    return TEMPLATE.format(
        slug=slug,
        title_tag=cfg["title_tag"],
        meta_title=cfg["meta_title"],
        meta_desc=cfg["meta_desc"],
        keywords=cfg["keywords"],
        llm_context=cfg["llm_context"],
        breadcrumb_parent_name=parent_name,
        breadcrumb_parent_url=parent_url,
        breadcrumb_name=cfg["breadcrumb_name"],
        hero_h1=cfg["hero_h1"],
        hero_p=cfg["hero_p"],
        pain_h2=cfg["pain_h2"],
        pain_intro=cfg["pain_intro"],
        pain_cards_html=pain_cards_html,
        mid_cta_h2=cfg["mid_cta_h2"],
        mid_cta_p=cfg["mid_cta_p"],
        why_jorge_h2=cfg["why_jorge_h2"],
        why_jorge_ps_html=why_jorge_ps_html,
        why_jorge_credentials_html=why_jorge_credentials_html,
        process_h2=cfg["process_h2"],
        process_intro=cfg["process_intro"],
        process_steps_html=process_steps_html,
        ai_h2=cfg["ai_h2"],
        ai_intro=cfg["ai_intro"],
        ai_cards_html=ai_cards_html,
        faq_h2=cfg["faq_h2"],
        faqs_html=faqs_html,
        internal_links_html=internal_links_html,
        final_cta_h2=cfg["final_cta_h2"],
        final_cta_p=cfg["final_cta_p"],
        faq_schema_items=faq_schema_items,
    )


def main():
    count = 0
    for slug, cfg in PAGES.items():
        html = render_page(slug, cfg)
        out_path = REPO / f"{slug}.html"
        out_path.write_text(html)
        print(f"✓ {slug}.html ({len(html):,} bytes)")
        count += 1
    print(f"\n{count} pages generated.")


if __name__ == "__main__":
    main()
