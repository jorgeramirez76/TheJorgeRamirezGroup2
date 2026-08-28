#!/usr/bin/env python3
"""Rebuild six Union County guides from reviewed primary-source research."""

from __future__ import annotations

import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = json.loads(
    (ROOT / "data" / "union-priority-town-sources.json").read_text(encoding="utf-8")
)
ACCESSED = "2026-08-25"
PAGE_MODIFIED_ON = "2026-08-27"


TOWNS = {
    "cranford": {
        "name": "Cranford",
        "postal": "07016",
        "title": "Cranford NJ Real Estate Research | Jorge Ramirez",
        "description": "Research Cranford, NJ real estate with official links for Raritan Valley rail, public schools, zoning, flood maps, parks, taxes, and parcel due diligence.",
        "hero": "A source-backed starting point for checking a Cranford address, from the Raritan Valley Line and public-school records to zoning and floodplain research.",
        "image": (
            "/images/towns/cranford-1.webp", "1280", "960",
            "Cranford NJ Transit station platform in Cranford, New Jersey",
            "Cranford NJ Transit station", "Adam Moss",
            "https://commons.wikimedia.org/wiki/File:Cranford_Station.jpg",
            "CC BY-SA 2.0", "https://creativecommons.org/licenses/by-sa/2.0/",
        ),
        "orientation_title": "Cranford research starts with the Rahway River, station, and parcel",
        "orientation": [
            "Cranford is governed by a five-member Township Committee, which appoints the mayor and deputy mayor each year. The official committee page is the direct place to review public agendas, approved minutes, appointments, and links to current municipal action instead of relying on a summary that can become stale.",
            "For a housing decision, the town-wide description matters less than the exact lot. Cranford publishes an interactive zoning map, land-development materials, and separate flood resources. Because the Township specifically asks prospective buyers and owners to understand possible flood exposure, a parcel review should include both municipal mapping and the current federal flood map before an offer or renovation plan is finalized.",
        ],
        "orientation_cards": [
            ("Public decisions", "Use Township Committee agendas and minutes to see adopted action, then confirm how an ordinance applies with the responsible office."),
            ("Rail access", "Cranford Station is on NJ TRANSIT's Raritan Valley Line. Use the station page for current advisories, ticketing, bicycle, and parking information."),
            ("River and flood review", "Check the Township flood-map page and current FEMA material by address. A neighborhood label is not a substitute for parcel research."),
            ("Parks and public space", "Union County's directory identifies Nomahegan, Sperry, and Unami among the public park resources associated with Cranford."),
        ],
        "facts_heading": "Who publishes the Cranford facts that affect a move?",
        "facts_intro": "Use the agency responsible for each decision. These links lead to the live public record, not a score or sales pitch.",
        "facts": [
            ("Municipal record", "Township Committee", "Five commissioners; current agendas and approved minutes", "https://www.cranfordnj.org/1952/Township-Committee"),
            ("Train service", "Cranford Station", "Raritan Valley Line station details and alerts", "https://www.njtransit.com/station/cranford-station"),
            ("School research", "Cranford Public Schools", "District directory, registration, reports, and notices", "https://www.cranfordschools.org/"),
            ("Land and flood review", "Township maps", "Zoning, applications, and parcel-level flood resources", "https://www.cranfordnj.org/2479/Applications-Maps-and-Resources"),
        ],
        "schools_heading": "Researching Cranford Public Schools without reducing them to a score",
        "schools": [
            "Cranford Public Schools maintains the current district directory, registration materials, calendars, and reports. Its school list includes multiple elementary configurations, two K–8 campuses, and Cranford High School. Buyers should verify the assigned school for a specific address with the district; proximity to a building does not establish assignment.",
            "For comparable public data, search the New Jersey Department of Education School Performance Reports by district or individual school. NJDOE presents these reports as a starting point for learning and conversation. Review the underlying measures and year, then add district documents, board materials, programs, transportation rules, and a direct district conversation to the decision.",
        ],
        "transit_heading": "Cranford transportation: verify the trip you will actually make",
        "transit": [
            "NJ TRANSIT identifies Cranford Station on the Raritan Valley Line. The station page is the reliable place for the service line, live advisories, ticketing, bicycle facilities, and parking notices. Timetables, transfer patterns, track work, and parking arrangements can change, so this guide does not publish a promised travel duration.",
            "Test a trip from the property, not just from the station pin. Include the walk or drive to the station, parking eligibility, departure needed for the actual work schedule, transfer requirements, and the final leg at the destination. Re-run that check for evenings and weekends if those trips matter to the household.",
        ],
        "transit_cards": [
            ("Station record", "Open NJ TRANSIT's Cranford Station page and then the current schedule and alert tools before comparing properties.", "https://www.njtransit.com/station/cranford-station"),
            ("Parking check", "Confirm permit rules and availability with the operator named by NJ TRANSIT; third-party parking details can change without notice.", "https://www.njtransit.com/station/cranford-station"),
            ("Flood-day planning", "A normal-day route does not answer flood or storm access questions. Review official emergency and flood information for the specific address.", "https://www.cranfordnj.org/2600/Flood-Maps"),
        ],
        "civic_heading": "Cranford parks, downtown, and civic records",
        "civic": [
            "Union County's parks directory is useful for confirming which facilities are county-managed and what activities are listed at each location. It includes Cranford entries such as Nomahegan Park, Sperry Park, and Unami Park. Verify reservation rules, closures, and facility status on the county site before treating an amenity as available for a particular use.",
            "For downtown or redevelopment questions, use Cranford's planning and zoning resources and adopted-ordinance archive. Public plans can explain intended land-use policy, but they are not a guarantee that a proposed project will proceed. Confirm adopted approvals and current status with the Township when a nearby proposal affects a buying or selling decision.",
        ],
        "civic_links": [
            ("Union County parks directory", "https://ucnj.org/parks-activities/"),
            ("Cranford planning maps and resources", "https://www.cranfordnj.org/2479/Applications-Maps-and-Resources"),
            ("Cranford flood maps", "https://www.cranfordnj.org/2600/Flood-Maps"),
        ],
        "diligence_heading": "Cranford property due diligence before price negotiations",
        "diligence_intro": "Ask for documents tied to the block, lot, structure, and intended use. Verify every time-sensitive item with its official source.",
        "diligence": [
            ("Flood and drainage", "Review the current FIRM and Township flood information, then inspect grading, drainage, water entry history, insurance requirements, and permits with qualified professionals."),
            ("Zoning and improvements", "Confirm the zoning district, overlays, setbacks, prior approvals, open permits, and whether a planned addition or accessory use is allowed."),
            ("Tax record", "Obtain the current municipal tax record and assessment for the exact parcel. Do not estimate a future bill from a neighboring home or listing field."),
            ("School assignment", "Verify assignment and registration requirements directly with Cranford Public Schools before relying on a portal, map pin, or prior owner's information."),
        ],
        "checklist_title": "A Cranford buyer-and-seller decision checklist",
        "steps": [
            ("Define the parcel question", "Record the block and lot, intended use, financing needs, station routine, and any renovation plan before comparing addresses."),
            ("Pull the public record", "Open zoning, flood, tax, permit, school, and transit sources for that address; save dated copies of anything central to the decision."),
            ("Bring in the right review", "Use an attorney, inspector, lender, insurance professional, surveyor, or municipal office as the issue requires; a real-estate guide cannot replace them."),
            ("Price after verification", "For a purchase, compare the verified property condition and restrictions with current listing and closed-sale data. For a sale, disclose known material facts and document improvements."),
        ],
        "faqs": [
            ("Does Cranford have NJ TRANSIT rail service?", "Yes. NJ TRANSIT lists Cranford Station on the Raritan Valley Line. Check the official station, schedule, and alerts for the trip date rather than relying on an estimated travel time."),
            ("How should I check flood exposure for a Cranford home?", "Start with Cranford's official flood-map page and current federal mapping, then verify the exact parcel, elevation, insurance, drainage, and building history with the appropriate professionals and Township offices."),
            ("Where can I research Cranford public schools?", "Use Cranford Public Schools for current schools, assignment, registration, calendars, and district records, and use NJDOE School Performance Reports for state-published data. Verify assignment for the property directly with the district."),
            ("Can a zoning map confirm that I can renovate?", "No. A map identifies a starting district, but an official parcel review must account for overlays, lot conditions, prior approvals, current ordinances, and the exact scope of work."),
            ("What should a Cranford seller assemble before listing?", "Useful records include the current tax card, survey, permits and approvals, improvement invoices, known flood or water information, utility and system details, and disclosures reviewed with the appropriate professionals."),
        ],
        "nearby": [("Westfield", "westfield"), ("Garwood", "garwood"), ("Fanwood", "fanwood"), ("Roselle Park", "roselle-park"), ("Springfield", "springfield")],
    },
    "fanwood": {
        "name": "Fanwood",
        "postal": "07023",
        "title": "Fanwood NJ Real Estate Research | Jorge Ramirez",
        "description": "Research Fanwood, NJ real estate with official links for its Raritan Valley station, regional public schools, zoning, recreation, taxes, and parcel checks.",
        "hero": "A practical guide to Fanwood's station-centered borough, shared public-school district, municipal zoning resources, and address-level property checks.",
        "image": (
            "/images/towns/fanwood-1.webp", "1280", "720",
            "Fanwood NJ Transit station and downtown Fanwood, New Jersey",
            "Fanwood NJ Transit station", "AtsushiJC",
            "https://commons.wikimedia.org/wiki/File:Fanwood_Station_View.jpg",
            "CC BY-SA 4.0", "https://creativecommons.org/licenses/by-sa/4.0/",
        ),
        "orientation_title": "Fanwood is compact, but every address still needs its own review",
        "orientation": [
            "Fanwood's official government page describes an elected mayor and six council members, with the council acting as the borough's legislative body. The public meeting record is useful when a buyer or owner wants to trace an ordinance, capital item, or land-use decision beyond a headline.",
            "The station area is a defining piece of local geography. Fanwood Station sits near North and South avenues at Martine Avenue on the Raritan Valley Line, while the borough's planning material addresses land use around the South Avenue corridor. Those facts help frame research; they do not tell whether a particular property has the parking, noise, access, or zoning characteristics a person expects.",
        ],
        "orientation_cards": [
            ("Borough government", "Use Mayor and Council records for adopted municipal action and the Planning Board page for land-use materials and public hearing information."),
            ("Station area", "NJ TRANSIT maintains current Fanwood Station service and parking details; the borough handles municipal questions connected to local lots."),
            ("Shared school district", "Fanwood participates in Scotch Plains-Fanwood Public Schools. The district's street index is the address-assignment research tool."),
            ("Home projects", "The borough Zoning Office publishes the map, forms, and parcel-specific submission guidance for additions and accessory improvements."),
        ],
        "facts_heading": "The public sources behind a Fanwood address check",
        "facts_intro": "Fanwood decisions cross borough, regional-district, and state agencies. Start with the office that owns the record.",
        "facts": [
            ("Municipal record", "Mayor and Council", "Ordinances, meetings, minutes, and borough responsibilities", "https://fanwoodnj.org/government/"),
            ("Train service", "Fanwood Station", "Raritan Valley Line station, alerts, and parking notices", "https://www.njtransit.com/station/fanwood-station"),
            ("School research", "Scotch Plains-Fanwood district", "School list and address-based street index", "https://www.spfk12.org/our-district/our-schools"),
            ("Parcel review", "Fanwood Zoning Office", "Zoning map, ordinance links, project forms, and review guidance", "https://fanwoodnj.org/departments/zoning/"),
        ],
        "schools_heading": "How to research the Scotch Plains-Fanwood school system",
        "schools": [
            "Fanwood is part of the regional Scotch Plains-Fanwood Public Schools system. The district's official school page lists La Grande Elementary in Fanwood alongside district campuses in Scotch Plains, including the middle schools and high school. It also directs people to a street index when they are unsure which school serves an address.",
            "Treat that address lookup as the first step, then confirm with the district during the transaction. NJDOE School Performance Reports provide official state data by school and district without turning the decision into a single label. Compare measures and reporting years, review district budgets and board records, and ask the district about programs or services that matter to the specific student.",
        ],
        "transit_heading": "Fanwood transportation: station facts, parking, and schedule checks",
        "transit": [
            "NJ TRANSIT lists Fanwood Station on the Raritan Valley Line at the Martine Avenue and North/South Avenue area. The official page separates the station's parking lots and identifies their operators, which matters because permit eligibility, payment, hours, and availability may differ by lot and can change.",
            "For a real comparison, test the trip from the front door at the needed departure time. Check the current rail schedule and alerts, confirm the applicable parking or drop-off plan, and include the last leg at the destination. A station within the same borough does not create the same routine for every block.",
        ],
        "transit_cards": [
            ("Rail record", "Use NJ TRANSIT's Fanwood Station page and current Raritan Valley schedule rather than a third-party commute estimate.", "https://www.njtransit.com/station/fanwood-station"),
            ("Lot-by-lot check", "Identify the lot operator and confirm current resident or nonresident rules directly; NJ TRANSIT notes that third-party parking details may change.", "https://www.njtransit.com/station/fanwood-station"),
            ("Station-area land use", "Review the borough Planning Board's current documents when a property is near a mapped corridor or a noticed application.", "https://fanwoodnj.org/departments/planning-board/"),
        ],
        "civic_heading": "Fanwood recreation and public participation",
        "civic": [
            "Fanwood Recreation oversees borough parks and facilities, reservations, programming, and community events. Its official page is the place to verify whether a field or building is reservable and which rules apply. Event calendars and program offerings change, so they should be checked when the activity is part of a moving decision.",
            "The borough publishes meeting schedules, public notices, planning documents, and municipal contacts. This makes it possible to distinguish an adopted action from a proposal. When a nearby application or corridor plan matters, read the filed materials and minutes and ask the responsible borough office about status instead of treating an old plan as a construction promise.",
        ],
        "civic_links": [
            ("Fanwood Recreation", "https://fanwoodnj.org/departments/recreation-info/"),
            ("Fanwood Planning Board", "https://fanwoodnj.org/departments/planning-board/"),
            ("Fanwood government and meetings", "https://fanwoodnj.org/government/"),
        ],
        "diligence_heading": "Fanwood property checks: zoning, taxes, and assignment",
        "diligence_intro": "A small borough can still contain different zones, lot constraints, school assignments, and station routines. Verify the exact property.",
        "diligence": [
            ("Survey and zoning", "Use a current survey and proposed scope when asking the Zoning Office about setbacks, coverage, structures, fences, driveways, or a change of use."),
            ("Assessment record", "Pull the official assessment and tax map from the borough source. Confirm the current bill and any added assessment instead of projecting from a portal."),
            ("School street index", "Check the district's address index, then confirm assignment, transportation, and registration requirements directly with the regional district."),
            ("Station impacts", "Visit at relevant hours and examine access, parking, traffic, sound, and pedestrian route from the particular block; do not infer them from borough size."),
        ],
        "checklist_title": "A Fanwood buyer-and-seller decision checklist",
        "steps": [
            ("Map the daily routine", "Test the property-to-station or road route at the times that matter and identify the exact lot or curb plan rather than assuming station access."),
            ("Check the shared systems", "Confirm the Scotch Plains-Fanwood school assignment, utilities, municipal services, and any shared-service office relevant to the address."),
            ("Validate the lot", "Match the survey to the zoning map and official record; ask about prior approvals, open permits, easements, coverage, and intended improvements."),
            ("Build a documented position", "Buyers can price condition and restrictions with current sale data; sellers can prepare permits, improvement records, survey, and disclosures before marketing."),
        ],
        "faqs": [
            ("Which rail line serves Fanwood Station?", "NJ TRANSIT identifies Fanwood Station on the Raritan Valley Line. Use its current schedule and alert tools for a specific trip rather than relying on a fixed travel-time claim."),
            ("Is Fanwood a separate public-school district?", "Fanwood is served by Scotch Plains-Fanwood Public Schools. The district publishes its schools and an address-based street index; confirm assignment and registration directly with the district."),
            ("Where can I check Fanwood zoning for a renovation?", "The Borough Zoning Office publishes the zoning map, land-use links, and project forms. Submit the parcel survey and exact proposal for official review before assuming a project is permitted."),
            ("How do I verify Fanwood property taxes?", "Use the Borough tax page and official parcel record for the assessment and current bill, then ask the assessor or collector about questions tied to that property."),
            ("What should a Fanwood seller prepare?", "Prepare the survey, permits and approvals, improvement documentation, current tax and assessment record, known property-condition information, and disclosures for professional review."),
        ],
        "nearby": [("Scotch Plains", "scotch-plains"), ("Westfield", "westfield"), ("Garwood", "garwood"), ("Cranford", "cranford"), ("Berkeley Heights", "berkeley-heights")],
    },
    "roselle-park": {
        "name": "Roselle Park",
        "postal": "07204",
        "title": "Roselle Park NJ Real Estate Research | Jorge Ramirez",
        "description": "Research Roselle Park, NJ real estate with official links for Raritan Valley rail, public schools, land use, parks, tax maps, assessments, and permits.",
        "hero": "A verified starting point for Roselle Park station access, borough land-use records, public schools, civic spaces, and parcel-specific research.",
        "image": (
            "/images/towns/roselle-park-1.webp", "1280", "960",
            "Roselle Park NJ Transit station platform in Roselle Park, New Jersey",
            "Roselle Park NJ Transit station", "Adam Moss",
            "https://commons.wikimedia.org/wiki/File:Roselle_Park_Station_-_January_2015.jpg",
            "CC BY-SA 2.0", "https://creativecommons.org/licenses/by-sa/2.0/",
        ),
        "orientation_title": "Roselle Park decisions connect the station, borough record, and exact lot",
        "orientation": [
            "Roselle Park's official government page explains its borough structure and identifies a combined Municipal Land Use Board that performs both planning and zoning-board functions. That combined structure is useful to know when tracing an application, variance, redevelopment document, or public hearing affecting a property.",
            "The borough is served by Roselle Park Station on NJ TRANSIT's Raritan Valley Line at Lincoln and Chestnut streets. A station reference is only the beginning of transportation research: platform advisories, access work, parking operators, and service patterns should be checked on the official page for the dates relevant to a move.",
        ],
        "orientation_cards": [
            ("Government record", "Use the borough government page and meeting materials to distinguish adopted action from discussion or a pending application."),
            ("Combined land-use board", "Planning and zoning-board functions are handled by the Municipal Land Use Board; review its filed materials for parcel-specific action."),
            ("Raritan Valley station", "NJ TRANSIT maintains Roselle Park Station advisories, ticketing, line, and access information at the official source."),
            ("Borough-scale amenities", "The municipal profile identifies Herm Shaw Field and Acker Park; verify current facilities and programming with the borough."),
        ],
        "facts_heading": "Where to verify Roselle Park housing questions",
        "facts_intro": "Use borough, transit, district, and state records together. No single directory answers every property question.",
        "facts": [
            ("Municipal structure", "Borough government", "Council information and combined land-use-board context", "https://www.rosellepark.net/27/Government"),
            ("Train service", "Roselle Park Station", "Raritan Valley Line station details and active advisories", "https://www.njtransit.com/station/roselle-park-station"),
            ("School research", "Roselle Park School District", "District structure and current registration requirements", "https://www.rpsd.org/registration-for-the-roselle-park-2"),
            ("Land-use record", "Planning and Zoning", "Zoning map and current borough planning documents", "https://www.rosellepark.net/186/Planning-and-Zoning"),
        ],
        "schools_heading": "Roselle Park school research by district record, not label",
        "schools": [
            "The Roselle Park School District's registration page describes a district with three elementary schools, one middle school, and one high school. Registration requirements and attendance assignments are administrative facts that should be confirmed directly with the district for the property and school year involved.",
            "NJDOE School Performance Reports add state-published information for each school and the district. Read the report year and individual measures rather than collapsing the data into one adjective. District board materials, budgets, course information, student-service resources, transportation policies, and direct questions may be more relevant to a particular decision than an aggregated portal score.",
        ],
        "transit_heading": "Roselle Park transportation and station-status research",
        "transit": [
            "NJ TRANSIT lists Roselle Park Station at Lincoln and Chestnut streets on the Raritan Valley Line. The official station page also carries advisories and parking information. Because station construction, platform access, parking operation, and schedules can change, verify the exact travel date and accessibility needs in NJ TRANSIT's live tools.",
            "A property comparison should include the actual path to the station, street crossings, pickup or parking plan, service needed after normal work hours, and the destination-side connection. Visit the route under realistic conditions and avoid converting a map distance into a guaranteed door-to-door trip.",
        ],
        "transit_cards": [
            ("Station advisory", "Check the Roselle Park Station page for current access notices and use the schedule tool for the intended travel day.", "https://www.njtransit.com/station/roselle-park-station"),
            ("Parking operator", "Confirm the operator, payment, eligibility, and available alternatives shown by NJ TRANSIT before relying on a listing's parking statement.", "https://www.njtransit.com/station/roselle-park-station"),
            ("Street-level route", "Walk or drive the property-to-station path at relevant hours and evaluate the route itself rather than a straight-line map distance.", "https://www.njtransit.com/station/roselle-park-station"),
        ],
        "civic_heading": "Roselle Park civic spaces and public records",
        "civic": [
            "The borough profile identifies Herm Shaw Field and Acker Park among local recreation resources. Municipal pages are the right place to verify the current facility, event, reservation, and program details. Amenities should not be inferred from an old listing description or a similarly named location in another municipality.",
            "For public participation, the government and land-use pages point to the boards responsible for ordinances and applications. When a project near a target property matters, note the application number, read the plans and resolutions, and verify current status with the Borough. A plan under review is not the same as an approval, and an approval is not proof of a completion date.",
        ],
        "civic_links": [
            ("Roselle Park municipal profile", "https://www.rosellepark.net/257/Township-Profile"),
            ("Roselle Park government", "https://www.rosellepark.net/27/Government"),
            ("Planning and Zoning", "https://www.rosellepark.net/186/Planning-and-Zoning"),
        ],
        "diligence_heading": "Roselle Park tax-map and land-use due diligence",
        "diligence_intro": "Connect the listing address to the official block and lot, then verify records with the borough office that maintains them.",
        "diligence": [
            ("Block and lot", "Use the assessor's tax maps and parcel record to confirm the legal research identifier, assessment information, and office responsible for questions."),
            ("Zoning map", "Identify the mapped district and then ask how current ordinances, prior approvals, lot conditions, and the proposed use apply to the parcel."),
            ("Permits and approvals", "Check for open or final permits and Municipal Land Use Board resolutions relevant to additions, conversions, parking, or other material work."),
            ("School registration", "Review the district's current documentation and confirm address eligibility and assignment directly before making a school-dependent decision."),
        ],
        "checklist_title": "A Roselle Park buyer-and-seller decision checklist",
        "steps": [
            ("Confirm identity", "Match the street address, municipality, block and lot, postal code, and tax record so every later search concerns the same property."),
            ("Read the board trail", "Search the combined Municipal Land Use Board record and zoning resources for parcel approvals or nearby applications that affect the decision."),
            ("Test station access", "Use current NJ TRANSIT information and a real property-to-platform route, including parking or pickup and any accessibility requirement."),
            ("Document condition", "Buyers should pair inspections and professional review with public records; sellers should organize permits, repairs, survey, assessment, and disclosures."),
        ],
        "faqs": [
            ("Which train line serves Roselle Park?", "NJ TRANSIT lists Roselle Park Station on the Raritan Valley Line. Confirm current schedules, advisories, platform access, and parking on the official NJ TRANSIT page."),
            ("Who reviews land-use applications in Roselle Park?", "The Borough identifies a combined Municipal Land Use Board that performs planning and zoning-board functions. Use borough records to verify the application and status for a specific parcel."),
            ("How many public schools does the district list?", "The district registration page identifies three elementary schools, one middle school, and one high school. Verify the assigned school and current registration rules directly with the district."),
            ("Where can I find Roselle Park tax maps?", "The Borough Tax Assessor page links tax maps and assessment-appeal resources. Use the exact block and lot and contact the assessor for parcel-record questions."),
            ("How should a seller handle unclosed work?", "Gather permits, inspections, approvals, contractor records, and the survey, then ask the municipal office and transaction professionals what must be resolved or disclosed before closing."),
        ],
        "nearby": [("Cranford", "cranford"), ("Garwood", "garwood"), ("Kenilworth", "kenilworth"), ("Linden", "linden"), ("Union", "union")],
    },
    "new-providence": {
        "name": "New Providence",
        "postal": "07974",
        "title": "New Providence NJ Real Estate Research | Jorge Ramirez",
        "description": "Research New Providence, NJ real estate with official links for both rail stations, public schools, borough parks, ordinances, taxes, assessments, and parcel checks.",
        "hero": "A source-backed guide to New Providence's two NJ TRANSIT stations, borough government, four public-school campuses, civic facilities, and property records.",
        "image": (
            "/images/towns/new-providence-1.webp", "1280", "854",
            "New Providence NJ Transit station building in New Providence, New Jersey",
            "New Providence NJ Transit station", "Kellerra",
            "https://commons.wikimedia.org/wiki/File:New_Providence_Station_-_2024.jpg",
            "CC0 1.0", "https://creativecommons.org/publicdomain/zero/1.0/",
        ),
        "orientation_title": "New Providence has two station areas and one parcel-specific decision",
        "orientation": [
            "New Providence's official government page describes a mayor-and-council borough. The mayor serves as chief executive, while the six-member council acts as the legislative body. Meeting records, ordinances, and public notices are the appropriate sources for municipal action that could affect a property.",
            "NJ TRANSIT maintains separate pages for New Providence Station at Springfield Avenue and Pittsford Way and Murray Hill Station at Foley Place between Floral Avenue and Southgate Road. Treat them as distinct access points. The practical station for an address depends on the route, parking rules, schedule, and travel pattern—not simply the municipality name.",
        ],
        "orientation_cards": [
            ("Two stations", "Compare New Providence and Murray Hill station access separately using NJ TRANSIT's current pages and a route from the target address."),
            ("Borough record", "Mayor and Council materials establish adopted action; the ordinance archive helps trace zoning and other municipal-law changes."),
            ("Four school campuses", "The district lists two elementary schools, a middle school, and a high school; assignment and registration remain district determinations."),
            ("Public facilities", "The borough directory lists Centennial Park, municipal recreation space, and fields with official addresses and facility information."),
        ],
        "facts_heading": "New Providence research by agency and location",
        "facts_intro": "This borough has two station records and separate municipal, district, and assessment sources. Keep them distinct in the transaction file.",
        "facts": [
            ("Government", "Mayor and Borough Council", "Municipal structure, meetings, agendas, and contacts", "https://www.newprov.us/404/Mayor-Borough-Council"),
            ("Rail option one", "New Providence Station", "Morris & Essex system station information", "https://www.njtransit.com/station/new-providence-station"),
            ("Rail option two", "Murray Hill Station", "Separate location, parking, and station information", "https://www.njtransit.com/station/murray-hill-station"),
            ("Schools", "New Providence School District", "Official list of the district's four campuses", "https://www.npsd.k12.nj.us/schools"),
        ],
        "schools_heading": "New Providence public-school research by campus and address",
        "schools": [
            "The New Providence School District lists Allen W. Roberts Elementary School, Salt Brook Elementary School, New Providence Middle School, and New Providence High School. Use the district for registration, assignment, redistricting information, transportation, board materials, calendars, and program questions tied to the relevant school year.",
            "NJDOE School Performance Reports provide state-published data and reporting context. Review the individual measures and source year, not a third-party shorthand. A careful school inquiry can include board agendas, user-friendly budgets, district policies, course documents, student services, and a direct confirmation that the address information is current.",
        ],
        "transit_heading": "Compare New Providence and Murray Hill as separate station routines",
        "transit": [
            "NJ TRANSIT places both stations within New Providence and lists each on the Morris & Essex system. New Providence Station and Murray Hill Station have different locations and parking arrangements. Open both official records and the current schedule before deciding which station is relevant to a property.",
            "Build two complete routes: front door to platform, the scheduled rail trip, and the destination-side segment. Confirm parking eligibility and payment with the named operator, and recheck evenings or weekends if applicable. This approach is more useful than publishing one borough-wide commute duration.",
        ],
        "transit_cards": [
            ("New Providence Station", "Review the official Springfield Avenue/Pittsford Way station page, current alerts, and the applicable parking information.", "https://www.njtransit.com/station/new-providence-station"),
            ("Murray Hill Station", "Review the separate Foley Place station page and verify which parking arrangement and walking route fit the address.", "https://www.njtransit.com/station/murray-hill-station"),
            ("Schedule validation", "Use NJ TRANSIT's current schedule for the intended date and direction; do not assume every train pattern or transfer remains constant.", "https://www.njtransit.com/schedules-and-fares/"),
        ],
        "civic_heading": "New Providence facilities and local-government access",
        "civic": [
            "The borough's facilities directory lists Centennial Park, the Recreation Offices and Municipal Center gym, Becton Dickinson Field, and other public locations. Use each facility page to verify address, reservation status, rules, and current availability. A facility listing does not promise a program or unrestricted access.",
            "For local policy, the borough publishes council records and an ordinance page that flags recent zoning action. When a proposed use or nearby change matters, read the ordinance text and planning record and ask the responsible department how the current law applies. Avoid relying on an archived copy detached from later amendments.",
        ],
        "civic_links": [
            ("New Providence facilities", "https://www.newprov.us/Facilities"),
            ("Mayor and Borough Council", "https://www.newprov.us/404/Mayor-Borough-Council"),
            ("Borough ordinances", "https://www.newprov.us/260/Borough-Ordinances"),
        ],
        "diligence_heading": "New Providence assessment and ordinance checks",
        "diligence_intro": "The assessor and ordinance archive answer different questions. Use both, plus permit and professional review, for the exact parcel.",
        "diligence": [
            ("Assessment and ownership", "Use the Tax Assessor's property-search resources for parcel identity, assessment, ownership, tax-map, and appeal information."),
            ("Current tax bill", "Confirm the billed amount and any added assessment with the responsible borough office; avoid estimating from assessment alone."),
            ("Zoning law", "Review the current ordinance and mapped district, then obtain an official response for a proposed addition, use, subdivision, or exterior change."),
            ("Station and school", "Verify the intended station routine and district assignment separately; neither is established by a listing's neighborhood description."),
        ],
        "checklist_title": "A New Providence buyer-and-seller decision checklist",
        "steps": [
            ("Run the two-station test", "Map and travel the route to New Providence Station and Murray Hill Station, then check the schedules and parking rules that match the routine."),
            ("Match public records", "Connect the address to the block and lot, assessment, tax map, permit history, current ordinance, and any prior land-use approval."),
            ("Confirm district details", "Use the district for assignment, registration, transportation, programs, and redistricting information for the applicable year."),
            ("Prepare the transaction file", "Buyers can log verified constraints and inspection findings; sellers can assemble the survey, permits, invoices, tax record, and disclosures."),
        ],
        "faqs": [
            ("How many NJ TRANSIT stations are in New Providence?", "NJ TRANSIT maintains separate pages for New Providence Station and Murray Hill Station. Compare their current schedules, access, and parking from the specific property."),
            ("Which public schools does the district list?", "The district lists Allen W. Roberts and Salt Brook elementary schools, New Providence Middle School, and New Providence High School. Confirm assignment and registration directly with the district."),
            ("Where can I research a New Providence assessment?", "The Borough Tax Assessor page links property search, tax maps, assessment appeals, ownership information, and taxpayer guidance for parcel-level research."),
            ("How do I check current New Providence zoning rules?", "Use the Borough ordinance archive and mapped district, then ask the responsible office to apply the current rules and any prior approvals to the exact project and parcel."),
            ("Should I rely on a listing's station name?", "No. Test both official station options from the address, review parking eligibility and current schedules, and use the route that matches the actual travel pattern."),
        ],
        "nearby": [("Berkeley Heights", "berkeley-heights"), ("Summit", "summit"), ("Springfield", "springfield"), ("Chatham", "chatham"), ("Westfield", "westfield")],
    },
    "berkeley-heights": {
        "name": "Berkeley Heights",
        "postal": "07922",
        "title": "Berkeley Heights NJ Real Estate Research | Jorge Ramirez",
        "description": "Research Berkeley Heights, NJ real estate with official links for rail, schools, Snyder Park, zoning, tree permits, flood maps, wetlands, and parcel records.",
        "hero": "An official-source guide to Berkeley Heights Station, district campuses, Snyder Avenue Park, zoning and tree review, flood maps, wetlands, and block-and-lot research.",
        "image": (
            "/images/towns/berkeley-heights-1.webp", "1280", "960",
            "Berkeley Heights NJ Transit station platform in Berkeley Heights, New Jersey",
            "Berkeley Heights NJ Transit station", "SeichanGant",
            "https://commons.wikimedia.org/wiki/File:Berkeley_Heights_Train_Station,_2.jpg",
            "CC BY-SA 4.0", "https://creativecommons.org/licenses/by-sa/4.0/",
        ),
        "orientation_title": "Berkeley Heights research crosses township, county, and school records",
        "orientation": [
            "The township's existing-conditions plan describes Berkeley Heights as a Union County municipality with a mayor-and-council form and local departments at Town Hall. Planning documents provide useful context, but parcel decisions still belong in current zoning, engineering, assessment, and permit records.",
            "Berkeley Heights Station is on NJ TRANSIT's Morris & Essex system near Sherman and Plainfield avenues. The township also includes county-managed recreation land. Snyder Avenue Park, for example, is identified as county-owned while the local Recreation Commission and Public Works Department have stated maintenance roles. Agency boundaries matter when verifying a rule or facility.",
        ],
        "orientation_cards": [
            ("Station source", "NJ TRANSIT maintains Berkeley Heights Station line, advisory, ticketing, bicycle, and parking information."),
            ("District structure", "Berkeley Heights Public Schools lists local PreK–8 campuses and Governor Livingston High School, including its Mountainside sending relationship."),
            ("Park ownership", "The township facility page identifies Snyder Avenue Park as county-owned and explains local maintenance responsibilities."),
            ("Parcel constraints", "Township offices separately handle zoning, tree permits, flood maps, wetlands maps, block and lot, building permits, and development questions."),
        ],
        "facts_heading": "Berkeley Heights facts come from several responsible offices",
        "facts_intro": "Use the official department directory to route each parcel question instead of expecting one page or person to answer everything.",
        "facts": [
            ("Local planning", "Township existing-conditions plan", "Government, land-use, conservation, and transportation context", "https://www.berkeleyheights.gov/DocumentCenter/View/6577/Master-Plan-2022_Exist-Conditions-Vol-1"),
            ("Train service", "Berkeley Heights Station", "Morris & Essex system station and parking information", "https://www.njtransit.com/station/berkeley-heights-station"),
            ("School research", "Berkeley Heights Public Schools", "District campuses and high-school sending relationship", "https://www.bhpsnj.org/page/district-home"),
            ("Question routing", "Responsible Department", "Zoning, flood, wetlands, block-and-lot, and permit contacts", "https://www.berkeleyheights.gov/265/Responsible-Department"),
        ],
        "schools_heading": "Berkeley Heights district research and the Mountainside relationship",
        "schools": [
            "Berkeley Heights Public Schools lists Mary Kay McMillin, William Woodruff, Thomas P. Hughes, Mountain Park, Columbia Middle School, and Governor Livingston High School. The district also states that students from Mountainside join Berkeley Heights students at Governor Livingston for high school. That regional relationship is a fact to understand when reviewing district records.",
            "Use the district for current assignment, registration, transportation, boundaries, board records, and program details. Then use NJDOE School Performance Reports for state-published measures with the report year and definitions in view. Neither source supports turning a school or district into a one-word real-estate claim.",
        ],
        "transit_heading": "Berkeley Heights Station and parcel-to-platform planning",
        "transit": [
            "NJ TRANSIT places Berkeley Heights Station near Sherman Avenue and Plainfield Avenue on the Morris & Essex system. The station page identifies municipal and NJ TRANSIT parking areas and publishes current advisories. Operator, permit, accessibility, and ticketing details should be rechecked for the intended date.",
            "The useful comparison begins at the target driveway. Account for the route to the station, a verified parking or drop-off plan, the current schedule, and the destination-side connection. Repeat the check for any secondary travel pattern rather than assigning one fixed commute description to the entire township.",
        ],
        "transit_cards": [
            ("Official station page", "Review the current Berkeley Heights Station record and linked alerts before relying on saved parking or service information.", "https://www.njtransit.com/station/berkeley-heights-station"),
            ("Two parking owners", "NJ TRANSIT identifies both municipal and agency-owned parking. Confirm the rule for the actual lot and intended user.", "https://www.njtransit.com/station/berkeley-heights-station"),
            ("Walk and road context", "Use the exact property route and current township information; municipality-wide distance language does not establish daily access.", "https://www.berkeleyheights.gov/265/Responsible-Department"),
        ],
        "civic_heading": "Snyder Avenue Park and public-space verification",
        "civic": [
            "The township's Snyder Avenue Park facility page lists field sports, a playground with spray area, and other facility details. It also states that Union County owns the park, while local recreation and public works participate in maintenance. Check current rules, field status, and reservations with the responsible agency before relying on an amenity.",
            "Berkeley Heights' official planning material also identifies a broader mix of municipal and county open space. Boundaries, trail conditions, and allowed uses are property- and facility-specific. Use the township and county records for the named location rather than assuming a nearby wooded parcel is public or accessible.",
        ],
        "civic_links": [
            ("Snyder Avenue Park facility page", "https://www.berkeleyheights.gov/Facilities/Facility/Details/Snyder-Avenue-Park-9"),
            ("Township existing-conditions plan", "https://www.berkeleyheights.gov/DocumentCenter/View/6577/Master-Plan-2022_Exist-Conditions-Vol-1"),
            ("Township department directory", "https://www.berkeleyheights.gov/265/Responsible-Department"),
        ],
        "diligence_heading": "Berkeley Heights zoning, tree, flood, and wetlands checks",
        "diligence_intro": "The township routes these subjects to different offices. Start with a survey and block-and-lot identity, then ask each responsible office the narrow question it maintains.",
        "diligence": [
            ("Zoning and coverage", "Use the current map and regulations for setbacks, building coverage, other coverage, structures, additions, pools, patios, decks, walls, and fences."),
            ("Tree removal", "The Zoning and Tree Inspections office publishes current permit rules. Verify whether a proposed removal or right-of-way tree requires approval."),
            ("Flood and wetlands maps", "The township directory routes flood-map questions to Engineering and identifies wetlands-map responsibility. Review both when site conditions warrant."),
            ("Block, lot, and permits", "Confirm the tax parcel, assessment record, survey, easements, open permits, and any planning or zoning-board resolution before designing work."),
        ],
        "checklist_title": "A Berkeley Heights buyer-and-seller decision checklist",
        "steps": [
            ("Route every question", "Create separate entries for zoning, engineering, tree, building, tax, school, transit, and park issues and contact the office listed by the Township."),
            ("Review the land", "Match the survey to zoning, coverage, easements, slopes, drainage, flood and wetlands information, and the intended work before pricing a project."),
            ("Confirm shared relationships", "Verify station parking ownership, county versus township park responsibility, and the district's school arrangement for the address."),
            ("Document before market", "Buyers can retain source dates and professional findings; sellers can assemble approvals, permits, survey, assessment, repair records, and disclosures."),
        ],
        "faqs": [
            ("Which rail system serves Berkeley Heights Station?", "NJ TRANSIT lists Berkeley Heights Station on the Morris & Essex system. Check the official station page and current schedule for service, parking, and alerts."),
            ("Which district serves Berkeley Heights public-school students?", "Berkeley Heights Public Schools lists the local campuses and states that Mountainside students join Berkeley Heights students at Governor Livingston High School. Confirm address details directly with the district."),
            ("Who owns Snyder Avenue Park?", "The Township facility page identifies Snyder Avenue Park as owned by Union County and describes local recreation and public-works maintenance roles. Confirm current use rules with the responsible agency."),
            ("Do tree removals require township review?", "The Zoning and Tree Inspections office publishes permit requirements for qualifying trees and right-of-way trees. Ask the office to apply the current ordinance to the specific tree and project."),
            ("Where do I ask about flood or wetlands maps?", "The Township Responsible Department directory routes flood-map and wetlands-map questions to the appropriate engineering or zoning contacts. Use the exact block, lot, and survey."),
        ],
        "nearby": [("New Providence", "new-providence"), ("Summit", "summit"), ("Fanwood", "fanwood"), ("Mountainside", "mountainside"), ("Springfield", "springfield")],
    },
    "springfield": {
        "name": "Springfield",
        "postal": "07081",
        "title": "Springfield NJ Real Estate Research | Jorge Ramirez",
        "description": "Research Springfield, NJ real estate with official links for Route 114 and jitney transit, public schools, parks, zoning, surveys, permits, taxes, and parcel checks.",
        "hero": "A verified guide to Springfield's bus and jitney connections, public-school campuses, Township records, county parks, zoning submissions, and property research.",
        "image": (
            "/images/towns/springfield-1.webp", "1280", "960",
            "Interstate 78 in Springfield Township, Union County, New Jersey",
            "Interstate 78 in Springfield Township", "Famartin",
            "https://commons.wikimedia.org/wiki/File:2021-07-06_15_21_17_View_east_along_Interstate_78_(Phillipsburg-Newark_Expressway)_from_the_overpass_for_Union_County_Route_636_(Shunpike_Road)_in_Springfield_Township,_Union_County,_New_Jersey.jpg",
            "CC BY-SA 4.0", "https://creativecommons.org/licenses/by-sa/4.0/",
        ),
        "orientation_title": "Springfield transportation research begins with bus and jitney sources",
        "orientation": [
            "Springfield publishes Township Committee, Planning Board, and Board of Adjustment meeting records on its municipal site. Those records are the place to trace ordinances, public applications, and official action that may affect a parcel or nearby corridor.",
            "The official sources reviewed for this guide identify two distinct transit options: NJ TRANSIT Route 114 includes a Springfield stop at Morris Avenue and Morris Road, and the Township publishes a local park-and-ride jitney connection from the community pool lot to Short Hills Station. Both require current schedule and service-status checks; neither should be described by a guaranteed travel duration.",
        ],
        "orientation_cards": [
            ("Route 114", "NJ TRANSIT's official timetable identifies the Springfield stop and publishes the schedule notes that apply to each trip."),
            ("Township jitney", "Springfield maintains the service page for its community-pool-lot connection to Short Hills Station and posts local updates there."),
            ("Public boards", "Township Committee, Planning Board, and Board of Adjustment records help verify adopted action and parcel applications."),
            ("County parks", "Union County's directory identifies Washington Avenue Park and includes Springfield among the municipalities connected to Watchung Reservation."),
        ],
        "facts_heading": "Springfield research by service and responsible agency",
        "facts_intro": "Bus, jitney, school, land-use, and park information comes from different public publishers. Keep the source attached to the fact.",
        "facts": [
            ("Municipal record", "Township meetings", "Committee, Planning Board, and Board of Adjustment materials", "https://springfield-nj.us/meetings/"),
            ("Bus service", "NJ TRANSIT Route 114", "Official timetable and Springfield stop listing", "https://content.njtransit.com/sites/default/files/bus_schedules/T1114.pdf"),
            ("Rail connection", "Township jitney", "Local connection to Short Hills Station and service updates", "https://springfield-nj.us/jitney/"),
            ("School research", "Springfield Public Schools", "Official early-childhood through high-school campus list", "https://www.springfieldschools.com/schools"),
        ],
        "schools_heading": "Springfield public-school research by campus and attendance zone",
        "schools": [
            "Springfield Public Schools lists Edward V. Walton Early Childhood Center, James Caldwell and Thelma L. Sandmeier elementary schools, Florence M. Gaudineer Middle School, and Jonathan Dayton High School. The district's registration material also links attendance-zone information. Verify the address, placement, registration, and transportation rules directly with the district.",
            "NJDOE School Performance Reports provide official state data by school and district. Use the report's definitions, year, and individual measures, and pair them with board records, budgets, program materials, student services, and direct district questions. This page does not assign a rank or subjective label to a school or attendance area.",
        ],
        "transit_heading": "Springfield's Route 114 and Short Hills jitney research",
        "transit": [
            "NJ TRANSIT's Route 114 timetable identifies a Springfield stop at Morris Avenue and Morris Road. The published timetable is the source for current trip patterns, stops, and service notes. Confirm the travel date in NJ TRANSIT's current tools because printed schedules can be replaced.",
            "The Township separately publishes a park-and-ride jitney from the community pool parking lot to Short Hills Station. Check the municipal page for rider forms, fees, schedule changes, and service notices. Then test the full route from the property, including the trip to the pickup point and the rail connection.",
        ],
        "transit_cards": [
            ("NJ TRANSIT Route 114", "Read the current official timetable and verify the Morris Avenue/Morris Road stop for the trip and direction needed.", "https://content.njtransit.com/sites/default/files/bus_schedules/T1114.pdf"),
            ("Springfield jitney", "Use the Township page for the community pool lot connection and check any posted schedule or service update before relying on it.", "https://springfield-nj.us/jitney/"),
            ("Door-to-door test", "Include local pickup access, schedule alignment, transfer, parking or fare requirements, and the destination-side segment.", "https://www.njtransit.com/schedules-and-fares/"),
        ],
        "civic_heading": "Springfield parks and civic meeting records",
        "civic": [
            "Union County's official parks directory lists Washington Avenue Park in Springfield and identifies Springfield among the municipalities associated with Watchung Reservation. Check the named facility's current activities, rules, parking, closures, and reservation information with the county rather than treating the broader reservation as a uniform amenity at every address.",
            "The municipal calendar and meetings page cover the Township Committee and land-use boards. If a buyer or seller is tracking a nearby application, search the agenda, exhibits, resolution, and minutes. Ask the Township for the current status and do not treat a hearing, conceptual plan, or old report as proof that work will occur.",
        ],
        "civic_links": [
            ("Union County parks directory", "https://ucnj.org/parks-activities/"),
            ("Springfield meeting records", "https://springfield-nj.us/meetings/"),
            ("Springfield municipal calendar", "https://springfield-nj.us/calendar/"),
        ],
        "diligence_heading": "Springfield zoning submissions and parcel records",
        "diligence_intro": "Springfield's zoning form shows why a survey and exact project scope matter. Verify requirements with current municipal staff before work or negotiation.",
        "diligence": [
            ("Survey-based review", "The municipal application asks for a property survey with proposed work shown to scale. Use a current survey and complete scope for the official question."),
            ("Prior board action", "Check whether the premises has prior Planning Board or Board of Adjustment action and obtain the resolution and approved plans when applicable."),
            ("Permit and office check", "Confirm zoning, engineering, building, code, tax-assessor, and tax-collector records with the offices identified in the current municipal guide."),
            ("Transit and attendance zone", "Verify Route 114 or jitney use from the property and confirm the school attendance zone directly with Springfield Public Schools."),
        ],
        "checklist_title": "A Springfield buyer-and-seller decision checklist",
        "steps": [
            ("Choose the actual transit path", "Test Route 114, the jitney-to-Short-Hills option, driving, or another route with current schedules and the exact property origin."),
            ("Trace the land-use file", "Match the block and lot, survey, zoning submission, permits, board resolutions, and current municipal record for additions or altered uses."),
            ("Verify public-service facts", "Use the district for attendance zones, Union County for county parks, and the Township for local facilities and meeting action."),
            ("Prepare before negotiation", "Buyers can price verified condition and constraints; sellers can organize permits, survey, tax records, repairs, and disclosures before launch."),
        ],
        "faqs": [
            ("What official transit sources cover Springfield?", "NJ TRANSIT's Route 114 timetable identifies a Springfield stop, and the Township publishes a separate jitney connection to Short Hills Station. Check both for current service details."),
            ("Does this guide promise a commute time?", "No. Timetables, transfers, traffic, pickup access, and service notices vary. Build the exact route in current official tools for the date and destination involved."),
            ("Which schools does Springfield Public Schools list?", "The district lists an early-childhood center, two elementary schools, a middle school, and Jonathan Dayton High School. Confirm the attendance zone and registration directly with the district."),
            ("Why is a survey important for Springfield zoning?", "The municipal zoning application asks applicants to show proposed work on a scaled property survey. The official review also considers the scope and any prior land-use-board action."),
            ("Where can I check Springfield parks?", "Union County's official directory identifies county park locations and activities, including Washington Avenue Park and Watchung Reservation context. Verify current facility rules with the County or Township as appropriate."),
        ],
        "nearby": [("Summit", "summit"), ("Millburn", "millburn"), ("Union", "union"), ("Mountainside", "mountainside"), ("New Providence", "new-providence")],
    },
}


