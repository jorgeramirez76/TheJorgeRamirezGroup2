const communitiesData = {
  "Essex": [
    {
      "town": "Maplewood",
      "description": "Beloved village with Midtown Direct trains and an artsy, inclusive vibe.",
      "schools": "Part of the South Orange-Maplewood School District, known for diversity, strong arts, and IB programs.",
      "primary_transit": "NJ Transit Morris & Essex Line from Maplewood Station with Midtown Direct service.",
      "commute_to_nyc": "Direct trains to New York Penn often in the 30–40 minute range, plus walk/drive to the station.",
      "highways": "Access to I-78, Garden State Parkway, and nearby Route 24.",
      "notes": "Popular with Brooklyn transplants seeking a walkable downtown and community events."
    },
    {
      "town": "Millburn",
      "description": "Prestigious commuter town with top-ranked schools, luxury homes, and Midtown Direct trains.",
      "schools": "Millburn Township Public Schools are consistently ranked among the best in New Jersey.",
      "primary_transit": "NJ Transit Morris & Essex Line from Millburn and Short Hills stations with Midtown Direct to NYC.",
      "commute_to_nyc": "Trains to New York Penn typically 30–40 minutes, making it one of the most desirable NYC suburbs.",
      "highways": "Close to Route 24, I-78, and the Garden State Parkway.",
      "notes": "Home to the Mall at Short Hills and upscale residential neighborhoods."
    },
    {
      "town": "Montclair",
      "description": "Trendy township with vibrant arts, diverse neighborhoods, and Midtown train service.",
      "schools": "Montclair Public Schools feature a magnet system with strong arts and academic programs.",
      "primary_transit": "Multiple NJ Transit Montclair-Boonton Line stations plus DeCamp/NYC buses (service patterns subject to change).",
      "commute_to_nyc": "Typical trips 35–55 minutes to Midtown via train or bus depending on origin station and transfers.",
      "highways": "Near the Garden State Parkway, Route 3, and Route 46.",
      "notes": "Active restaurant scene, music venues, and Montclair State University help sustain demand."
    },
    {
      "town": "North Caldwell",
      "description": "Upscale borough with luxury homes, top schools, and suburban tranquility.",
      "schools": "North Caldwell students attend North Caldwell School District (K–6) and West Essex Regional School District (7–12).",
      "primary_transit": "Commuters typically use buses along Bloomfield Avenue or drive to nearby rail/PATH access.",
      "commute_to_nyc": "Door-to-door Midtown commutes often 45–75 minutes via bus or park-and-ride.",
      "highways": "Access to I-280, Garden State Parkway, and Route 23 via nearby corridors.",
      "notes": "Large homes and quiet streets appeal to move-up buyers."
    },
    {
      "town": "Nutley",
      "description": "Family-friendly township with strong schools, parks, and proximity to NYC.",
      "schools": "Nutley Public Schools provide K–12 education with neighborhood schools and AP offerings.",
      "primary_transit": "NJ Transit buses to Newark and NYC; some residents use nearby rail or light rail connections.",
      "commute_to_nyc": "Many commuters travel 45–75 minutes via bus/rail combinations to Midtown.",
      "highways": "Close to Route 3, Route 21, and the Garden State Parkway.",
      "notes": "Parks along the Third River and tree-lined streets provide a classic suburban feel."
    },
    {
      "town": "Orange",
      "description": "Historic urban-suburban city with direct Midtown train service.",
      "schools": "Orange Public School District serves K–12 students with urban amenities and improving test scores.",
      "primary_transit": "NJ Transit Morris & Essex Line provides Midtown Direct service from Orange Station.",
      "commute_to_nyc": "Express trains to New York Penn about 25–35 minutes during peak times.",
      "highways": "I-280 and Garden State Parkway are both close by.",
      "notes": "Historically significant architecture and active redevelopment projects."
    },
    {
      "town": "Roseland",
      "description": "Compact suburban borough known for corporate office parks.",
      "schools": "Roseland Public Schools (K–8), with high schoolers typically attending West Essex Regional.",
      "primary_transit": "Primarily a car-commute town, but some buses and nearby train stations in neighboring areas.",
      "commute_to_nyc": "Often 45–75 minutes depending on whether you take bus or drive-to-train.",
      "highways": "Route 280 access makes it easy to reach nearby stations or the city.",
      "notes": "Office parks and corporate headquarters make this more of a business hub."
    },
    {
      "town": "South Orange",
      "description": "Vibrant village with Seton Hall University, great restaurants, and Midtown Direct trains.",
      "schools": "South Orange-Maplewood School District (combined with Maplewood), well-regarded for diversity and programs.",
      "primary_transit": "NJ Transit Morris & Essex Line with Midtown Direct service from South Orange Station.",
      "commute_to_nyc": "Express trains to New York Penn typically 25–35 minutes.",
      "highways": "Access to I-78, Route 24, and the Garden State Parkway.",
      "notes": "University presence keeps nightlife and restaurant scene energetic; strong local arts community."
    },
    {
      "town": "Verona",
      "description": "Small, friendly community centered on Verona Park, with easy highway access.",
      "schools": "Verona Public Schools (K–12) consistently rank well for academics and athletics.",
      "primary_transit": "Verona residents often drive to nearby train stations or take buses to Newark/NYC.",
      "commute_to_nyc": "Commutes via park-and-ride at nearby stations can be 40–60 minutes.",
      "highways": "Close to Route 23, I-280, and the Garden State Parkway.",
      "notes": "Verona Park offers boating, walking trails, and community events year-round."
    },
    {
      "town": "West Caldwell",
      "description": "Suburban township with great schools, family-friendly parks, and convenient highways.",
      "schools": "West Caldwell School District (K–8), then students attend James Caldwell High School.",
      "primary_transit": "Primarily a car town; residents drive to train or bus lines.",
      "commute_to_nyc": "Most commuters park-and-ride or bus to NYC, averaging 45–75 minutes.",
      "highways": "I-280 and Route 46 nearby.",
      "notes": "Stable neighborhoods and good parks, popular with families."
    },
    {
      "town": "West Orange",
      "description": "Diverse township with landmarks like Turtle Back Zoo, Thomas Edison National Park, and the South Mountain Reservation.",
      "schools": "West Orange Public Schools serve K–12 across multiple elementary, middle, and high school options.",
      "primary_transit": "Bus service to Newark/NYC, plus some residents drive to nearby train stations.",
      "commute_to_nyc": "Midtown commutes generally 45–75 minutes via bus or park-and-ride.",
      "highways": "I-280, Garden State Parkway, and Route 10 access.",
      "notes": "Large parks, suburban neighborhoods, and historic sites make this a well-rounded community."
    }
  ],
  "Hudson": [
    {
      "town": "Bayonne",
      "description": "Peninsula city with growing waterfront development and convenient Light Rail access to Jersey City/Hoboken.",
      "schools": "Bayonne Board of Education oversees public schools; some charter options available.",
      "primary_transit": "Hudson-Bergen Light Rail connects to Hoboken PATH; also buses to NYC.",
      "commute_to_nyc": "Light Rail to Hoboken PATH often takes 30–50 minutes total to Lower Manhattan or Midtown.",
      "highways": "Route 440, NJ Turnpike Extension (I-78), and Bayonne Bridge to Staten Island.",
      "notes": "More affordable than Hoboken/JC; waterfront redevelopment projects add appeal."
    },
    {
      "town": "East Newark",
      "description": "Tiny borough surrounded by Kearny and Harrison, mostly industrial.",
      "schools": "East Newark School District is small; some families send high schoolers to Kearny or Harrison.",
      "primary_transit": "PATH from nearby Harrison; NJ Transit buses and Harrison Station for rail.",
      "commute_to_nyc": "PATH from Harrison about 20–35 minutes to Lower Manhattan/Midtown.",
      "highways": "Route 1&9, Pulaski Skyway overhead.",
      "notes": "Limited residential inventory; historically industrial with some new housing developments."
    },
    {
      "town": "Guttenberg",
      "description": "Small, densely built borough on the Hudson River with stunning NYC skyline views.",
      "schools": "Guttenberg Public Schools; many families explore private/charter or neighboring district options.",
      "primary_transit": "NY Waterway Ferry to Midtown, plus extensive bus routes along Boulevard East.",
      "commute_to_nyc": "Ferries run about 10–20 minutes to Midtown; buses about 20–40 minutes depending on traffic.",
      "highways": "Route 495, Palisades Interstate Parkway nearby.",
      "notes": "Galaxy Towers and waterfront high-rises offer incredible views; parking can be tight."
    },
    {
      "town": "Harrison",
      "description": "Redeveloped waterfront town, home to Red Bull Arena.",
      "schools": "Harrison Public Schools; district serves K–12.",
      "primary_transit": "PATH Red Bull Arena station provides direct service to Newark and Lower Manhattan.",
      "commute_to_nyc": "PATH to World Trade Center about 20–35 minutes; PATH to Midtown via transfer in Jersey City.",
      "highways": "Route 1&9, NJ Turnpike, and I-280 nearby.",
      "notes": "Major League Soccer venue draws fans; waterfront housing developments expanding."
    },
    {
      "town": "Hoboken",
      "description": "Highly walkable, ultra-vibrant city with PATH trains, ferry, and NJ Transit rail.",
      "schools": "Hoboken Public Schools; many families also consider private or charter schools.",
      "primary_transit": "PATH trains to Lower Manhattan/Midtown (10–25 min), NJ Transit trains to Penn Station, NY Waterway Ferry.",
      "commute_to_nyc": "Among the fastest anywhere in NJ—PATH often under 20 minutes to Lower Manhattan.",
      "highways": "I-495, NJ Turnpike, and Route 1&9 nearby.",
      "notes": "High-end restaurants, bars, and nightlife; real estate prices among the highest in NJ."
    },
    {
      "town": "Jersey City",
      "description": "New Jersey's second-largest city, offering waterfront towers, PATH trains, and diverse neighborhoods.",
      "schools": "Jersey City Public Schools (large district) plus many charters; quality varies by school/area.",
      "primary_transit": "PATH trains (Journal Square, Grove Street, Exchange Place, Newport), Light Rail, ferries, buses.",
      "commute_to_nyc": "PATH often 10–20 minutes to Lower Manhattan or Midtown depending on station.",
      "highways": "NJ Turnpike, Route 1&9, Route 440, Pulaski Skyway.",
      "notes": "Waterfront living along the Hudson; Downtown JC is highly desirable for NYC commuters."
    },
    {
      "town": "Kearny",
      "description": "Industrial and residential town with improving riverfront areas.",
      "schools": "Kearny School District (K–12), neighborhood schools with a community focus.",
      "primary_transit": "PATH from Harrison or buses to Port Authority; NJ Transit trains also accessible.",
      "commute_to_nyc": "Via PATH or bus typically 30–50 minutes to Midtown.",
      "highways": "NJ Turnpike, Route 1&9, Pulaski Skyway.",
      "notes": "Known as 'Soccer Town USA'; more affordable housing compared to Hoboken/JC."
    },
    {
      "town": "North Bergen",
      "description": "Township on the Palisades with parks, residential neighborhoods, and NYC skyline views.",
      "schools": "North Bergen School District serves K–12; several schools across town.",
      "primary_transit": "NJ Transit buses along Bergenline Avenue to Port Authority; ferries from nearby towns.",
      "commute_to_nyc": "Buses about 20–45 minutes to Port Authority depending on traffic and route.",
      "highways": "I-495, Route 3, Palisades Interstate Parkway.",
      "notes": "James J. Braddock North Hudson County Park is a major recreational spot."
    },
    {
      "town": "Secaucus",
      "description": "Major transit hub with shopping outlets and wetlands along the Hackensack River.",
      "schools": "Secaucus Public Schools (K–12); compact district.",
      "primary_transit": "Secaucus Junction is a massive rail hub connecting multiple NJ Transit lines and Amtrak.",
      "commute_to_nyc": "Direct NJ Transit trains to Penn Station often 10–20 minutes.",
      "highways": "NJ Turnpike, Route 3, Route 495.",
      "notes": "Secaucus Outlet Mall and mega rail station define the area; some new residential."
    },
    {
      "town": "Union City",
      "description": "Dense, bustling city atop the Palisades with sweeping Manhattan views.",
      "schools": "Union City Board of Education runs public schools; diverse student population.",
      "primary_transit": "Extensive bus network along Bergenline Avenue to Port Authority; Light Rail accessible at northern border.",
      "commute_to_nyc": "Buses can be 15–35 minutes to Midtown depending on traffic.",
      "highways": "Route 495, Palisades Interstate Parkway nearby.",
      "notes": "One of the most densely populated municipalities in the U.S.; vibrant Latino culture."
    },
    {
      "town": "Weehawken",
      "description": "Cliffside town with stunning Manhattan views and ferry service.",
      "schools": "Weehawken Township School District (K–12), smaller district.",
      "primary_transit": "NY Waterway Ferry to Midtown (Weehawken Port Imperial terminal), plus buses.",
      "commute_to_nyc": "Ferry often 10–30 minutes to Midtown; buses about 20–40 minutes.",
      "highways": "Route 495, Palisades Interstate Parkway.",
      "notes": "Waterfront high-rises with spectacular city views; quieter than Hoboken but still convenient."
    },
    {
      "town": "West New York",
      "description": "Densely populated hilltop town with iconic Manhattan vistas along Boulevard East.",
      "schools": "West New York Board of Education oversees public schools; various charters also available.",
      "primary_transit": "Multiple bus lines along Boulevard East and Bergenline Avenue; ferry in nearby Weehawken.",
      "commute_to_nyc": "Buses typically 20–40 minutes to Midtown; ferry access about 10–30 minutes.",
      "highways": "Route 495, Palisades Interstate Parkway.",
      "notes": "Strong sense of community and Latino culture; views are among the best in NJ."
    }
  ],
  "Morris": [
    {
      "town": "Boonton",
      "description": "Charming historic town with Boonton Reservoir views and a walkable Main Street.",
      "schools": "Boonton Public Schools (K–12), including Boonton High School.",
      "primary_transit": "NJ Transit Morris & Essex Line (Montclair-Boonton branch) from Boonton Station.",
      "commute_to_nyc": "Trains to Hoboken (transfer to PATH or ferry) or direct to New York Penn typically 60–80 minutes.",
      "highways": "Route 287, Route 202, I-80 nearby.",
      "notes": "Historic downtown, local boutiques, and reservoir scenery attract a loyal community."
    },
    {
      "town": "Boonton Township",
      "description": "Residential suburb near Boonton town, mostly single-family homes.",
      "schools": "Boonton Township School District (K–8), with high schoolers attending Boonton or Mountain Lakes.",
      "primary_transit": "Residents typically drive to Boonton or other stations for rail/bus.",
      "commute_to_nyc": "Park-and-ride commutes to NYC often 60–90 minutes total.",
      "highways": "Route 287, I-80.",
      "notes": "Quiet streets and good schools, popular with families."
    },
    {
      "town": "Butler",
      "description": "Small borough with a suburban feel and access to major highways.",
      "schools": "Butler Public Schools (K–12), including Butler High School.",
      "primary_transit": "NJ Transit Main Line from Butler Station, connecting to Hoboken.",
      "commute_to_nyc": "Typically 60–90 minutes to Midtown via Hoboken transfer to PATH or ferry.",
      "highways": "Route 23, I-287.",
      "notes": "Affordable homes relative to other Morris County towns; family-oriented community."
    },
    {
      "town": "Chatham Borough",
      "description": "Historic downtown with top schools, Midtown Direct trains, and strong community spirit.",
      "schools": "Chatham Borough School District (K–8), then School District of the Chathams for high school.",
      "primary_transit": "NJ Transit Morris & Essex Line with Midtown Direct service from Chatham Station.",
      "commute_to_nyc": "Direct trains to New York Penn typically 40–50 minutes.",
      "highways": "Route 24, I-287, Route 124.",
      "notes": "Walkable downtown, library, and community events; highly rated schools drive demand."
    },
    {
      "town": "Chatham Township",
      "description": "Spacious homes and estate-like properties surrounding Chatham Borough.",
      "schools": "Chatham Township School District, then School District of the Chathams for high school (shared with Borough).",
      "primary_transit": "Residents often drive to Chatham or Madison for Midtown Direct.",
      "commute_to_nyc": "Varies depending on driving to station, typically 45–60 minutes total.",
      "highways": "Route 24, I-287.",
      "notes": "Larger lots and quiet streets; same excellent high school as Chatham Borough."
    },
    {
      "town": "Chester Borough",
      "description": "Quaint village known for antique shops and historic charm.",
      "schools": "Chester Borough School District (K–8), then West Morris Regional High School.",
      "primary_transit": "No train station; residents drive or take buses from other towns.",
      "commute_to_nyc": "Longer commute, often 70–100 minutes by car-to-train or bus.",
      "highways": "Route 206, Route 24 access.",
      "notes": "Picturesque Main Street, popular for weekend visitors and antique hunters."
    },
    {
      "town": "Chester Township",
      "description": "Rolling hills, horse farms, and rural estates around Chester Borough.",
      "schools": "Chester Township School District (K–8), then West Morris Regional High School.",
      "primary_transit": "Primarily a car-commute area; limited public transit.",
      "commute_to_nyc": "Extended commutes 70–100+ minutes via park-and-ride.",
      "highways": "Route 206, I-287 accessible.",
      "notes": "Scenic countryside and large lots; strong equestrian presence."
    },
    {
      "town": "Denville",
      "description": "The Hub of Morris County, with shopping centers and easy highway access.",
      "schools": "Denville Township School District (K–12), including Morris Knolls High School.",
      "primary_transit": "NJ Transit Morris & Essex Line (Montclair-Boonton branch) from Denville Station.",
      "commute_to_nyc": "Trains to Hoboken or transfer to direct trains; total 60–80 minutes typically.",
      "highways": "Route 10, Route 46, I-80, I-287.",
      "notes": "Lakes and parks make this a recreation hub; retail and dining options along Route 10."
    },
    {
      "town": "Dover",
      "description": "Diverse industrial town and rail hub in central Morris County.",
      "schools": "Dover Public Schools (K–12), with a bilingual focus in some programs.",
      "primary_transit": "NJ Transit Morris & Essex Line from Dover Station.",
      "commute_to_nyc": "Commutes to Hoboken or transfer for Midtown, often 70–90 minutes.",
      "highways": "Route 80, Route 46, Route 15.",
      "notes": "More affordable housing; industrial heritage and growing immigrant population."
    },
    {
      "town": "East Hanover",
      "description": "Quiet residential suburb with corporate offices and parks.",
      "schools": "East Hanover Township School District (K–8), then Hanover Park High School.",
      "primary_transit": "Primarily a car town; nearby Morristown or short-line trains for commuters.",
      "commute_to_nyc": "Park-and-ride commutes often 50–80 minutes total.",
      "highways": "Route 10, I-280.",
      "notes": "Popular with families; strong sense of community."
    },
    {
      "town": "Florham Park",
      "description": "Corporate headquarters hub with luxury developments and easy highway access.",
      "schools": "Florham Park School District (K–8), then Hanover Park High School.",
      "primary_transit": "No direct rail; commuters drive to nearby stations (Morristown, Madison).",
      "commute_to_nyc": "Park-and-ride to Midtown Direct often 50–70 minutes total.",
      "highways": "Route 24, I-287.",
      "notes": "Major employers include BASF and other Fortune 500 companies."
    },
    {
      "town": "Hanover Township",
      "description": "Large residential and commercial township with shopping along Route 10.",
      "schools": "Hanover Township School District (K–8), then Hanover Park High School.",
      "primary_transit": "No train station; residents drive to Morristown or other stations.",
      "commute_to_nyc": "Park-and-ride often 60–80 minutes to Midtown.",
      "highways": "Route 10, I-287.",
      "notes": "Bee Meadow Park and family neighborhoods; retail corridor along Route 10."
    },
    {
      "town": "Harding Township",
      "description": "Exclusive, rural township with large estates and preserved open space.",
      "schools": "Harding Township School District (K–8), then Morristown or private/regional high schools.",
      "primary_transit": "No public transit; residents drive to nearby stations.",
      "commute_to_nyc": "Extended commutes 60–90+ minutes via car-to-train.",
      "highways": "Route 202, I-287 accessible.",
      "notes": "Horse farms, historic sites, and a low-density, high-income community."
    },
    {
      "town": "Madison",
      "description": "The Rose City, known for blooms in summer, Midtown Direct trains, and Drew University.",
      "schools": "Madison Public Schools (K–12), highly rated.",
      "primary_transit": "NJ Transit Morris & Essex Line with Midtown Direct from Madison Station.",
      "commute_to_nyc": "Direct trains to New York Penn often 50–55 minutes.",
      "highways": "Route 24, I-287.",
      "notes": "Charming downtown with restaurants and shops; university presence adds cultural flair."
    },
    {
      "town": "Mendham Borough",
      "description": "Historic village with preserved colonial architecture and a tight-knit community.",
      "schools": "Mendham Borough School District (K–8), then West Morris Mendham High School.",
      "primary_transit": "No train; residents typically drive to Morristown or Madison.",
      "commute_to_nyc": "Park-and-ride commutes 60–90 minutes.",
      "highways": "Route 24, I-287.",
      "notes": "Scenic historic downtown and upscale homes."
    },
    {
      "town": "Mendham Township",
      "description": "Sprawling rural township with large properties and equestrian estates.",
      "schools": "Mendham Township School District (K–8), then West Morris Mendham High School.",
      "primary_transit": "No public transit; car-commute area.",
      "commute_to_nyc": "Often 70–100+ minutes via park-and-ride.",
      "highways": "Route 24, I-287 accessible.",
      "notes": "Horse country with expansive lots and privacy."
    },
    {
      "town": "Mine Hill",
      "description": "Small residential township with access to Route 80 and neighboring Wharton/Dover.",
      "schools": "Mine Hill Township School District (K–8), then Morris Hills Regional High School.",
      "primary_transit": "No train; bus or drive to nearby stations.",
      "commute_to_nyc": "Typically 70–100 minutes by car-to-train.",
      "highways": "Route 80, Route 46.",
      "notes": "Quiet community; more affordable than some surrounding towns."
    },
    {
      "town": "Montville",
      "description": "Spacious suburban township with excellent schools and family-friendly neighborhoods.",
      "schools": "Montville Township Public Schools (K–12), highly regarded.",
      "primary_transit": "No direct rail; residents drive to Denville, Mountain Lakes, or other stations.",
      "commute_to_nyc": "Park-and-ride 60–90 minutes total.",
      "highways": "Route 202, I-287.",
      "notes": "Well-regarded schools and parks; popular with families."
    },
    {
      "town": "Morris Township",
      "description": "Large township surrounding Morristown, including upscale neighborhoods.",
      "schools": "Morris School District (K–12), shared with Morristown; Morristown High School is renowned.",
      "primary_transit": "NJ Transit Morris & Essex Line Midtown Direct from Morristown Station.",
      "commute_to_nyc": "Direct trains to New York Penn typically 55–65 minutes.",
      "highways": "I-287, Route 24.",
      "notes": "More suburban feel than Morristown proper; strong school system."
    },
    {
      "town": "Morristown",
      "description": "Historic county seat with Midtown Direct trains, vibrant downtown, restaurants, and arts scene.",
      "schools": "Morris School District (K–12), including Morristown High School (shared with Morris Township).",
      "primary_transit": "NJ Transit Morris & Essex Line with Midtown Direct service from Morristown Station.",
      "commute_to_nyc": "Direct trains to New York Penn typically 55–65 minutes.",
      "highways": "I-287, Route 24, Route 202.",
      "notes": "Cultural hub with theater, shopping, and nightlife; historic Revolutionary War sites."
    },
    {
      "town": "Mount Arlington",
      "description": "Small borough on the shores of Lake Hopatcong.",
      "schools": "Mount Arlington School District (K–8), then Roxbury or other high schools.",
      "primary_transit": "NJ Transit Main Line stops at Mount Arlington, though frequency is limited.",
      "commute_to_nyc": "Typically 75–100+ minutes via rail or bus.",
      "highways": "I-80, Route 46.",
      "notes": "Lake Hopatcong access; seasonal recreation and waterfront living."
    },
    {
      "town": "Mount Olive",
      "description": "Large township including Budd Lake and Flanders sections.",
      "schools": "Mount Olive Township School District (K–12).",
      "primary_transit": "Limited rail; NJ Transit from Budd Lake station (infrequent service).",
      "commute_to_nyc": "Often 70–100+ minutes by car or rail.",
      "highways": "Route 46, I-80.",
      "notes": "More rural western Morris; affordable housing and growing commercial areas."
    },
    {
      "town": "Mountain Lakes",
      "description": "Exclusive lake community with Tudor-style homes and top schools.",
      "schools": "Mountain Lakes School District (K–12), highly ranked.",
      "primary_transit": "NJ Transit Morris & Essex Line (Montclair-Boonton branch) from Mountain Lakes Station.",
      "commute_to_nyc": "Trains to Hoboken or transfer; typically 60–80 minutes to Midtown.",
      "highways": "Route 46, I-280.",
      "notes": "Four private lakes for residents; prestigious and sought-after community."
    },
    {
      "town": "Parsippany-Troy Hills",
      "description": "Major corporate center with diverse residential neighborhoods.",
      "schools": "Parsippany-Troy Hills School District (K–12), large district with multiple schools.",
      "primary_transit": "Limited direct rail; extensive bus service and easy highway access.",
      "commute_to_nyc": "Commutes often 60–90 minutes via bus or park-and-ride to trains.",
      "highways": "I-287, Route 80, Route 46, Route 10.",
      "notes": "Many Fortune 500 headquarters; large commercial tax base."
    },
    {
      "town": "Pequannock Township",
      "description": "Suburban township with reservoirs and parks along the Pequannock River.",
      "schools": "Pequannock Township School District (K–12).",
      "primary_transit": "Limited rail; residents drive to nearby stations or bus routes.",
      "commute_to_nyc": "Typically 60–90 minutes by car-to-train.",
      "highways": "Route 23, I-287.",
      "notes": "Reservoir system provides drinking water to Newark; outdoor recreation popular."
    },
    {
      "town": "Randolph",
      "description": "Family-friendly township with top schools, parks, and trail systems.",
      "schools": "Randolph Township Schools (K–12), highly regarded.",
      "primary_transit": "No direct rail; commuters drive to nearby stations (Morristown, Dover).",
      "commute_to_nyc": "Park-and-ride often 60–90 minutes total.",
      "highways": "Route 10, I-287.",
      "notes": "Strong school district and numerous parks/trails make it popular with families."
    },
    {
      "town": "Riverdale",
      "description": "Small borough near Pequannock River with a suburban feel.",
      "schools": "Riverdale School District (K–8), then students attend regional high schools.",
      "primary_transit": "Limited public transit; mainly car-oriented.",
      "commute_to_nyc": "Often 60–90 minutes via car-to-train or bus.",
      "highways": "Route 23, I-287.",
      "notes": "Quiet community with affordable housing compared to other Morris towns."
    },
    {
      "town": "Rockaway Borough",
      "description": "Small borough along the Rockaway River with a walkable Main Street.",
      "schools": "Rockaway Borough School District (K–8), then Morris Hills High School.",
      "primary_transit": "NJ Transit Main Line from Rockaway Station.",
      "commute_to_nyc": "Trains often 70–90 minutes to Hoboken or transfer.",
      "highways": "Route 80, Route 46.",
      "notes": "Historic downtown; tight-knit community with local shops."
    },
    {
      "town": "Rockaway Township",
      "description": "Larger township surrounding Rockaway Borough with diverse neighborhoods.",
      "schools": "Rockaway Township Public Schools (K–8), then Morris Hills or Morris Knolls High School.",
      "primary_transit": "Limited rail; residents drive to nearby stations.",
      "commute_to_nyc": "Typically 70–90 minutes via car-to-train.",
      "highways": "Route 80, Route 46, I-287.",
      "notes": "Includes areas like Lake Telemark and Hibernia; mix of suburban and rural."
    },
    {
      "town": "Roxbury Township",
      "description": "Large township including Succasunna, Landing, and Ledgewood sections.",
      "schools": "Roxbury Township School District (K–12).",
      "primary_transit": "NJ Transit Main Line stops at Mount Arlington/Landing (limited service).",
      "commute_to_nyc": "Often 75–100+ minutes by rail or bus.",
      "highways": "Route 80, Route 46.",
      "notes": "More affordable; mix of residential neighborhoods and open land."
    },
    {
      "town": "Victory Gardens",
      "description": "Tiny borough historically built for workers, now quiet residential.",
      "schools": "Victory Gardens School District (K–8), then Morris Hills High School.",
      "primary_transit": "No direct train; nearby Dover for rail.",
      "commute_to_nyc": "Typically 70–100 minutes via car-to-train.",
      "highways": "Route 80, Route 46.",
      "notes": "Smallest and least populated municipality in Morris County."
    },
    {
      "town": "Washington Township",
      "description": "Rural-suburban township in western Morris County.",
      "schools": "Washington Township School District (K–8), then West Morris Central High School.",
      "primary_transit": "No public transit; car-oriented.",
      "commute_to_nyc": "Extended commutes 80–100+ minutes by car-to-train.",
      "highways": "Route 57, I-80 accessible.",
      "notes": "Large lots and open space; lower density living."
    },
    {
      "town": "Wharton",
      "description": "Small borough with canal heritage and a revitalizing downtown.",
      "schools": "Wharton Borough School District (K–8), then Morris Hills High School.",
      "primary_transit": "NJ Transit Main Line from Wharton Station.",
      "commute_to_nyc": "Trains often 70–90 minutes to Hoboken or transfer.",
      "highways": "Route 80, Route 15.",
      "notes": "Historic Morris Canal influences local character; affordable housing."
    }
  ],
  "Middlesex": [
    {
      "town": "Carteret",
      "description": "Industrial waterfront borough with growing residential areas.",
      "schools": "Carteret Public Schools (K–12).",
      "primary_transit": "NJ Transit buses and nearby rail connections (Rahway, Metuchen).",
      "commute_to_nyc": "Typically 45–75 minutes via bus or park-and-ride to trains.",
      "highways": "NJ Turnpike, Route 1, Route 440.",
      "notes": "Waterfront redevelopment projects underway; historically industrial."
    },
    {
      "town": "Cranbury",
      "description": "Historic village center surrounded by farmland and preserved open space.",
      "schools": "Cranbury Township School District (K–8), then students attend high school via sending relationship.",
      "primary_transit": "No direct rail; commuters drive to Princeton Junction or other stations.",
      "commute_to_nyc": "Often 60–90 minutes by car-to-train.",
      "highways": "NJ Turnpike, Route 130.",
      "notes": "Colonial charm; quiet, low-density living."
    },
    {
      "town": "East Brunswick",
      "description": "Large suburban township with top schools, shopping, and diverse neighborhoods.",
      "schools": "East Brunswick Public Schools (K–12), consistently highly ranked.",
      "primary_transit": "Extensive NJ Transit bus service to NYC; no direct train.",
      "commute_to_nyc": "Buses to Port Authority often 45–70 minutes depending on traffic.",
      "highways": "NJ Turnpike, Route 18, Route 1.",
      "notes": "Strong school district draws families; large retail centers."
    },
    {
      "town": "Edison",
      "description": "New Jersey's fifth-largest municipality, with diverse communities and major transit hub at Metropark.",
      "schools": "Edison Township Public Schools is a large district with many elementary, middle, and high schools.",
      "primary_transit": "NJ Transit Northeast Corridor at Metropark and Edison stations, plus extensive bus service.",
      "commute_to_nyc": "Express trains from Metropark to New York Penn as fast as 35–45 minutes.",
      "highways": "NJ Turnpike, Garden State Parkway, Route 1, Route 27.",
      "notes": "Home to major corporate campuses; diverse food scene and shopping."
    },
    {
      "town": "Helmetta",
      "description": "Tiny historic borough along the Manalapan Brook.",
      "schools": "Helmetta School District (K–8), then students attend Spotswood or regional high schools.",
      "primary_transit": "Limited public transit; primarily a car town.",
      "commute_to_nyc": "Often 70–100+ minutes via car-to-train or bus.",
      "highways": "Route 18, Route 130.",
      "notes": "Small-town feel; modest homes and historic mill buildings."
    },
    {
      "town": "Highland Park",
      "description": "Small, progressive borough with a walkable downtown and Raritan River waterfront.",
      "schools": "Highland Park Public Schools (K–12).",
      "primary_transit": "NJ Transit Northeast Corridor from Highland Park Station.",
      "commute_to_nyc": "Trains to New York Penn typically 50–70 minutes.",
      "highways": "Route 27, NJ Turnpike nearby.",
      "notes": "Tree-lined streets and tight-knit community; near Rutgers."
    },
    {
      "town": "Jamesburg",
      "description": "Historic small borough with a revitalizing downtown.",
      "schools": "Jamesburg Public Schools (K–8), then students typically attend Monroe Township High School.",
      "primary_transit": "Limited public transit; car-oriented.",
      "commute_to_nyc": "Often 70–100 minutes via car-to-train or bus.",
      "highways": "Route 18, NJ Turnpike.",
      "notes": "Affordable homes; historic character being restored."
    },
    {
      "town": "Metuchen",
      "description": "The Brainy Borough, with a charming downtown and direct NEC trains.",
      "schools": "Metuchen Public Schools (K–12), highly regarded.",
      "primary_transit": "NJ Transit Northeast Corridor from Metuchen Station.",
      "commute_to_nyc": "Trains to New York Penn typically 40–50 minutes.",
      "highways": "Garden State Parkway, Route 27, NJ Turnpike nearby.",
      "notes": "Walkable downtown with restaurants and shops; strong community events."
    },
    {
      "town": "Middlesex",
      "description": "Small borough with suburban neighborhoods and proximity to Route 28 corridor.",
      "schools": "Middlesex Borough School District (K–8), then students attend regional high schools.",
      "primary_transit": "Limited public transit; bus and car-oriented.",
      "commute_to_nyc": "Typically 60–90 minutes via bus or park-and-ride.",
      "highways": "Route 28, NJ Turnpike nearby.",
      "notes": "Affordable housing; quiet residential streets."
    },
    {
      "town": "Milltown",
      "description": "Tiny borough along the Raritan River with a small-town vibe.",
      "schools": "Milltown Public Schools (K–8), then students attend Spotswood or other high schools.",
      "primary_transit": "Limited transit; primarily car-oriented.",
      "commute_to_nyc": "Often 60–90 minutes via car-to-train or bus.",
      "highways": "Route 18, NJ Turnpike.",
      "notes": "Affordable homes; close-knit community."
    },
    {
      "town": "Monroe Township",
      "description": "Large township known for active adult communities and diverse residential areas.",
      "schools": "Monroe Township Public Schools (K–12).",
      "primary_transit": "Limited rail; extensive bus service.",
      "commute_to_nyc": "Often 60–90+ minutes via bus or car-to-train.",
      "highways": "NJ Turnpike, Route 33, Route 130.",
      "notes": "Major retirement communities; family neighborhoods also expanding."
    },
    {
      "town": "New Brunswick",
      "description": "Urban hub and home to Rutgers University, medical centers, and cultural venues.",
      "schools": "New Brunswick Public Schools (K–12); urban district.",
      "primary_transit": "NJ Transit Northeast Corridor from New Brunswick Station.",
      "commute_to_nyc": "Trains to New York Penn typically 45–60 minutes.",
      "highways": "Route 18, Route 1, NJ Turnpike.",
      "notes": "University presence drives arts, dining, and nightlife; State Theatre and more."
    },
    {
      "town": "North Brunswick",
      "description": "Diverse residential and commercial township along Route 1.",
      "schools": "North Brunswick Township Public Schools (K–12).",
      "primary_transit": "NJ Transit bus service to NYC; no direct rail.",
      "commute_to_nyc": "Buses or park-and-ride often 50–80 minutes.",
      "highways": "Route 1, NJ Turnpike.",
      "notes": "Mix of residential neighborhoods and commercial centers."
    },
    {
      "town": "Old Bridge",
      "description": "Large, sprawling township with diverse neighborhoods and Route 9 retail corridor.",
      "schools": "Old Bridge Township Public Schools (K–12), large district.",
      "primary_transit": "NJ Transit buses; nearby rail at Aberdeen-Matawan.",
      "commute_to_nyc": "Often 60–90 minutes via bus or park-and-ride.",
      "highways": "Route 9, Route 18, Garden State Parkway.",
      "notes": "Suburban lifestyle with shopping and parks; affordable housing."
    },
    {
      "town": "Perth Amboy",
      "description": "Historic waterfront city on the Raritan Bay.",
      "schools": "Perth Amboy Public Schools (K–12).",
      "primary_transit": "NJ Transit North Jersey Coast Line from Perth Amboy Station.",
      "commute_to_nyc": "Trains to New York Penn typically 60–80 minutes.",
      "highways": "Route 440, Garden State Parkway, Route 9.",
      "notes": "Waterfront redevelopment; historic sites and diverse community."
    },
    {
      "town": "Piscataway",
      "description": "Large township adjacent to Rutgers University with diverse neighborhoods.",
      "schools": "Piscataway Township Schools (K–12).",
      "primary_transit": "NJ Transit Northeast Corridor (nearby stations in Edison/Metuchen), plus extensive bus service.",
      "commute_to_nyc": "Typically 50–75 minutes via bus or nearby train stations.",
      "highways": "Route 287, Route 18, Route 1.",
      "notes": "Home to part of Rutgers campus; mix of residential and commercial."
    },
    {
      "town": "Sayreville",
      "description": "Industrial and residential borough with waterfront areas along Raritan Bay.",
      "schools": "Sayreville Public Schools (K–12).",
      "primary_transit": "NJ Transit Northeast Corridor from nearby stations; bus service.",
      "commute_to_nyc": "Often 50–80 minutes to New York Penn.",
      "highways": "Route 9, Route 35, Garden State Parkway.",
      "notes": "Mix of working-class neighborhoods and industrial zones; some waterfront development."
    },
    {
      "town": "South Amboy",
      "description": "Small waterfront city with ferry service to Manhattan and rail connections.",
      "schools": "South Amboy Public Schools (K–12).",
      "primary_transit": "NJ Transit North Jersey Coast Line; Seastreak Ferry to Manhattan.",
      "commute_to_nyc": "Ferry about 45–60 minutes to Manhattan; trains about 60–80 minutes.",
      "highways": "Route 35, Garden State Parkway.",
      "notes": "Historic downtown; ferry adds commuting flexibility."
    },
    {
      "town": "South Plainfield",
      "description": "Suburban borough with strong industrial base and affordable housing.",
      "schools": "South Plainfield Public Schools (K–12).",
      "primary_transit": "NJ Transit buses; nearby rail at Metuchen/Edison.",
      "commute_to_nyc": "Typically 50–80 minutes via bus or park-and-ride.",
      "highways": "Route 287, Route 1.",
      "notes": "Mix of residential and industrial; family-oriented community."
    },
    {
      "town": "South River",
      "description": "Small borough along the South River with a downtown feel.",
      "schools": "South River Public Schools (K–12).",
      "primary_transit": "Limited rail; NJ Transit buses and nearby stations.",
      "commute_to_nyc": "Often 60–90 minutes via bus or car-to-train.",
      "highways": "Route 18, Route 1, NJ Turnpike nearby.",
      "notes": "Affordable homes; tight-knit community with local shops."
    },
    {
      "town": "Spotswood",
      "description": "Small borough with residential neighborhoods and proximity to major highways.",
      "schools": "Spotswood Public Schools (K–12).",
      "primary_transit": "Limited public transit; car-oriented.",
      "commute_to_nyc": "Typically 60–90 minutes via car-to-train or bus.",
      "highways": "Route 18, NJ Turnpike.",
      "notes": "Quiet suburban feel; affordable housing."
    },
    {
      "town": "Woodbridge",
      "description": "Large, diverse township with multiple neighborhoods, shopping, and direct NEC/NJCL trains.",
      "schools": "Woodbridge Township School District is one of the largest in the state, serving numerous neighborhoods and schools.",
      "primary_transit": "Multiple NJ Transit stations (Woodbridge, Avenel, Metropark nearby) plus extensive bus network.",
      "commute_to_nyc": "Express trains from Metropark/Woodbridge can be 35–55 minutes to New York Penn.",
      "highways": "NJ Turnpike, Garden State Parkway, Route 1&9, Route 35, and Route 440 intersect here.",
      "notes": "Encompasses many distinct sections, each with its own character and price points."
    }
  ],
  "Union": [
    {
      "town": "Summit",
      "description": "Premier hilltop city with charming downtown, top schools, and Midtown Direct service—home to Jorge Ramirez's office!",
      "schools": "Summit Public Schools (K–12) are consistently ranked among New Jersey's best districts.",
      "primary_transit": "NJ Transit Morris & Essex Line with Midtown Direct service from Summit Station.",
      "commute_to_nyc": "Direct trains to New York Penn typically 35–45 minutes, making Summit a prime commuter town.",
      "highways": "Route 24, I-78 nearby for easy highway access.",
      "notes": "Walkable downtown with boutiques, restaurants, and cultural events; highly sought-after for families and professionals."
    },
    {
      "town": "Westfield",
      "description": "Classic suburban town with excellent schools, vibrant downtown, and strong community spirit.",
      "schools": "Westfield Public Schools (K–12), consistently top-rated in New Jersey.",
      "primary_transit": "NJ Transit Raritan Valley Line from Westfield Station, with connections to NYC.",
      "commute_to_nyc": "Trains to New York Penn typically 45–60 minutes via Newark transfer.",
      "highways": "Route 22, Garden State Parkway nearby.",
      "notes": "Tree-lined streets, active downtown, and excellent recreation facilities make this highly desirable."
    },
    {
      "town": "Cranford",
      "description": "Charming downtown with restaurants, boutiques, and Raritan Valley Line service.",
      "schools": "Cranford Public Schools (K–12), well-regarded district.",
      "primary_transit": "NJ Transit Raritan Valley Line from Cranford Station.",
      "commute_to_nyc": "Trains to New York Penn typically 50–65 minutes via Newark.",
      "highways": "Garden State Parkway, Route 22.",
      "notes": "Walkable downtown and strong community events; family-friendly atmosphere."
    },
    {
      "town": "Plainfield",
      "description": "Historic city with diverse neighborhoods and direct Northeast Corridor rail service.",
      "schools": "Plainfield Public Schools (K–12), urban district with various programs.",
      "primary_transit": "NJ Transit Northeast Corridor from Plainfield Station.",
      "commute_to_nyc": "Trains to New York Penn typically 50–65 minutes.",
      "highways": "Route 22, Route 28.",
      "notes": "More affordable housing; historic architecture and diverse community."
    },
    {
      "town": "Union",
      "description": "Township with diverse neighborhoods, shopping centers, and convenient highway access.",
      "schools": "Union Public Schools (K–12).",
      "primary_transit": "NJ Transit Raritan Valley Line from Union Station; extensive bus service.",
      "commute_to_nyc": "Trains typically 50–70 minutes to New York Penn via Newark.",
      "highways": "Route 22, Garden State Parkway, Route 82.",
      "notes": "Mix of residential areas and commercial districts; affordable options."
    },
    {
      "town": "Elizabeth",
      "description": "New Jersey's fourth-largest city with diverse neighborhoods and excellent transit connections.",
      "schools": "Elizabeth Public Schools (K–12), large urban district.",
      "primary_transit": "NJ Transit Northeast Corridor and North Jersey Coast Line, plus PATH-adjacent locations.",
      "commute_to_nyc": "Trains to New York Penn 25–40 minutes; close to Newark Airport.",
      "highways": "NJ Turnpike, Route 1&9, Route 22.",
      "notes": "Very affordable; diverse immigrant communities and expanding development."
    },
    {
      "town": "Linden",
      "description": "Industrial and residential city with refinery presence and transit access.",
      "schools": "Linden Public Schools (K–12).",
      "primary_transit": "NJ Transit Northeast Corridor from Linden Station.",
      "commute_to_nyc": "Trains to New York Penn typically 35–50 minutes.",
      "highways": "NJ Turnpike, Route 1&9.",
      "notes": "Working-class community with industrial base; affordable housing."
    },
    {
      "town": "Rahway",
      "description": "Historic city with arts district, downtown restaurants, and Northeast Corridor trains.",
      "schools": "Rahway Public Schools (K–12).",
      "primary_transit": "NJ Transit Northeast Corridor from Rahway Station.",
      "commute_to_nyc": "Trains to New York Penn typically 40–55 minutes.",
      "highways": "NJ Turnpike, Garden State Parkway, Route 1&9.",
      "notes": "Revitalizing downtown with Union County Performing Arts Center; affordable homes."
    },
    {
      "town": "Roselle",
      "description": "Small borough with residential neighborhoods and convenient transit access.",
      "schools": "Roselle Public Schools (K–12).",
      "primary_transit": "NJ Transit Raritan Valley Line from Roselle Station.",
      "commute_to_nyc": "Trains typically 50–70 minutes to New York Penn via Newark.",
      "highways": "Route 22, Garden State Parkway nearby.",
      "notes": "Affordable housing; close-knit community with local parks."
    },
    {
      "town": "Roselle Park",
      "description": "Compact borough with walkable streets and Raritan Valley rail access.",
      "schools": "Roselle Park School District (K–12).",
      "primary_transit": "NJ Transit Raritan Valley Line from Roselle Park Station.",
      "commute_to_nyc": "Trains typically 50–65 minutes to New York Penn via Newark.",
      "highways": "Garden State Parkway, Route 22.",
      "notes": "Small-town feel with affordable homes and easy highway access."
    },
    {
      "town": "Springfield",
      "description": "Suburban township with excellent schools and proximity to Short Hills Mall.",
      "schools": "Springfield Public Schools (K–12), highly regarded.",
      "primary_transit": "No direct train; residents drive to nearby Midtown Direct stations (Millburn, Summit).",
      "commute_to_nyc": "Park-and-ride typically 40–60 minutes total via Midtown Direct.",
      "highways": "Route 22, Route 24, I-78 nearby.",
      "notes": "Family-friendly with strong schools; close to premier shopping."
    },
    {
      "town": "Mountainside",
      "description": "Small, quiet borough with wooded lots and top-rated schools.",
      "schools": "Mountainside Public Schools (K–8), then students attend Governor Livingston High School.",
      "primary_transit": "No direct train; residents drive to nearby stations (Summit, Westfield).",
      "commute_to_nyc": "Park-and-ride typically 45–65 minutes total.",
      "highways": "Route 22, I-78 nearby.",
      "notes": "Peaceful, low-density living with excellent schools and Watchung Reservation access."
    },
    {
      "town": "Berkeley Heights",
      "description": "Spacious suburban township with excellent schools and family-friendly neighborhoods.",
      "schools": "Berkeley Heights Public Schools (K–12), consistently highly rated.",
      "primary_transit": "NJ Transit Raritan Valley Line from Berkeley Heights Station.",
      "commute_to_nyc": "Trains typically 55–70 minutes to New York Penn via Newark.",
      "highways": "Route 22, Route 78, I-287 nearby.",
      "notes": "Large lots, strong community, and top schools make this popular with families."
    },
    {
      "town": "New Providence",
      "description": "Charming borough with walkable downtown, top schools, and direct Midtown service.",
      "schools": "New Providence School District (K–12), highly regarded.",
      "primary_transit": "NJ Transit Morris & Essex Line with Midtown Direct from New Providence Station.",
      "commute_to_nyc": "Direct trains to New York Penn typically 45–55 minutes.",
      "highways": "Route 22, I-78 nearby.",
      "notes": "Quaint downtown with local shops; strong sense of community."
    },
    {
      "town": "Clark",
      "description": "Residential township with parks and convenient highway access.",
      "schools": "Clark Public Schools (K–12).",
      "primary_transit": "No direct train; residents use nearby Rahway or Cranford stations.",
      "commute_to_nyc": "Park-and-ride typically 50–70 minutes total.",
      "highways": "Garden State Parkway, Route 22.",
      "notes": "Suburban feel with affordable homes and good schools."
    },
    {
      "town": "Garwood",
      "description": "Tiny borough with small-town charm and proximity to Westfield and Cranford.",
      "schools": "Garwood Public Schools (K–8), then students attend Arthur L. Johnson High School.",
      "primary_transit": "No direct station; close to Cranford and Westfield stations.",
      "commute_to_nyc": "Park-and-ride typically 50–65 minutes total.",
      "highways": "Route 22, Garden State Parkway nearby.",
      "notes": "Very small but tight-knit community; affordable starter homes."
    },
    {
      "town": "Scotch Plains",
      "description": "Spacious suburban township with top schools and large residential lots.",
      "schools": "Scotch Plains-Fanwood Regional School District (K–12), highly rated.",
      "primary_transit": "NJ Transit Raritan Valley Line from Fanwood Station (shared with Fanwood).",
      "commute_to_nyc": "Trains typically 55–70 minutes to New York Penn via Newark.",
      "highways": "Route 22, Garden State Parkway.",
      "notes": "Large homes, excellent schools, and strong community programs."
    },
    {
      "town": "Fanwood",
      "description": "Small, walkable borough with charming downtown and Raritan Valley rail access.",
      "schools": "Scotch Plains-Fanwood Regional School District (K–12), shared with Scotch Plains.",
      "primary_transit": "NJ Transit Raritan Valley Line from Fanwood Station.",
      "commute_to_nyc": "Trains typically 55–70 minutes to New York Penn via Newark.",
      "highways": "Route 22, Garden State Parkway.",
      "notes": "Victorian homes and walkable downtown; strong community feel."
    },
    {
      "town": "Kenilworth",
      "description": "Small borough with residential neighborhoods and proximity to Garden State Parkway.",
      "schools": "Kenilworth Public Schools (K–12).",
      "primary_transit": "No direct train; close to Union and Cranford stations.",
      "commute_to_nyc": "Park-and-ride typically 55–75 minutes total.",
      "highways": "Garden State Parkway, Route 22.",
      "notes": "Quiet community with affordable homes and easy highway access."
    },
    {
      "town": "Hillside",
      "description": "Residential township with diverse neighborhoods and convenient transit.",
      "schools": "Hillside Public Schools (K–12).",
      "primary_transit": "NJ Transit Raritan Valley Line from Hillside Station.",
      "commute_to_nyc": "Trains typically 50–70 minutes to New York Penn via Newark.",
      "highways": "Route 22, Garden State Parkway, I-78.",
      "notes": "Affordable housing; diverse community near Newark."
    },
    {
      "town": "Winfield",
      "description": "Tiny residential township, one of New Jersey's smallest municipalities.",
      "schools": "Winfield Township School (K–8), then students attend regional high schools.",
      "primary_transit": "No direct train; close to Clark and Linden stations.",
      "commute_to_nyc": "Park-and-ride typically 50–70 minutes total.",
      "highways": "Garden State Parkway nearby.",
      "notes": "Very small community with modest homes; affordable living."
    }
  ]
};
