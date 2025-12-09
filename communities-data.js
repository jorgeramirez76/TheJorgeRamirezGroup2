const communitiesData = {
  "Essex": [
    {
      "town": "Maplewood",
      "description": "Beloved village with Midtown Direct trains and an artsy, inclusive vibe.",
      "schools": "Part of the South Orange-Maplewood School District, known for diversity, strong arts, and IB programs.",
      "primary_transit": "NJ Transit Morris & Essex Line from Maplewood Station with Midtown Direct service.",
      "commute_to_nyc": "Direct trains to New York Penn often in the 30\u201340 minute range, plus walk/drive to the station.",
      "highways": "Access to I-78, Garden State Parkway, and nearby Route 24.",
      "notes": "Popular with Brooklyn transplants seeking a walkable downtown and community events."
    },
    {
      "town": "Millburn",
      "description": "Prestigious commuter town with top-ranked schools, luxury homes, and Midtown Direct trains.",
      "schools": "Millburn Township Public Schools are consistently ranked among the best in New Jersey.",
      "primary_transit": "NJ Transit Morris & Essex Line from Millburn and Short Hills stations with Midtown Direct to NYC.",
      "commute_to_nyc": "Trains to New York Penn typically 30\u201340 minutes, making it one of the most desirable NYC suburbs.",
      "highways": "Close to Route 24, I-78, and the Garden State Parkway.",
      "notes": "Home to the Mall at Short Hills and upscale residential neighborhoods."
    },
    {
      "town": "Montclair",
      "description": "Trendy township with vibrant arts, diverse neighborhoods, and Midtown train service.",
      "schools": "Montclair Public Schools feature a magnet system with strong arts and academic programs.",
      "primary_transit": "Multiple NJ Transit Montclair-Boonton Line stations plus DeCamp/NYC buses (service patterns subject to change).",
      "commute_to_nyc": "Typical trips 35\u201355 minutes to Midtown via train or bus depending on origin station and transfers.",
      "highways": "Near the Garden State Parkway, Route 3, and Route 46.",
      "notes": "Active restaurant scene, music venues, and Montclair State University help sustain demand."
    },
    {
      "town": "North Caldwell",
      "description": "Upscale borough with luxury homes, top schools, and suburban tranquility.",
      "schools": "North Caldwell students attend North Caldwell School District (K\u20136) and West Essex Regional School District (7\u201312).",
      "primary_transit": "Commuters typically use buses along Bloomfield Avenue or drive to nearby rail/PATH access.",
      "commute_to_nyc": "Door-to-door Midtown commutes often 45\u201375 minutes via bus or park-and-ride.",
      "highways": "Access to I-280, Garden State Parkway, and Route 23 via nearby corridors.",
      "notes": "Large homes and quiet streets appeal to move-up buyers."
    },
    {
      "town": "Nutley",
      "description": "Family-friendly township with strong schools, parks, and proximity to NYC.",
      "schools": "Nutley Public Schools provide K\u201312 education with neighborhood schools and AP offerings.",
      "primary_transit": "NJ Transit buses to Newark and NYC; some residents use nearby rail or light rail connections.",
      "commute_to_nyc": "Many commuters travel 45\u201375 minutes via bus/rail combinations to Midtown.",
      "highways": "Close to Route 3, Route 21, and the Garden State Parkway.",
      "notes": "Parks along the Third River and tree-lined streets provide a classic suburban feel."
    },
    {
      "town": "Orange",
      "description": "Historic urban-suburban city with direct Midtown train service.",
      "schools": "Orange Board of Education operates multiple K\u201312 schools, including STEM and arts-focused programs.",
      "primary_transit": "NJ Transit Morris & Essex Line and Highland Avenue stations; buses to Newark and NYC.",
      "commute_to_nyc": "Rail to New York Penn via Midtown Direct typically 25\u201335 minutes plus local access time.",
      "highways": "Adjacent to I-280 with connections to the Garden State Parkway and I-78.",
      "notes": "Ongoing redevelopment around stations offers opportunities for buyers and investors."
    },
    {
      "town": "Roseland",
      "description": "Small upscale borough with suburban tranquility and strong schools.",
      "schools": "Roseland students are served by the West Essex Regional School District for 7\u201312 and a local K\u20136 school system.",
      "primary_transit": "Commuters rely on NJ Transit buses along Eagle Rock Avenue and nearby rail in Livingston/West Orange corridors.",
      "commute_to_nyc": "Typical Midtown trips about 45\u201380 minutes via bus and highway routes.",
      "highways": "Excellent access to I-280, Route 10, and the Garden State Parkway.",
      "notes": "Corporate office parks and quiet neighborhoods share the small borough footprint."
    },
    {
      "town": "South Orange",
      "description": "Vibrant and diverse village with a lively downtown, Seton Hall University, and direct Midtown trains.",
      "schools": "Also part of the South Orange-Maplewood School District with a wide range of academic and arts programs.",
      "primary_transit": "NJ Transit Morris & Essex Line with Midtown Direct from South Orange Station.",
      "commute_to_nyc": "Direct trains to New York Penn are often 25\u201335 minutes, making this a quintessential rail suburb.",
      "highways": "Access to I-78, the Garden State Parkway, and Route 124 via nearby corridors.",
      "notes": "Walkable downtown, university presence, and historic housing stock draw a wide range of buyers."
    },
    {
      "town": "Verona",
      "description": "Charming township with Verona Park, strong schools, and a family-oriented lifestyle.",
      "schools": "Verona Public Schools provide K\u201312 education with a solid reputation and community support.",
      "primary_transit": "Commuters typically use NJ Transit buses along Bloomfield Avenue to Newark and NYC.",
      "commute_to_nyc": "Bus trips to Midtown often 45\u201375 minutes depending on traffic and route.",
      "highways": "Near Route 46, the Garden State Parkway, and I-280.",
      "notes": "Verona Park and neighborhood events contribute to high quality of life."
    },
    {
      "town": "West Caldwell",
      "description": "Residential township with strong schools and suburban convenience.",
      "schools": "West Caldwell is part of the Caldwell-West Caldwell School District, serving K\u201312 students.",
      "primary_transit": "NJ Transit buses along Bloomfield Avenue and nearby park-and-ride lots.",
      "commute_to_nyc": "Door-to-door commutes 45\u201380 minutes via bus/highway combinations.",
      "highways": "Good access to I-280, Route 46, and the Garden State Parkway.",
      "notes": "Primarily single-family homes with convenient shopping and services."
    },
    {
      "town": "West Orange",
      "description": "Diverse township with historic sites, suburban neighborhoods, and NYC skyline views.",
      "schools": "West Orange Public Schools offer K\u201312 education with magnet and honors programs.",
      "primary_transit": "NJ Transit buses to Newark and NYC; residents also use nearby rail and the Newark Light Rail system.",
      "commute_to_nyc": "Typical trips 45\u201375 minutes to Midtown via bus/rail connections.",
      "highways": "Access to I-280, the Garden State Parkway, and Route 10.",
      "notes": "Home to the Turtle Back Zoo, South Mountain Reservation access points, and varied housing stock."
    }
  ],
  "Hudson": [
    {
      "town": "Hoboken",
      "description": "Ultra-walkable brownstone city with waterfront parks, dining, and direct PATH/ferry to Manhattan.",
      "schools": "Hoboken Public Schools plus various charters and private schools serve local students.",
      "primary_transit": "PATH trains from Hoboken Terminal, NJ Transit rail and buses, Hudson-Bergen Light Rail, and NY Waterway ferries.",
      "commute_to_nyc": "One of the fastest NJ\u2013NYC commutes, often 10\u201325 minutes to Lower or Midtown Manhattan via PATH or ferry.",
      "highways": "Access to the Holland Tunnel, Route 495/Lincoln Tunnel approaches, and NJ Turnpike via nearby routes.",
      "notes": "High demand from young professionals, with strong rental and condo markets."
    },
    {
      "town": "Jersey City",
      "description": "NYC-adjacent metropolis with booming neighborhoods, waterfront towers, and PATH/HBLR/ferry access.",
      "schools": "Jersey City Public Schools plus a growing number of charter, magnet, and private schools.",
      "primary_transit": "Multiple PATH stations, Hudson-Bergen Light Rail, extensive bus network, and NY Waterway ferries.",
      "commute_to_nyc": "PATH and ferry rides can be as short as 10\u201320 minutes to Manhattan; many neighborhoods are true transit hubs.",
      "highways": "NJ Turnpike, Route 1&9, Route 440, and major tunnel approaches.",
      "notes": "Significant redevelopment along the waterfront, Journal Square, and emerging neighborhoods."
    },
    {
      "town": "Weehawken",
      "description": "Bluff-top and waterfront living with postcard Manhattan views and premier ferry access.",
      "schools": "Weehawken Township School District serves K\u201312 students with small class sizes by urban standards.",
      "primary_transit": "NY Waterway ferries from Port Imperial, NJ Transit buses along Boulevard East, and access to Light Rail nearby.",
      "commute_to_nyc": "Ferry and bus rides into Manhattan can be 10\u201330 minutes depending on destination and timing.",
      "highways": "Direct access to Route 495/Lincoln Tunnel, NJ Turnpike, and local arterials.",
      "notes": "Luxury condos and townhomes dominate the waterfront, while the bluffs offer older housing with spectacular views."
    },
    {
      "town": "West New York",
      "description": "Densely populated \u201cBoulevard East\u201d town with big views and quick bus/ferry access.",
      "schools": "West New York School District runs neighborhood schools, including Memorial High School.",
      "primary_transit": "NJ Transit and private buses along Bergenline Avenue and Boulevard East; ferries from nearby Port Imperial.",
      "commute_to_nyc": "Bus rides to Midtown via Lincoln Tunnel often 20\u201340 minutes depending on traffic.",
      "highways": "Close to Route 495/Lincoln Tunnel approaches and local Hudson County arterials.",
      "notes": "High-rise and mid-rise apartments are common, appealing to renters and first-time buyers."
    },
    {
      "town": "Union City",
      "description": "Ultra-dense, transit-rich city on the Palisades with fast bus runs to Midtown.",
      "schools": "Union City School District with several modern school complexes and extensive bilingual programs.",
      "primary_transit": "Heavy NJ Transit and private bus presence along Bergenline Avenue and surrounding corridors.",
      "commute_to_nyc": "Fast bus commutes via Lincoln Tunnel often 15\u201335 minutes depending on time of day.",
      "highways": "Near Route 495, Kennedy Boulevard, and local access to NJ Turnpike.",
      "notes": "Known for very high population density and vibrant commercial corridors."
    },
    {
      "town": "Bayonne",
      "description": "Peninsula city with neighborhood feel, parks, and HBLR to Jersey City and Hoboken.",
      "schools": "Bayonne Board of Education runs K\u201312 schools, with a single large high school.",
      "primary_transit": "Hudson-Bergen Light Rail stations throughout Bayonne, buses, and planned ferry service expansion.",
      "commute_to_nyc": "Many commuters take Light Rail to Jersey City\u2019s PATH/ferry, with total times generally 40\u201370 minutes to Manhattan.",
      "highways": "NJ Turnpike Extension, Route 440, and Bayonne Bridge access.",
      "notes": "Mix of older housing stock and new waterfront development attracts a wide range of buyers."
    },
    {
      "town": "North Bergen",
      "description": "Diverse township with Palisades views, parks, and strong bus access to NYC.",
      "schools": "North Bergen School District serves K\u201312 students; high school located on a ridge with skyline views.",
      "primary_transit": "Heavy NJ Transit and jitney bus service along Bergenline Avenue and Tonnelle Avenue; nearby Light Rail stops.",
      "commute_to_nyc": "Buses to Port Authority via Lincoln Tunnel typically 20\u201345 minutes depending on traffic.",
      "highways": "Close to Route 495, US 1&9, and NJ Turnpike.",
      "notes": "Hilly terrain and parkland like James J. Braddock Park offer green spaces amid dense development."
    },
    {
      "town": "Guttenberg",
      "description": "Tiny Hudson town atop the Palisades with dense housing and quick NYC buses.",
      "schools": "Guttenberg Public School District (Anna L. Klein School) with high school students attending North Bergen High.",
      "primary_transit": "NJ Transit and private buses along Boulevard East and Bergenline Avenue.",
      "commute_to_nyc": "Short bus rides via Lincoln Tunnel often 20\u201340 minutes door-to-door.",
      "highways": "Near Route 495 and major Hudson County arterials.",
      "notes": "One of the smallest municipalities by area in the U.S., dominated by high-rises like Galaxy Towers."
    },
    {
      "town": "Secaucus",
      "description": "Meadowlands suburb with NJ Transit hub, outlet shopping, and riverfront housing.",
      "schools": "Secaucus Public Schools serve K\u201312 students with modern facilities.",
      "primary_transit": "Secaucus Junction rail hub connects to nearly all NJ Transit lines; extensive bus network as well.",
      "commute_to_nyc": "Very fast train connections to New York Penn, often 10\u201320 minutes once onboard.",
      "highways": "Crisscrossed by NJ Turnpike, Route 3, and Route 1&9.",
      "notes": "Combination of suburban neighborhoods and large retail/employment centers."
    },
    {
      "town": "Kearny",
      "description": "Working-class town with Scottish roots, riverfront parks, and NJ Transit service.",
      "schools": "Kearny School District operates local K\u201312 schools with a single high school.",
      "primary_transit": "NJ Transit bus routes and nearby PATH access via Harrison or Newark; some regional rail access.",
      "commute_to_nyc": "Bus and PATH combinations usually 35\u201365 minutes to Manhattan.",
      "highways": "Close to I-280, the NJ Turnpike, and Truck Route 1&9.",
      "notes": "Offers more affordable options relative to neighboring waterfront Hudson towns."
    },
    {
      "town": "Harrison",
      "description": "Redeveloped riverfront city with PATH service, Red Bull Arena, and new high-rises.",
      "schools": "Harrison Public Schools provide K\u201312 education in a compact urban district.",
      "primary_transit": "PATH station at Harrison plus NJ Transit buses and proximity to Newark Penn Station.",
      "commute_to_nyc": "PATH to World Trade Center or Midtown (via transfer) often 20\u201335 minutes.",
      "highways": "Adjacent to I-280, with quick access to NJ Turnpike and Route 21.",
      "notes": "Significant transit-oriented development has reshaped its waterfront skyline."
    },
    {
      "town": "East Newark",
      "description": "Tiny borough with affordable housing and easy walk to Harrison PATH.",
      "schools": "East Newark Public School District (K\u20138); high school students attend Harrison High School.",
      "primary_transit": "Residents typically walk to Harrison PATH station and use local buses.",
      "commute_to_nyc": "Excellent transit access; PATH trips to Manhattan often 20\u201335 minutes.",
      "highways": "Near I-280 and local arterials into Newark and Jersey City.",
      "notes": "One of the smallest municipalities in New Jersey, tightly integrated with Harrison."
    }
  ],
  "Morris": [
    {
      "town": "Boonton",
      "description": "Historic town with lively Main Street, Victorian homes, and reservoir views.",
      "schools": "Served by Boonton Public Schools, with K\u201312 neighborhood schools and a small-town district feel.",
      "primary_transit": "NJ Transit Montclair-Boonton Line from Boonton Station; regional commuter buses and local roads.",
      "commute_to_nyc": "Many residents take the Montclair-Boonton Line into Hoboken or New York via transfer, typically 60\u201390 minutes door-to-door depending on schedule.",
      "highways": "Convenient to I-287, I-80, and Route 46.",
      "notes": "Walkable downtown and views of the Jersey City Reservoir appeal to buyers seeking character homes."
    },
    {
      "town": "Boonton Township",
      "description": "Quiet township with rural charm, spacious homes, and natural beauty.",
      "schools": "Local K\u20138 schools with high school students usually attending Mountain Lakes High School through a sending/receiving relationship.",
      "primary_transit": "Residents typically drive to nearby Boonton, Mountain Lakes, or Denville stations on the Montclair-Boonton or Morris & Essex lines.",
      "commute_to_nyc": "Typical commute to Midtown via train or bus is roughly 70\u2013100 minutes including drive to station and transfers.",
      "highways": "Access to I-287, Route 46, and nearby I-80.",
      "notes": "Large lots, trails, and preserved land make it attractive for buyers seeking privacy and nature."
    },
    {
      "town": "Butler",
      "description": "Historic borough with small-town character and affordable housing options.",
      "schools": "Butler Public Schools serve local students with neighborhood elementary, middle, and high schools.",
      "primary_transit": "NJ Transit buses toward Newark and NYC; nearby rail access via Wayne/Route 23 or Pompton Plains park-and-ride options.",
      "commute_to_nyc": "Many commuters take park-and-ride bus service or drive to rail stations, with total commute times around 60\u201390 minutes.",
      "highways": "Easy access to Route 23 and I-287.",
      "notes": "Older housing stock and small-town main streets appeal to value-focused buyers."
    },
    {
      "town": "Chatham Borough",
      "description": "Quaint borough with walkable downtown, top schools, and direct trains.",
      "schools": "Part of the School District of the Chathams, consistently rated among the strongest in New Jersey.",
      "primary_transit": "NJ Transit Morris & Essex Midtown Direct service from Chatham Station.",
      "commute_to_nyc": "Direct trains to New York Penn typically 40\u201350 minutes, making it a classic commuter favorite.",
      "highways": "Close to Route 24 and I-78, with access to the Garden State Parkway.",
      "notes": "Highly competitive market with strong demand from NYC professionals."
    },
    {
      "town": "Chatham Township",
      "description": "Upscale township with estate-style homes, open space, and top schools.",
      "schools": "Also served by the School District of the Chathams with high-performing K\u201312 schools.",
      "primary_transit": "Residents often use Chatham or Summit train stations on the Morris & Essex line.",
      "commute_to_nyc": "Door-to-door commute into Midtown Manhattan commonly 50\u201375 minutes via train or park-and-ride bus.",
      "highways": "Good access to Route 24, I-78, and nearby I-287.",
      "notes": "Larger lots and preserved land provide a more rural-suburban feel compared to the borough."
    },
    {
      "town": "Chester Borough",
      "description": "Quaint borough with antique shops, historic character, and rural surroundings.",
      "schools": "Chester School District (K\u20138) with high schoolers attending West Morris Mendham High School.",
      "primary_transit": "Commuters typically drive to NJ Transit stations in Gladstone, Peapack, or other Morris & Essex line towns, or use park-and-ride buses.",
      "commute_to_nyc": "Many Chester commuters plan on 75\u2013110 minutes door-to-door depending on station choice and traffic.",
      "highways": "Access to Route 206, Route 24, and I-80 via connecting roads.",
      "notes": "Downtown Chester is a regional draw with shops, restaurants, and seasonal events."
    },
    {
      "town": "Chester Township",
      "description": "Expansive rural township with preserved land, farms, and upscale homes.",
      "schools": "Also served by Chester School District and West Morris Regional High School District.",
      "primary_transit": "Similar patterns as Chester Borough: drive to Gladstone Branch or Morris & Essex line stations or park-and-ride buses.",
      "commute_to_nyc": "Expect roughly 75\u2013110 minutes to Midtown with a combination of local driving and rail/bus.",
      "highways": "Route 206 is the main spine, with connections to I-80 and I-287.",
      "notes": "Popular among buyers seeking privacy, acreage, and equestrian properties."
    },
    {
      "town": "Denville",
      "description": "Known as the 'Hub of Morris County,' with lakes, parks, and strong community.",
      "schools": "Denville Township School District for K\u20138; high school students usually attend Morris Knolls High School.",
      "primary_transit": "NJ Transit rail at Denville Station (Montclair-Boonton and Morris & Essex lines) plus commuter buses.",
      "commute_to_nyc": "Trains to Hoboken or New York (via transfer) typically run 60\u201390 minutes door-to-door.",
      "highways": "Excellent access to I-80, I-287, and Route 46.",
      "notes": "Lake communities and active civic life make it a versatile choice for commuters and families."
    },
    {
      "town": "Dover",
      "description": "Historic town with cultural diversity, walkable downtown, and major rail hub.",
      "schools": "Dover Public Schools serve a diverse student body with neighborhood K\u201312 schools.",
      "primary_transit": "Major NJ Transit rail hub on the Morris & Essex and Montclair-Boonton lines; regional bus service as well.",
      "commute_to_nyc": "Rail commute to Hoboken or Midtown (via transfer) generally 60\u201390 minutes door-to-door.",
      "highways": "Close to Route 46, Route 10, and I-80.",
      "notes": "Downtown redevelopment and transit access appeal to first-time buyers and investors."
    },
    {
      "town": "Morristown",
      "description": "Historic county seat with lively nightlife, green spaces, and direct rail.",
      "schools": "Morris School District serves Morristown and Morris Township with comprehensive K\u201312 programs.",
      "primary_transit": "NJ Transit Morris & Essex Midtown Direct service from Morristown Station.",
      "commute_to_nyc": "Direct trains to New York Penn commonly 55\u201365 minutes; Hoboken service also available.",
      "highways": "Central access to I-287, Route 24, and I-80.",
      "notes": "Highly walkable downtown, cultural venues, and employment base drive strong housing demand."
    },
    {
      "town": "Parsippany-Troy Hills",
      "description": "Large township with corporate campuses, varied neighborhoods, and commuter options.",
      "schools": "Parsippany-Troy Hills School District with multiple elementary, middle, and two high schools.",
      "primary_transit": "Commuter buses to NYC and nearby rail at Morris Plains, Mountain Lakes, or Boonton; some residents use Lakeland bus lines.",
      "commute_to_nyc": "Typical Midtown commute 60\u201390 minutes via bus or train/park-and-ride combinations.",
      "highways": "Major crossroads of I-80, I-287, Route 46, and Route 10.",
      "notes": "Strong corporate presence and diverse housing from condos to larger single-family homes."
    },
    {
      "town": "East Hanover",
      "description": "Family-oriented township with strong schools, retail centers, and highway access.",
      "schools": "East Hanover Township School District (K\u20138); high school students attend Hanover Park High School.",
      "primary_transit": "NJ Transit buses toward Newark and NYC; residents often drive to nearby Morris & Essex line stations.",
      "commute_to_nyc": "Door-to-door trips to Midtown by bus or rail generally range 60\u201390 minutes.",
      "highways": "Along Route 10 with quick access to I-280, I-287, and Route 24.",
      "notes": "Popular for its combination of suburban living and employment centers."
    },
    {
      "town": "Florham Park",
      "description": "Upscale township with strong schools, corporate campuses, and Jets training center.",
      "schools": "Florham Park School District (K\u20138) with high schoolers attending Hanover Park High School.",
      "primary_transit": "Residents typically use nearby Madison or Convent Station for Morris & Essex Midtown Direct service, plus commuter buses.",
      "commute_to_nyc": "Trains from Madison/Convent to NYC plus local driving usually total 60\u201380 minutes.",
      "highways": "Near Route 24, I-287, and Route 10.",
      "notes": "Attractive to relocating professionals and families seeking strong schools."
    },
    {
      "town": "Hanover Township",
      "description": "Convenient township with residential neighborhoods and major employment centers.",
      "schools": "Hanover Township Public Schools for K\u20138; high school students attend Whippany Park High School.",
      "primary_transit": "NJ Transit rail nearby at Morristown, Morris Plains, or East Hanover buses; park-and-ride options.",
      "commute_to_nyc": "Most commuters plan on 60\u201390 minutes via train/bus plus local driving.",
      "highways": "Central access to Route 10, I-287, I-80, and Route 24.",
      "notes": "Corporate parks and residential neighborhoods coexist, offering short local commutes."
    },
    {
      "town": "Harding Township",
      "description": "Exclusive township with estate homes, preserved land, and country club living.",
      "schools": "Harding Township School for K\u20138; high school students typically attend Madison High School.",
      "primary_transit": "Residents often drive to Morristown or Madison rail stations on the Morris & Essex line.",
      "commute_to_nyc": "Door-to-door travel to Midtown via train commonly 70\u2013100 minutes including local driving.",
      "highways": "Nearby access to I-287 and Route 24.",
      "notes": "Appeals to buyers seeking privacy, high-end properties, and rural character near Morristown."
    },
    {
      "town": "Jefferson Township",
      "description": "Lakeside township with scenic beauty, outdoor recreation, and diverse neighborhoods.",
      "schools": "Jefferson Township Public Schools serve K\u201312 students with multiple neighborhood schools.",
      "primary_transit": "Commuter buses and park-and-ride lots; some residents drive to NJ Transit stations such as Lake Hopatcong or Dover.",
      "commute_to_nyc": "Expect 75\u2013110 minutes to Manhattan via a combination of highway driving and bus or rail.",
      "highways": "Access primarily via Route 15 and I-80.",
      "notes": "Lakefront properties and wooded neighborhoods draw year-round and second-home buyers."
    },
    {
      "town": "Kinnelon",
      "description": "Affluent township with scenic hills, gated communities, and top-ranked schools.",
      "schools": "Kinnelon Public Schools with a strong academic reputation, including Kinnelon High School.",
      "primary_transit": "Commuters often use bus service along Route 23 or drive to rail stations in neighboring towns.",
      "commute_to_nyc": "Typical Midtown commute ranges from 70\u2013100 minutes depending on bus/park-and-ride choices.",
      "highways": "Convenient to Route 23 and I-287.",
      "notes": "Communities like Smoke Rise offer gated, amenity-rich living."
    },
    {
      "town": "Lincoln Park",
      "description": "Commuter-friendly borough with affordable homes and Montclair-Boonton Line station.",
      "schools": "Lincoln Park Public Schools serve local K\u20138 students; high schoolers attend Boonton High School.",
      "primary_transit": "NJ Transit Montclair-Boonton Line from Lincoln Park Station; regional buses and nearby highways.",
      "commute_to_nyc": "Rail to Hoboken or NYC via transfer typically 60\u201390 minutes total.",
      "highways": "Access to Route 23, I-80, and I-287.",
      "notes": "Appeals to buyers seeking value with direct rail access."
    },
    {
      "town": "Long Hill Township",
      "description": "Scenic township with small-town feel, top schools, and Gladstone Branch rail service.",
      "schools": "Long Hill Township School District (K\u20138); high school students attend Watchung Hills Regional High School.",
      "primary_transit": "NJ Transit Gladstone Branch stations in Stirling, Millington, and Gillette.",
      "commute_to_nyc": "Trains to Hoboken or New York (via transfer/Midtown Direct) typically take 65\u201390 minutes door-to-door.",
      "highways": "Near I-78 and Route 24 via neighboring towns.",
      "notes": "Riverfront parks and village centers create a classic small-town New Jersey feel."
    },
    {
      "town": "Madison",
      "description": "Historic borough with lively downtown, top schools, and direct Midtown trains.",
      "schools": "Madison Public Schools with strong test scores and extensive extracurriculars.",
      "primary_transit": "NJ Transit Morris & Essex Midtown Direct from Madison Station.",
      "commute_to_nyc": "Direct trains to New York Penn often around 50\u201360 minutes, making it a sought-after commuter hub.",
      "highways": "Convenient to Route 24, I-287, and I-78.",
      "notes": "Home to Drew University and Fairleigh Dickinson\u2019s Florham campus, adding a collegiate vibe."
    },
    {
      "town": "Mendham Borough",
      "description": "Quaint historic borough with top schools and a charming downtown.",
      "schools": "Mendham Borough and Mendham Township share elementary/middle schools with high schoolers at West Morris Mendham.",
      "primary_transit": "Residents typically drive to Morristown or Bernardsville train stations, or use regional bus service.",
      "commute_to_nyc": "Many commuters plan on 75\u2013105 minutes door-to-door via mix of driving and rail/bus.",
      "highways": "Access via Route 24 and local connections to I-287 and I-78.",
      "notes": "Highly rated schools and classic streetscapes attract move-up buyers."
    },
    {
      "town": "Mendham Township",
      "description": "Affluent township with rolling hills, large estates, and preserved land.",
      "schools": "Served by Mendham Township School District and West Morris Regional High School District.",
      "primary_transit": "Commuters often use train stations at Morristown, Bernardsville, or Far Hills plus park-and-ride buses.",
      "commute_to_nyc": "Door-to-door trips to Midtown can range 75\u2013110 minutes depending on route.",
      "highways": "Rural roads connect to Route 24, I-287, and I-78.",
      "notes": "Known for equestrian properties, trails, and scenic roads."
    },
    {
      "town": "Mine Hill",
      "description": "Small township with suburban feel and convenient highway access.",
      "schools": "Mine Hill Township School District for K\u20136; older students often attend schools in the Dover area.",
      "primary_transit": "Residents typically use Dover or Mt. Arlington NJ Transit stations and regional buses.",
      "commute_to_nyc": "Expect about 75\u2013105 minutes to Midtown with a mix of driving and train/bus.",
      "highways": "Close to Route 46 and I-80.",
      "notes": "Compact community with value-oriented housing."
    },
    {
      "town": "Montville",
      "description": "Affluent township with strong schools, suburban neighborhoods, and open space.",
      "schools": "Montville Township School District is well-regarded, with Montville Township High School serving grades 9\u201312.",
      "primary_transit": "Residents use Montville and Towaco stations on the Montclair-Boonton Line and regional buses.",
      "commute_to_nyc": "Typical Midtown trips via train/bus often range 65\u201395 minutes including local travel.",
      "highways": "Access to I-287, Route 46, and nearby I-80.",
      "notes": "Mix of newer subdivisions and older neighborhoods offers a range of options."
    },
    {
      "town": "Morris Township",
      "description": "Expansive township surrounding Morristown with diverse housing and strong schools.",
      "schools": "Part of the Morris School District shared with Morristown.",
      "primary_transit": "Many residents use Morristown or Convent Station on the Morris & Essex line.",
      "commute_to_nyc": "Midtown commutes typically 60\u201380 minutes via train plus local driving.",
      "highways": "Near I-287, Route 24, and Route 124.",
      "notes": "Wide range of neighborhoods from historic areas to newer developments."
    },
    {
      "town": "Mount Arlington",
      "description": "Lake Hopatcong community with strong recreation and rail access.",
      "schools": "Mount Arlington Public Schools for K\u20138; high schoolers often attend Roxbury High School.",
      "primary_transit": "NJ Transit Montclair-Boonton Line at Mount Arlington Station; park-and-ride for regional buses.",
      "commute_to_nyc": "Trains to Hoboken or NYC (via transfer) plus local driving often total 75\u2013105 minutes.",
      "highways": "Just off I-80 with connections to Route 46 and Route 10.",
      "notes": "Popular with buyers seeking lake access and newer townhome/condo communities."
    },
    {
      "town": "Mount Olive",
      "description": "Large township with diverse neighborhoods, shopping, and transit options.",
      "schools": "Mount Olive Township School District with comprehensive K\u201312 offerings and a large high school.",
      "primary_transit": "NJ Transit Montclair-Boonton and Morristown lines at nearby stations; local buses and park-and-ride lots.",
      "commute_to_nyc": "Many residents commute 75\u2013110 minutes via bus or rail plus highway driving.",
      "highways": "Strong access to I-80, Route 46, and Route 206.",
      "notes": "Includes communities like Flanders and Budd Lake with a mix of housing types."
    },
    {
      "town": "Mountain Lakes",
      "description": "Prestigious lake community with Tudor-style homes and natural beauty.",
      "schools": "Mountain Lakes School District is highly ranked, with Mountain Lakes High School known statewide.",
      "primary_transit": "NJ Transit rail from Mountain Lakes Station on the Montclair-Boonton Line; regional buses.",
      "commute_to_nyc": "Trips to Hoboken or NYC (via transfer) typically about 70\u2013100 minutes door-to-door.",
      "highways": "Near Route 46, I-80, and I-287.",
      "notes": "Signature early-1900s architecture and lake setting attract high-end buyers."
    },
    {
      "town": "Pequannock Township",
      "description": "Family-friendly township with suburban neighborhoods, parks, and strong community.",
      "schools": "Pequannock Township School District serves K\u201312 students with local schools.",
      "primary_transit": "Commuters frequently use buses along Route 23 or rail from neighboring Lincoln Park or Pompton Plains areas.",
      "commute_to_nyc": "Midtown trips via bus/rail and local driving are often 60\u201390 minutes.",
      "highways": "Access to Route 23, I-287, and Route 80 via nearby connections.",
      "notes": "Parks and riverfront areas offer outdoor recreation close to major job centers."
    },
    {
      "town": "Randolph",
      "description": "Large suburban township with top schools, parks, and family amenities.",
      "schools": "Randolph Township Schools are highly regarded, with a full K\u201312 pathway and strong extracurriculars.",
      "primary_transit": "Residents often drive to Dover, Denville, or Morristown for NJ Transit trains, or use commuter buses.",
      "commute_to_nyc": "Most commuters plan on 75\u2013105 minutes via car plus train or bus to Midtown.",
      "highways": "Near Route 10, Route 46, and I-80.",
      "notes": "Extensive trail system and recreation department make it a favorite for active families."
    },
    {
      "town": "Riverdale",
      "description": "Small suburban borough with easy access to highways and shopping.",
      "schools": "Riverdale School District (K\u20138); high school students attend Pompton Lakes High School.",
      "primary_transit": "NJ Transit bus service along Route 23; rail access via nearby towns for some commuters.",
      "commute_to_nyc": "Bus/park-and-ride commutes typically 60\u201390 minutes door-to-door.",
      "highways": "Excellent access to Route 23, I-287, and I-80.",
      "notes": "Compact size and highway convenience appeal to commuters seeking shorter local drives."
    },
    {
      "town": "Rockaway Borough",
      "description": "Small historic borough with Main Street charm and suburban living.",
      "schools": "Rockaway Borough School District for K\u20138; high schoolers attend Morris Hills High School.",
      "primary_transit": "Residents often use Dover or Denville NJ Transit stations and regional bus routes.",
      "commute_to_nyc": "Expect 75\u2013105 minutes to Midtown via combination of local driving and train/bus.",
      "highways": "Near Route 46 and I-80.",
      "notes": "Walkable downtown and older housing stock offer a classic feel."
    },
    {
      "town": "Rockaway Township",
      "description": "Large township with diverse neighborhoods, parks, and shopping centers.",
      "schools": "Rockaway Township Public Schools serve most of the township; high schoolers attend Morris Hills or Morris Knolls.",
      "primary_transit": "Commuters typically use Denville, Dover, or Mount Arlington rail stations and park-and-ride buses.",
      "commute_to_nyc": "Door-to-door times commonly 75\u2013110 minutes via bus/rail plus local driving.",
      "highways": "Strong access to I-80, Route 15, and Route 46.",
      "notes": "Includes developed and more rural sections, plus access to lakes and parks."
    },
    {
      "town": "Roxbury Township",
      "description": "Township with lake communities, shopping, and strong schools.",
      "schools": "Roxbury Township Public Schools, including Roxbury High School, serve the community.",
      "primary_transit": "NJ Transit rail at Mount Arlington and nearby stations; commuter buses along major corridors.",
      "commute_to_nyc": "Typical Midtown trips 75\u2013110 minutes via bus/rail plus highway driving.",
      "highways": "Well-positioned along Route 10, Route 46, and I-80.",
      "notes": "Includes Succasunna, Landing, and other neighborhoods with varied housing styles."
    },
    {
      "town": "Victory Gardens",
      "description": "Small urban borough with affordable housing and diverse community.",
      "schools": "Students generally attend Dover Public Schools through a sending/receiving relationship.",
      "primary_transit": "Residents frequently use Dover Station on the Morris & Essex line or regional buses.",
      "commute_to_nyc": "Door-to-door Midtown commutes typically 70\u2013100 minutes.",
      "highways": "Close to Route 46 and I-80.",
      "notes": "Compact and densely populated with easy access to Dover\u2019s amenities."
    },
    {
      "town": "Washington Township",
      "description": "Expansive rural-suburban township with farms, open space, and top schools.",
      "schools": "Washington Township School District and West Morris Central High School serve local students.",
      "primary_transit": "Many residents drive to rail stations in Chester, Hackettstown, or other neighboring towns, or use park-and-ride bus lots.",
      "commute_to_nyc": "Often 80\u2013120 minutes to Midtown via car plus train/bus.",
      "highways": "Served primarily by Route 46 and Route 57 with connections to I-80.",
      "notes": "Appeals to buyers seeking more land, rural character, and strong schools."
    },
    {
      "town": "Wharton",
      "description": "Historic borough with affordable homes, parks, and highway convenience.",
      "schools": "Wharton Borough School District (K\u20138); high schoolers attend Morris Hills High School.",
      "primary_transit": "Commuters typically use Dover or Denville stations and park-and-ride bus services.",
      "commute_to_nyc": "Midtown Manhattan commutes usually 75\u2013105 minutes total.",
      "highways": "Excellent access to I-80 and Route 15.",
      "notes": "Small-town vibe with quick access to regional shopping and jobs."
    }
  ],
  "Middlesex": [
    {
      "town": "New Brunswick",
      "description": "University city with cultural venues, rail hub, and redevelopment.",
      "schools": "New Brunswick Public Schools plus Rutgers University anchoring higher education and research.",
      "primary_transit": "NJ Transit Northeast Corridor at New Brunswick Station; extensive local and coach bus network.",
      "commute_to_nyc": "Direct trains to New York Penn typically 45\u201360 minutes depending on express vs local service.",
      "highways": "Near Routes 18 and 27, the NJ Turnpike, and Route 1.",
      "notes": "Major medical, educational, and cultural center with significant rental and condo markets."
    },
    {
      "town": "Edison",
      "description": "Sprawling suburb with major transit hubs, shopping, and diverse housing.",
      "schools": "Edison Township Public Schools serve a large, diverse K\u201312 population with multiple high schools.",
      "primary_transit": "Metropark and Edison stations on the Northeast Corridor, plus many NJ Transit and private buses.",
      "commute_to_nyc": "Express trains from Metropark can reach New York Penn in about 35\u201345 minutes.",
      "highways": "Crisscrossed by the Garden State Parkway, NJ Turnpike, Route 1, Route 27, and Route 287.",
      "notes": "One of New Jersey\u2019s largest townships with strong demand from commuters and investors."
    },
    {
      "town": "Carteret",
      "description": "Industrial-riverfront borough with new waterfront redevelopment and strong highway access.",
      "schools": "Carteret Public Schools operate local K\u201312 schools with recent facility upgrades.",
      "primary_transit": "NJ Transit buses to Newark and NYC; planned or emerging ferry service has been discussed for the waterfront.",
      "commute_to_nyc": "Bus and park-and-ride commutes commonly 45\u201375 minutes to Manhattan.",
      "highways": "Excellent access to NJ Turnpike, Route 1&9, and Route 440.",
      "notes": "Redevelopment on the Arthur Kill is transforming former industrial sites into residential and recreational areas."
    },
    {
      "town": "Cranbury",
      "description": "Historic rural-suburban township with colonial charm and preserved farmland.",
      "schools": "Cranbury School District for K\u20138 with high schoolers attending Princeton High School.",
      "primary_transit": "Residents usually drive to nearby Princeton Junction or New Brunswick for NJ Transit trains, or use park-and-ride buses along Route 130 and Route 1.",
      "commute_to_nyc": "Door-to-door commutes to Manhattan via rail or bus often 70\u2013100 minutes.",
      "highways": "Strategically located near NJ Turnpike Exit 8A and Route 130.",
      "notes": "Quaint village center and strict farmland preservation policies keep it low-density."
    },
    {
      "town": "East Brunswick",
      "description": "Large suburban township with top-rated schools, diverse housing, and major highways.",
      "schools": "East Brunswick Public Schools widely regarded for strong academics and music programs.",
      "primary_transit": "NJ Transit and private commuter buses from park-and-ride lots (notably the Turnpike and Route 18) into NYC.",
      "commute_to_nyc": "Express buses to Port Authority often 45\u201370 minutes depending on traffic.",
      "highways": "Major interchange of NJ Turnpike, Route 18, and Route 1 nearby.",
      "notes": "Popular with commuters wanting strong schools without direct rail."
    },
    {
      "town": "Helmetta",
      "description": "Tiny borough with small-town feel and historic snuff mill heritage.",
      "schools": "Students typically attend Spotswood Public Schools through sending/receiving relationships.",
      "primary_transit": "Residents use regional buses and drive to nearby rail in South Amboy or New Brunswick.",
      "commute_to_nyc": "Most commuters plan on 70\u2013100 minutes via park-and-ride bus or rail connections.",
      "highways": "Access to Route 130, Route 18, and NJ Turnpike via neighboring towns.",
      "notes": "Quiet residential streets appeal to buyers seeking a tucked-away feel."
    },
    {
      "town": "Highland Park",
      "description": "Walkable borough across from New Brunswick, with strong community and schools.",
      "schools": "Highland Park Public Schools serve K\u201312 students with a close-knit district.",
      "primary_transit": "Residents often walk or bus into New Brunswick Station for Northeast Corridor rail; local buses run along Route 27.",
      "commute_to_nyc": "Rail from New Brunswick to New York Penn plus local access is often 60\u201380 minutes door-to-door.",
      "highways": "Access to Route 27, Route 1, and nearby NJ Turnpike interchanges.",
      "notes": "Historic housing stock and walkable streets draw faculty, students, and professionals."
    },
    {
      "town": "Jamesburg",
      "description": "Compact borough with suburban lifestyle and Monroe Township amenities nearby.",
      "schools": "Jamesburg Public Schools for K\u20138; high school students typically attend Monroe Township High School.",
      "primary_transit": "Bus routes and park-and-ride access toward NYC via Routes 18, 33, and NJ Turnpike.",
      "commute_to_nyc": "Most commuters expect 70\u2013100 minutes to Manhattan via bus or mixed modes.",
      "highways": "Close to NJ Turnpike Exit 8A and Route 33.",
      "notes": "Small-town center with easy access to larger township services."
    },
    {
      "town": "Metuchen",
      "description": "Charming walkable borough with direct NEC trains and vibrant downtown.",
      "schools": "Metuchen School District offers K\u201312 schooling with a strong reputation for academics.",
      "primary_transit": "NJ Transit Northeast Corridor from Metuchen Station with frequent service.",
      "commute_to_nyc": "Express trains to New York Penn can be around 40\u201350 minutes, making this a premier rail suburb.",
      "highways": "Near the Garden State Parkway, Route 1, and Route 27.",
      "notes": "Known for its \"Brainy Borough\" identity and active downtown businesses."
    },
    {
      "town": "Middlesex",
      "description": "Borough on the Raritan Valley Line with suburban neighborhoods and local parks.",
      "schools": "Middlesex Borough Public Schools serve local K\u201312 students.",
      "primary_transit": "NJ Transit Raritan Valley Line from Bound Brook and Dunellen stations nearby; local buses.",
      "commute_to_nyc": "Commuters often take RVL trains via Newark into NYC, typically 70\u2013100 minutes total.",
      "highways": "Access to Route 28, I-287, and Route 22.",
      "notes": "Residential community with convenient access to Somerset County and Rutgers area."
    },
    {
      "town": "Milltown",
      "description": "Small borough with historic charm, Mill Pond, and suburban neighborhoods.",
      "schools": "Milltown Public Schools for K\u20138; high school students attend Spotswood High School.",
      "primary_transit": "Regional buses and nearby rail in New Brunswick, Edison, or East Brunswick park-and-ride lots.",
      "commute_to_nyc": "Most commuters plan on 70\u2013100 minutes via bus/train combos.",
      "highways": "Convenient to Route 1, Route 18, and NJ Turnpike interchanges.",
      "notes": "Quaint downtown and water features create a village-like feel."
    },
    {
      "town": "Monroe Township",
      "description": "Large suburban-rural township with retirement communities, open space, and golf courses.",
      "schools": "Monroe Township School District for K\u201312 with a large modern high school.",
      "primary_transit": "Park-and-ride buses along Routes 33 and 130 to NYC and North Jersey.",
      "commute_to_nyc": "Express buses to Midtown can run 60\u201390 minutes depending on traffic.",
      "highways": "Easy access to NJ Turnpike, Route 33, and Route 130.",
      "notes": "Popular for active adult communities as well as traditional single-family developments."
    },
    {
      "town": "North Brunswick",
      "description": "Large suburban township with diverse housing, major retail, and growing development.",
      "schools": "North Brunswick Township Schools handle local K\u201312 education, with a large high school campus.",
      "primary_transit": "Park-and-ride buses on Routes 130 and 1; a new rail station is planned along the NEC corridor.",
      "commute_to_nyc": "Bus and future rail service generally mean 60\u201390 minute commutes to Midtown.",
      "highways": "Located along Route 1 and close to NJ Turnpike and Route 130.",
      "notes": "New mixed-use developments and central location keep demand strong."
    },
    {
      "town": "Old Bridge",
      "description": "Expansive township with suburban neighborhoods, waterfront parks, and Route 9 retail.",
      "schools": "Old Bridge Township Public Schools operate numerous K\u201312 schools across the large township.",
      "primary_transit": "NJ Transit and private buses along Route 9 to NYC park-and-ride facilities.",
      "commute_to_nyc": "Rush-hour bus commutes to Port Authority commonly 60\u201390 minutes depending on congestion.",
      "highways": "Route 9, Route 18, Garden State Parkway, and Route 35 nearby.",
      "notes": "Varied housing stock from townhomes to larger colonials near the Raritan Bay."
    },
    {
      "town": "Perth Amboy",
      "description": "Historic waterfront city with diverse housing, cultural amenities, and NJCL rail.",
      "schools": "Perth Amboy Public Schools provide K\u201312 education with several neighborhood schools.",
      "primary_transit": "NJ Transit North Jersey Coast Line from Perth Amboy Station plus buses and nearby ferry options.",
      "commute_to_nyc": "Trains and buses to NYC typically 60\u201390 minutes depending on route and transfers.",
      "highways": "Close to the Outerbridge Crossing, Route 35, Route 440, and the Garden State Parkway.",
      "notes": "Waterfront redevelopment and historic districts offer investment and lifestyle opportunities."
    },
    {
      "town": "Piscataway",
      "description": "Large township with Rutgers campus, suburban neighborhoods, and Raritan River parks.",
      "schools": "Piscataway Township Schools plus portions of Rutgers University\u2019s Busch and Livingston campuses.",
      "primary_transit": "Nearby NJ Transit stations at New Brunswick, Edison, and Rutgers area buses; park-and-ride options.",
      "commute_to_nyc": "Most commuters use NEC rail or buses, planning on 60\u201390 minutes door-to-door.",
      "highways": "Intersected by I-287, Route 18, and Route 28 with access to Route 1.",
      "notes": "Draws a mix of families, students, and university staff."
    },
    {
      "town": "Sayreville",
      "description": "Suburban-riverfront township with Raritan Bay access, Route 9 shopping, and cultural diversity.",
      "schools": "Sayreville Public Schools serve local K\u201312 students with multiple neighborhood schools.",
      "primary_transit": "NJ Transit and private buses along Route 9 plus park-and-ride lots toward NYC.",
      "commute_to_nyc": "Typical bus commutes 60\u201390 minutes depending on traffic on Route 9 and approaches to NYC.",
      "highways": "Route 9, Garden State Parkway, Route 35, and Route 18 nearby.",
      "notes": "Riverfront and bayfront areas continue to redevelop with residential communities."
    },
    {
      "town": "South Amboy",
      "description": "Bayfront city with NJCL rail service, ferry access, and waterfront redevelopment.",
      "schools": "South Amboy Public Schools operate a small K\u201312 system.",
      "primary_transit": "NJ Transit North Jersey Coast Line at South Amboy Station and ferry service toward Manhattan when operating.",
      "commute_to_nyc": "Rail and ferry options can make commutes 60\u201390 minutes depending on schedules.",
      "highways": "Near Garden State Parkway, Route 9, and Route 35.",
      "notes": "Waterfront redevelopment and transit access make it attractive to commuters."
    },
    {
      "town": "South Plainfield",
      "description": "Suburban township with strong schools, shopping centers, and community parks.",
      "schools": "South Plainfield Public Schools serve local K\u201312 students.",
      "primary_transit": "Commuters use buses along Route 22 and I-287 corridors or drive to nearby NJ Transit stations.",
      "commute_to_nyc": "Most plan for 70\u2013100 minute commutes using a mix of car, bus, and rail.",
      "highways": "Close to I-287, Route 22, and Route 27.",
      "notes": "Industrial parks and retail centers coexist with residential neighborhoods."
    },
    {
      "town": "South River",
      "description": "Diverse small borough with strong cultural heritage and affordable housing.",
      "schools": "South River Public Schools provide K\u201312 education.",
      "primary_transit": "Regional buses and nearby park-and-ride lots in East Brunswick and Old Bridge.",
      "commute_to_nyc": "Bus commutes commonly 70\u2013100 minutes to Midtown depending on traffic.",
      "highways": "Access via Route 18, Route 9, and NJ Turnpike interchanges nearby.",
      "notes": "Historic neighborhoods and ethnic eateries add local character."
    },
    {
      "town": "Spotswood",
      "description": "Small suburban borough with strong schools and community feel.",
      "schools": "Spotswood Public Schools serve Spotswood and some neighboring sending districts.",
      "primary_transit": "Commuters rely on park-and-ride bus service from nearby East Brunswick and Old Bridge.",
      "commute_to_nyc": "Buses to Port Authority often 70\u2013100 minutes including local driving.",
      "highways": "Close to Route 18, Route 9, and NJ Turnpike via connectors.",
      "notes": "Compact, close-knit community with local parks and neighborhood streets."
    },
    {
      "town": "Woodbridge",
      "description": "Large, diverse township with multiple neighborhoods, shopping, and direct NEC/NJCL trains.",
      "schools": "Woodbridge Township School District is one of the largest in the state, serving numerous neighborhoods and schools.",
      "primary_transit": "Multiple NJ Transit stations (Woodbridge, Avenel, Metropark nearby) plus extensive bus network.",
      "commute_to_nyc": "Express trains from Metropark/Woodbridge can be 35\u201355 minutes to New York Penn.",
      "highways": "NJ Turnpike, Garden State Parkway, Route 1&9, Route 35, and Route 440 intersect here.",
      "notes": "Encompasses many distinct sections, each with its own character and price points."
    }
  ]
};