def anchor(url: str, label: str) -> str:
    return (
        f'<a href="{html.escape(url, quote=True)}" target="_blank" rel="noopener" '
        f'style="color:#8A6D14;text-decoration:underline;text-underline-offset:3px;">'
        f"{html.escape(label)}</a>"
    )


def render_main(slug: str, town: dict) -> str:
    name = town["name"]
    (
        image_url,
        width,
        height,
        image_alt,
        image_subject,
        image_artist,
        image_source_url,
        image_license,
        image_license_url,
    ) = town["image"]
    image_caption = (
        f"{html.escape(image_subject)}. Photo: {html.escape(image_artist)} via "
        f'{anchor(image_source_url, "Wikimedia Commons")}; '
        f'{anchor(image_license_url, image_license)}, resized to WebP.'
    )
    cards = "\n".join(
        f'''          <article class="neighborhood-card">
            <h3>{html.escape(title)}</h3>
            <p>{html.escape(body)}</p>
          </article>'''
        for title, body in town["orientation_cards"]
    )
    facts = "\n".join(
        f'''          <article class="snapshot-card">
            <h3>{html.escape(label)}</h3>
            <p class="snapshot-value" style="font-size:1.2rem;">{html.escape(value)}</p>
            <p class="snapshot-label">{html.escape(body)}</p>
            <p style="margin-top:14px;">{anchor(url, "Open official source →")}</p>
          </article>'''
        for label, value, body, url in town["facts"]
    )
    transit_cards = "\n".join(
        f'''          <article class="commute-card">
            <h3>{html.escape(title)}</h3>
            <p>{html.escape(body)}</p>
            <p style="margin-top:12px;">{anchor(url, "Verify with the publisher →")}</p>
          </article>'''
        for title, body, url in town["transit_cards"]
    )
    civic_links = "\n".join(
        f"          <li>{anchor(url, label)}</li>" for label, url in town["civic_links"]
    )
    diligence = "\n".join(
        f'''          <article class="neighborhood-card">
            <h3>{html.escape(title)}</h3>
            <p>{html.escape(body)}</p>
          </article>'''
        for title, body in town["diligence"]
    )
    steps = "\n".join(
        f'''          <article class="process-step">
            <div class="step-number">{number}</div>
            <h3>{html.escape(title)}</h3>
            <p>{html.escape(body)}</p>
          </article>'''
        for number, (title, body) in enumerate(town["steps"], start=1)
    )
    faqs = "\n".join(
        f'''          <article class="faq-item">
            <h3>{html.escape(question)}</h3>
            <p>{html.escape(answer)}</p>
          </article>'''
        for question, answer in town["faqs"]
    )
    sources = MANIFEST["towns"][slug]["sources"]
    source_items = "\n".join(
        f'''          <li>
            {anchor(source["url"], source["publisher"])}
            <span style="display:block;color:#666;font-size:.9rem;">{html.escape(source["fact_supported"])}</span>
          </li>'''
        for source in sources
    )

    return f'''<main id="main">
  <section class="hero">
    <div class="hero-inner">
      <p class="hero-county">Union County · Official-source local guide</p>
      <h1>Real Estate Research in <span>{html.escape(name)}, NJ</span></h1>
      <p class="hero-tagline">{html.escape(town["hero"])}</p>
      <div class="hero-ctas">
        <a href="/property-search" class="btn btn-primary">Search Current Listings</a>
        <a href="/home-valuation" class="btn btn-secondary">Request a Home Valuation</a>
      </div>
      <p style="margin-top:18px;color:rgba(255,255,255,.72);font-size:.88rem;">Last reviewed August 25, 2026 · Verify time-sensitive details with the linked official publisher.</p>
    </div>
  </section>

  <section class="neighborhoods">
    <div class="container">
      <figure class="article-figure"><img src="{image_url}" alt="{html.escape(image_alt)}" width="{width}" height="{height}" loading="lazy" decoding="async"><figcaption>{image_caption}</figcaption></figure>
      <h2>{html.escape(town["orientation_title"])}</h2>
      {''.join(f'<p>{html.escape(paragraph)}</p>' for paragraph in town['orientation'])}
      <div class="neighborhoods-grid" style="margin-top:28px;">
{cards}
      </div>
    </div>
  </section>

  <section class="market-snapshot">
    <div class="container">
      <h2>{html.escape(town["facts_heading"])}</h2>
      <p style="max-width:820px;margin:-20px 0 32px;">{html.escape(town["facts_intro"])}</p>
      <div class="snapshot-grid">
{facts}
      </div>
    </div>
  </section>

  <section class="schools">
    <div class="container">
      <h2>{html.escape(town["schools_heading"])}</h2>
      {''.join(f'<p>{html.escape(paragraph)}</p>' for paragraph in town['schools'])}
      <p style="margin-top:20px;">{anchor(next(source['url'] for source in sources if source['category'] == 'schools' and 'nj.gov' not in source['url']), 'Open the official district source →')} &nbsp; {anchor('https://www.nj.gov/education/schoolperformance/', 'Search NJDOE School Performance Reports →')}</p>
    </div>
  </section>

  <section class="commute">
    <div class="container">
      <h2>{html.escape(town["transit_heading"])}</h2>
      {''.join(f'<p>{html.escape(paragraph)}</p>' for paragraph in town['transit'])}
      <div class="commute-grid" style="margin-top:28px;">
{transit_cards}
      </div>
    </div>
  </section>

  <section class="neighborhoods">
    <div class="container">
      <h2>{html.escape(town["civic_heading"])}</h2>
      {''.join(f'<p>{html.escape(paragraph)}</p>' for paragraph in town['civic'])}
      <ul style="margin:22px 0 0 22px;display:grid;gap:10px;">
{civic_links}
      </ul>
    </div>
  </section>

  <section class="schools">
    <div class="container">
      <h2>{html.escape(town["diligence_heading"])}</h2>
      <p>{html.escape(town["diligence_intro"])}</p>
      <div class="neighborhoods-grid" style="margin-top:28px;">
{diligence}
      </div>
      <p style="margin-top:24px;padding:20px 24px;background:#FAFAF8;border-left:3px solid #8A6D14;"><strong>Verification note:</strong> Confirm current taxes, assessment, zoning, permits, flood or wetlands status, transit, and school assignment with the official agency and qualified professionals. This guide is informational and is not legal, tax, engineering, insurance, inspection, or school-placement advice.</p>
    </div>
  </section>

  <section class="process">
    <div class="container">
      <h2>{html.escape(town["checklist_title"])}</h2>
      <p>Keep the source date and parcel identifier beside every material fact so the transaction team can recheck it before a deadline.</p>
      <div class="process-steps">
{steps}
      </div>
    </div>
  </section>

  <section class="faq">
    <div class="container">
      <h2>{html.escape(name)} research questions</h2>
      <div class="faq-grid">
{faqs}
      </div>
    </div>
  </section>

  <section class="cta-final">
    <div class="container">
      <h2>Need property-specific help in {html.escape(name)}?</h2>
      <p>Jorge Ramirez can help organize a current listing or sale analysis while municipal, district, transit, and professional sources answer the questions they control.</p>
      <div class="cta-buttons">
        <a href="tel:908-230-7844" class="btn btn-primary btn-large">Call (908) 230-7844</a>
        <a href="/contact" class="btn btn-secondary btn-large">Send a Message</a>
        <a href="/home-valuation" class="btn btn-outline btn-large">Home Valuation</a>
      </div>
      <p class="cta-note">No-obligation conversation · Verify all property facts before acting</p>
    </div>
  </section>

  <section class="neighborhoods" aria-labelledby="sources-{slug}">
    <div class="container">
      <h2 id="sources-{slug}">Official sources reviewed</h2>
      <p>Accessed August 25, 2026. Links may publish newer information after this review, so open the source again when making a decision.</p>
      <ul style="margin:22px 0 0 22px;display:grid;gap:14px;">
{source_items}
      </ul>
      <p style="margin-top:24px;font-size:.9rem;color:#666;">Prepared by Jorge Ramirez · Licensed New Jersey Real Estate Agent #1754604 · Keller Williams Premier Properties.</p>
    </div>
  </section>
</main>'''


def render_schema(slug: str, town: dict) -> str:
    canonical = f"https://thejorgeramirezgroup.com/towns/{slug}"
    graph = [
        {
            "@type": "WebPage",
            "@id": canonical,
            "url": canonical,
            "name": town["title"],
            "description": town["description"],
            "dateModified": PAGE_MODIFIED_ON,
            "inLanguage": "en-US",
            "isPartOf": {"@type": "WebSite", "@id": "https://thejorgeramirezgroup.com/#website"},
            "publisher": {"@id": "https://thejorgeramirezgroup.com/#agent"},
            "about": {
                "@type": "Place",
                "name": f"{town['name']}, New Jersey",
                "address": {
                    "@type": "PostalAddress",
                    "addressLocality": town["name"],
                    "addressRegion": "NJ",
                    "postalCode": town["postal"],
                    "addressCountry": "US",
                },
            },
        },
        {
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Home", "item": "https://thejorgeramirezgroup.com/"},
                {"@type": "ListItem", "position": 2, "name": "Communities", "item": "https://thejorgeramirezgroup.com/communities"},
                {"@type": "ListItem", "position": 3, "name": town["name"], "item": canonical},
            ],
        },
        {
            "@type": "FAQPage",
            "mainEntity": [
                {
                    "@type": "Question",
                    "name": question,
                    "acceptedAnswer": {"@type": "Answer", "text": answer},
                }
                for question, answer in town["faqs"]
            ],
        },
    ]
    return json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False, separators=(",", ":"))


def replace_once(source: str, pattern: str, replacement: str, label: str, flags: int = 0) -> str:
    updated, count = re.subn(pattern, lambda _: replacement, source, count=1, flags=flags)
    if count != 1:
        raise RuntimeError(f"{label}: expected one replacement, found {count}")
    return updated


def preserve_local_search_pathway(rendered_main: str, source: str) -> str:
    """Keep the separately managed local-search block across a page rebuild."""
    pathway_match = re.search(
        r"[ \t]*<!-- local-search-pathways:start -->.*?"
        r"<!-- local-search-pathways:end -->\n?",
        source,
        flags=re.S,
    )
    if not pathway_match:
        return rendered_main
    return rendered_main.replace(
        "</main>", pathway_match.group(0).rstrip() + "\n</main>", 1
    )


def rebuild(slug: str, town: dict) -> None:
    path = ROOT / "towns" / f"{slug}.html"
    source = path.read_text(encoding="utf-8")
    canonical = f"https://thejorgeramirezgroup.com/towns/{slug}"
    source = replace_once(source, r"<title>.*?</title>", f"<title>{html.escape(town['title'])}</title>", f"{slug} title", re.S)
    source = replace_once(source, r'<meta name="description" content="[^"]*">', f'<meta name="description" content="{html.escape(town["description"], quote=True)}">', f"{slug} description")
    source = re.sub(
        r'<meta name="keywords" content="[^"]*">',
        f'<meta name="keywords" content="{html.escape(town["name"], quote=True)} NJ real estate, {html.escape(town["name"], quote=True)} NJ homes, Union County property research">',
        source,
        count=1,
    )
    source = replace_once(source, r'<meta property="og:title" content="[^"]*">', f'<meta property="og:title" content="{html.escape(town["title"], quote=True)}">', f"{slug} og title")
    source = replace_once(source, r'<meta property="og:description" content="[^"]*">', f'<meta property="og:description" content="{html.escape(town["description"], quote=True)}">', f"{slug} og description")
    source = replace_once(source, r'<meta name="twitter:title" content="[^"]*">', f'<meta name="twitter:title" content="{html.escape(town["title"], quote=True)}">', f"{slug} twitter title")
    source = replace_once(source, r'<meta name="twitter:description" content="[^"]*">', f'<meta name="twitter:description" content="{html.escape(town["description"], quote=True)}">', f"{slug} twitter description")
    source = replace_once(source, r'<meta name="ai-content-declaration" content="[^"]*">', f'<meta name="ai-content-declaration" content="Source-backed {html.escape(town["name"], quote=True)} local research using municipal, county, NJ TRANSIT, district, and NJDOE sources reviewed 2026-08-25.">', f"{slug} AI declaration")
    source = replace_once(source, r'<meta name="llm-context" content="[^"]*">', f'<meta name="llm-context" content="{html.escape(town["name"], quote=True)} is a Union County, New Jersey municipality. This page links the responsible public sources for transit, schools, civic resources, zoning, and parcel due diligence and avoids market or ranking claims.">', f"{slug} llm context")
    source = re.sub(r'^\s*<meta name="geo\.(?:region|placename|position)"[^>]*>\s*$', "", source, flags=re.M)
    source = re.sub(r'^\s*<meta name="ICBM"[^>]*>\s*$', "", source, flags=re.M)
    source = replace_once(source, r'<script type="application/ld\+json">.*?</script>', f'<script type="application/ld+json">{render_schema(slug, town)}</script>', f"{slug} schema", re.S)
    rendered_main = preserve_local_search_pathway(render_main(slug, town), source)
    source = replace_once(
        source,
        r'<main id="main">.*?</main>',
        rendered_main,
        f"{slug} main",
        re.S,
    )

    related_items = "\n".join(
        f'        <li><a href="/towns/{nearby_slug}">{html.escape(nearby_name)} NJ Real Estate Research</a></li>'
        for nearby_name, nearby_slug in town["nearby"]
    )
    related = f'''<section class="related-pages">
    <div class="container">
      <h2>Explore Nearby Union County and NJ Communities</h2>
      <ul>
{related_items}
      </ul>
      <p>
        <a href="/communities">Explore all community guides</a>
        <a href="/property-search">Search current listings</a>
        <a href="/home-valuation">Request a home valuation</a>
        <a href="/contact">Contact Jorge Ramirez</a>
      </p>
    </div>
  </section>'''
    source = replace_once(source, r'<section class="related-pages">.*?</section>', related, f"{slug} related pages", re.S)
    source = re.sub(r'\n?<!-- JR-MARKET-TABLE-v1 -->\s*<section\b.*?</section>', "", source, count=1, flags=re.S)
    path.write_text(source, encoding="utf-8")


def main() -> None:
    manifest_slugs = set(MANIFEST["towns"])
    if manifest_slugs != set(TOWNS):
        raise RuntimeError(f"manifest/content mismatch: {manifest_slugs ^ set(TOWNS)}")
    for slug, town in TOWNS.items():
        manifest_urls = {source["url"] for source in MANIFEST["towns"][slug]["sources"]}
        rendered = render_main(slug, town)
        missing = sorted(url for url in manifest_urls if html.escape(url, quote=True) not in rendered)
        if missing:
            raise RuntimeError(f"{slug}: manifest sources not rendered: {missing}")
        rebuild(slug, town)
        print(f"rebuilt towns/{slug}.html")


if __name__ == "__main__":
    main()
