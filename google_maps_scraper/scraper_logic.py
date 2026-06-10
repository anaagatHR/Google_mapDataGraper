from playwright.sync_api import sync_playwright
from dataclasses import dataclass, asdict, field
import os
import time
import json
import re

@dataclass
class Business:
    name: str = None
    address: str = None
    website: str = None
    phone_number: str = None
    reviews_count: int = None
    reviews_average: float = None
    latitude: float = None
    longitude: float = None
    status: str = "New"
    notes: str = ""

@dataclass
class BusinessList:
    business_list: list[Business] = field(default_factory=list)

# ── City → Areas/Neighbourhoods (Worldwide) ───────────────────────────────────
CITY_AREAS = {

    # ── INDIA ─────────────────────────────────────────────────────────────────
    "jaipur": [
        "Malviya Nagar","Vaishali Nagar","Mansarovar","Pratap Nagar",
        "Raja Park","C-Scheme","Tonk Road","Ajmer Road","Sodala",
        "Sanganer","Murlipura","Jhotwara","Shastri Nagar","Nirman Nagar",
        "Durgapura","Lalkothi","Sitapura","Jagatpura","Vidyadhar Nagar",
        "Bapu Nagar","Triveni Nagar","Kanakpura","Kukas","Khatipura",
        "Adarsh Nagar","Sindhi Camp","Johari Bazar","Bani Park",
        "Gopalpura","New Sanganer Road","Tonk Phatak","Kartarpura",
        "Vidhyadhar Nagar","Ambabari","Imli Phatak","80 Feet Road",
    ],
    "delhi": [
        "Connaught Place","Lajpat Nagar","Saket","Dwarka","Rohini",
        "Pitampura","Janakpuri","Karol Bagh","Vasant Kunj","Greater Kailash",
        "South Extension","Defence Colony","Hauz Khas","Nehru Place",
        "Okhla","Shahdara","Preet Vihar","Mayur Vihar","Uttam Nagar",
        "Paschim Vihar","Rajouri Garden","Tilak Nagar","Laxmi Nagar",
        "Chandni Chowk","Katwaria Sarai","Munirka","RK Puram",
        "Dwarka Sector 10","Dwarka Sector 12","Patparganj","Geeta Colony",
    ],
    "new delhi": [
        "Connaught Place","Lajpat Nagar","Saket","Dwarka","Rohini",
        "Pitampura","Janakpuri","Karol Bagh","Vasant Kunj","Greater Kailash",
        "Hauz Khas","Nehru Place","Okhla","Chandni Chowk","RK Puram",
    ],
    "mumbai": [
        "Andheri West","Andheri East","Bandra West","Bandra East",
        "Borivali","Dadar","Kurla","Malad","Goregaon","Kandivali",
        "Thane","Powai","Vikhroli","Ghatkopar","Mulund","Worli",
        "Lower Parel","Chembur","Juhu","Santacruz","Khar",
        "Versova","Oshiwara","Jogeshwari","Mira Road","Navi Mumbai",
    ],
    "bangalore": [
        "Koramangala","Indiranagar","Whitefield","JP Nagar","Jayanagar",
        "BTM Layout","HSR Layout","Electronic City","Marathahalli",
        "Bellandur","Sarjapur Road","Banashankari","Rajajinagar",
        "Malleshwaram","Yelahanka","Hebbal","KR Puram","Bommanahalli",
        "Brookefield","Mahadevapura","Varthur","Domlur","Richmond Town",
    ],
    "bengaluru": [
        "Koramangala","Indiranagar","Whitefield","JP Nagar","Jayanagar",
        "BTM Layout","HSR Layout","Electronic City","Marathahalli","Bellandur",
    ],
    "hyderabad": [
        "Banjara Hills","Jubilee Hills","Madhapur","Gachibowli",
        "Kondapur","Hitech City","Begumpet","Secunderabad","Ameerpet",
        "Kukatpally","Miyapur","LB Nagar","Dilsukhnagar","Uppal",
        "Kompally","Bachupally","Alwal","Trimulgherry","Tarnaka",
    ],
    "chennai": [
        "Anna Nagar","T Nagar","Velachery","Adyar","Besant Nagar",
        "Nungambakkam","Perambur","Tambaram","Porur","Chromepet",
        "Sholinganallur","Mogappair","Ambattur","Guindy","OMR",
        "Thoraipakkam","Medavakkam","Pallikaranai","Perungudi",
    ],
    "pune": [
        "Koregaon Park","Viman Nagar","Wakad","Baner","Aundh",
        "Kothrud","Hadapsar","Kondhwa","Shivajinagar","Kharadi",
        "Magarpatta","Pimple Saudagar","Hinjewadi","Warje","Deccan",
        "Kalyani Nagar","Mundhwa","Fatima Nagar","Katraj","Ambegaon",
    ],
    "ahmedabad": [
        "Navrangpura","Satellite","Vastrapur","Maninagar","Bopal",
        "Prahlad Nagar","Chandkheda","Naroda","Gota","Thaltej",
        "Bodakdev","Paldi","Naranpura","SG Road","Ambawadi",
        "Vejalpur","Nikol","Odhav","Vatva","Isanpur",
    ],
    "kolkata": [
        "Park Street","Salt Lake","New Town","Howrah","Dum Dum",
        "Ballygunge","Behala","Kasba","Tollygunge","Jadavpur",
        "Rajarhat","Ultadanga","Sealdah","Burrabazar","Gariahat",
    ],
    "lucknow": [
        "Hazratganj","Gomti Nagar","Aliganj","Indira Nagar",
        "Rajajipuram","Alambagh","Chinhat","Vikas Nagar",
        "Mahanagar","Jankipuram","Vrindavan Yojana","Sushant Golf City",
    ],
    "surat": [
        "Adajan","Vesu","Athwalines","Katargam","Varachha",
        "Piplod","Pal","City Light","Bhatar","Althan",
    ],
    "nagpur": [
        "Dharampeth","Sadar","Sitabuldi","Ramdaspeth","Pratap Nagar",
        "Manish Nagar","Hingna","Wadi","Kamptee","Amravati Road",
    ],
    "indore": [
        "Vijay Nagar","Scheme 54","Palasia","MG Road","Rau",
        "Nipania","Bhawarkuan","Banganga","Old Palasia","Khandwa Road",
    ],
    "bhopal": [
        "MP Nagar","Arera Colony","Kolar Road","Bawadia Kalan",
        "Hoshangabad Road","Ayodhya Nagar","Piplani","Berasia Road",
    ],
    "chandigarh": [
        "Sector 17","Sector 22","Sector 34","Sector 35","Sector 43",
        "Sector 44","Panchkula","Mohali","Zirakpur","IT Park",
    ],
    "coimbatore": [
        "RS Puram","Gandhipuram","Saibaba Colony","Peelamedu",
        "Vadavalli","Singanallur","Thudiyalur","Hopes College",
    ],
    "visakhapatnam": [
        "Madhurawada","Gajuwaka","MVP Colony","Dwaraka Nagar",
        "Seethammadhara","Rushikonda","Bheemunipatnam",
    ],
    "kochi": [
        "Ernakulam","Kakkanad","Edapally","Aluva","Thevara",
        "Vyttila","Kaloor","MG Road","Marine Drive","Vytilla",
    ],

    # ── USA ───────────────────────────────────────────────────────────────────
    "new york": [
        "Manhattan","Brooklyn","Queens","Bronx","Staten Island",
        "Harlem","Upper East Side","Upper West Side","Midtown",
        "Lower Manhattan","SoHo","Tribeca","Chelsea","Greenwich Village",
        "East Village","Lower East Side","Williamsburg","Bushwick",
        "Astoria","Jackson Heights","Flushing","Jamaica","Ridgewood",
        "Bedford-Stuyvesant","Park Slope","Crown Heights","Flatbush",
        "Bay Ridge","Bensonhurst","Coney Island","Forest Hills",
    ],
    "new york city": [
        "Manhattan","Brooklyn","Queens","Bronx","Staten Island",
        "Harlem","Upper East Side","Midtown","Lower Manhattan","SoHo",
        "Williamsburg","Astoria","Flushing","Park Slope","Flatbush",
    ],
    "los angeles": [
        "Hollywood","Beverly Hills","Santa Monica","Venice Beach",
        "Downtown LA","Koreatown","Westwood","Silver Lake","Echo Park",
        "Los Feliz","Culver City","Inglewood","Pasadena","Glendale",
        "Burbank","Long Beach","Torrance","Compton","Boyle Heights",
        "Eagle Rock","Highland Park","Brentwood","Pacific Palisades",
        "Westchester","El Segundo","Hawthorne","Gardena",
    ],
    "chicago": [
        "Loop","Lincoln Park","Wicker Park","Bucktown","Lakeview",
        "Rogers Park","Hyde Park","Pilsen","Bridgeport","Wrigleyville",
        "Gold Coast","River North","Streeterville","Andersonville",
        "Edgewater","Uptown","Logan Square","Humboldt Park","Austin",
        "Oak Park","Evanston","Cicero","Berwyn","Schaumburg",
    ],
    "houston": [
        "Downtown","Midtown","Heights","Montrose","Galleria",
        "Medical Center","River Oaks","Sugar Land","Katy","Pearland",
        "The Woodlands","Spring","Humble","Pasadena","Baytown",
        "Clear Lake","Memorial","Bellaire","West University","Meyerland",
    ],
    "phoenix": [
        "Downtown","Scottsdale","Tempe","Mesa","Glendale",
        "Chandler","Gilbert","Peoria","Surprise","Avondale",
        "Goodyear","Ahwatukee","Arcadia","Biltmore","Camelback",
    ],
    "philadelphia": [
        "Center City","South Philly","North Philly","West Philly",
        "Fishtown","Northern Liberties","Manayunk","Chestnut Hill",
        "Germantown","Kensington","Frankford","Northeast Philadelphia",
    ],
    "san antonio": [
        "Downtown","Alamo Heights","Stone Oak","Helotes","Converse",
        "Universal City","Leon Valley","Pleasanton","New Braunfels",
        "Northside","Southside","Westside","Medical Center",
    ],
    "san diego": [
        "Downtown","Gaslamp Quarter","Mission Valley","Pacific Beach",
        "Ocean Beach","La Jolla","North Park","Hillcrest","Chula Vista",
        "El Cajon","Escondido","Santee","Poway","Encinitas","Carlsbad",
    ],
    "dallas": [
        "Downtown","Uptown","Deep Ellum","Oak Cliff","East Dallas",
        "North Dallas","Plano","Richardson","Garland","Irving",
        "Arlington","Grand Prairie","Denton","Frisco","McKinney",
    ],
    "san francisco": [
        "Downtown","SOMA","Mission District","Castro","Haight-Ashbury",
        "North Beach","Chinatown","Financial District","Marina","Pacific Heights",
        "Sunset District","Richmond District","Excelsior","Bayview","Potrero Hill",
    ],
    "seattle": [
        "Downtown","Capitol Hill","Fremont","Ballard","West Seattle",
        "South Seattle","Beacon Hill","Columbia City","Bellevue","Redmond",
        "Kirkland","Bothell","Renton","Kent","Federal Way","Auburn",
    ],
    "denver": [
        "Downtown","LoDo","Capitol Hill","Five Points","Curtis Park",
        "Congress Park","Wash Park","Cherry Creek","Aurora","Lakewood",
        "Westminster","Thornton","Arvada","Englewood","Highlands Ranch",
    ],
    "boston": [
        "Downtown","Back Bay","South End","Fenway","Jamaica Plain",
        "Roxbury","Dorchester","South Boston","Charlestown","East Boston",
        "Cambridge","Somerville","Brookline","Newton","Quincy",
    ],
    "las vegas": [
        "Strip","Downtown","Henderson","Summerlin","Green Valley",
        "Centennial Hills","North Las Vegas","Spring Valley","Enterprise",
        "Paradise","Whitney","Sunrise Manor","Winchester",
    ],
    "miami": [
        "Downtown","Brickell","Wynwood","Little Havana","Little Haiti",
        "Coral Gables","Coconut Grove","South Beach","North Miami",
        "Hialeah","Homestead","Kendall","Aventura","Doral",
    ],
    "atlanta": [
        "Downtown","Midtown","Buckhead","Decatur","Virginia-Highland",
        "Little Five Points","East Atlanta","Marietta","Smyrna","Sandy Springs",
        "Dunwoody","Roswell","Alpharetta","Peachtree City","Stockbridge",
    ],
    "austin": [
        "Downtown","East Austin","South Congress","Hyde Park","Bouldin Creek",
        "Travis Heights","Mueller","Cedar Park","Round Rock","Georgetown",
        "Pflugerville","Leander","Kyle","Buda","San Marcos",
    ],
    "washington dc": [
        "Capitol Hill","Georgetown","Dupont Circle","Adams Morgan","Logan Circle",
        "Columbia Heights","Shaw","Navy Yard","Northeast DC","Southeast DC",
        "Arlington","Alexandria","Bethesda","Silver Spring","Rockville",
    ],
    "minneapolis": [
        "Downtown","Uptown","Northeast","South Minneapolis","North Minneapolis",
        "St Paul","Bloomington","Eden Prairie","Plymouth","Maple Grove",
    ],
    "portland": [
        "Downtown","Pearl District","Northwest","Northeast","Southeast",
        "Hawthorne","Alberta Arts District","Beaverton","Gresham","Lake Oswego",
    ],
    "nashville": [
        "Downtown","East Nashville","Germantown","12 South","Gulch",
        "Midtown","West End","Antioch","Brentwood","Franklin","Murfreesboro",
    ],

    # ── UK ────────────────────────────────────────────────────────────────────
    "london": [
        "City of London","Westminster","Chelsea","Kensington","Notting Hill",
        "Shoreditch","Canary Wharf","Greenwich","Hackney","Islington",
        "Camden","Brixton","Croydon","Richmond","Wimbledon",
        "Fulham","Hammersmith","Shepherds Bush","Clapham","Battersea",
        "Peckham","Lewisham","Stratford","Ilford","Ealing",
        "Chiswick","Hounslow","Twickenham","Kingston","Tooting",
        "Wandsworth","Putney","Wembley","Harrow","Barnet",
    ],
    "manchester": [
        "City Centre","Salford","Trafford","Didsbury","Chorlton",
        "Fallowfield","Withington","Levenshulme","Rusholme","Ancoats",
        "Stockport","Bury","Bolton","Oldham","Rochdale",
    ],
    "birmingham": [
        "City Centre","Edgbaston","Moseley","Solihull","Sutton Coldfield",
        "Sparkhill","Small Heath","Selly Oak","Kings Heath","Hall Green",
        "Erdington","Perry Barr","Handsworth","West Bromwich","Wolverhampton",
    ],
    "leeds": [
        "City Centre","Headingley","Chapel Allerton","Roundhay","Horsforth",
        "Kirkstall","Burley","Hyde Park","Harehills","Beeston",
    ],
    "glasgow": [
        "City Centre","West End","Southside","East End","Finnieston",
        "Merchant City","Govan","Pollokshields","Shawlands","Partick",
    ],
    "edinburgh": [
        "Old Town","New Town","Leith","Morningside","Bruntsfield",
        "Stockbridge","Marchmont","Portobello","Corstorphine","Gilmerton",
    ],
    "bristol": [
        "City Centre","Clifton","Redland","Southville","Bedminster",
        "Stokes Croft","Easton","St George","Henleaze","Bishopston",
    ],
    "liverpool": [
        "City Centre","Toxteth","Kensington","Anfield","Walton",
        "Aigburth","Allerton","Wavertree","West Derby","Birkenhead",
    ],

    # ── AUSTRALIA ─────────────────────────────────────────────────────────────
    "sydney": [
        "CBD","Surry Hills","Newtown","Glebe","Pyrmont",
        "Darlinghurst","Redfern","Paddington","Bondi","Coogee",
        "Manly","North Sydney","Chatswood","Parramatta","Blacktown",
        "Penrith","Liverpool","Campbelltown","Hornsby","Sutherland",
        "Balmain","Leichhardt","Marrickville","Mascot","Zetland",
    ],
    "melbourne": [
        "CBD","Fitzroy","Collingwood","Richmond","South Yarra",
        "Prahran","St Kilda","Brunswick","Carlton","Northcote",
        "Thornbury","Footscray","Williamstown","Brighton","Caulfield",
        "Clayton","Box Hill","Doncaster","Ringwood","Frankston",
        "Dandenong","Craigieburn","Sunbury","Werribee","Geelong",
    ],
    "brisbane": [
        "CBD","South Brisbane","West End","Fortitude Valley","Newstead",
        "New Farm","Teneriffe","Hamilton","Chermside","Carindale",
        "Capalaba","Sunnybank","Indooroopilly","Toowong","Ipswich",
    ],
    "perth": [
        "CBD","Fremantle","Subiaco","Leederville","Mount Lawley",
        "Northbridge","Victoria Park","Cannington","Midland","Joondalup",
        "Rockingham","Mandurah","Armadale","Stirling","Wanneroo",
    ],
    "adelaide": [
        "CBD","North Adelaide","Norwood","Glenelg","Port Adelaide",
        "Prospect","Unley","Salisbury","Tea Tree Gully","Marion",
    ],

    # ── CANADA ────────────────────────────────────────────────────────────────
    "toronto": [
        "Downtown","Midtown","North York","Scarborough","Etobicoke",
        "East York","York","Mississauga","Brampton","Markham",
        "Vaughan","Richmond Hill","Oakville","Pickering","Ajax",
        "Kensington Market","Annex","Leslieville","Danforth","Bloor West",
    ],
    "vancouver": [
        "Downtown","West End","Gastown","Kitsilano","Commercial Drive",
        "Mount Pleasant","Fairview","West Vancouver","North Vancouver",
        "Burnaby","Richmond","Surrey","Langley","Coquitlam","Abbotsford",
    ],
    "montreal": [
        "Downtown","Plateau Mont-Royal","Mile End","Old Montreal","Rosemont",
        "Notre-Dame-de-Grâce","Verdun","LaSalle","Laval","Longueuil",
        "Westmount","Outremont","Villeray","Hochelaga","Saint-Laurent",
    ],
    "calgary": [
        "Downtown","Beltline","Kensington","Inglewood","Mission",
        "Bridgeland","Sunnyside","Forest Lawn","Shawnessy","Airdrie",
    ],
    "ottawa": [
        "Downtown","Centretown","Glebe","Westboro","Hintonburg",
        "Vanier","Kanata","Orleans","Barrhaven","Nepean",
    ],
    "edmonton": [
        "Downtown","Whyte Ave","Glenora","Bonnie Doon","Mill Woods",
        "West Edmonton","Sherwood Park","St Albert","Spruce Grove",
    ],

    # ── UAE ───────────────────────────────────────────────────────────────────
    "dubai": [
        "Deira","Bur Dubai","Karama","JBR","Downtown Dubai",
        "Business Bay","Dubai Marina","Al Barsha","Jumeirah",
        "Discovery Gardens","Sports City","Silicon Oasis","Mirdif",
        "Al Quoz","Satwa","Oud Metha","Muhaisnah","International City",
        "Jumeirah Lake Towers","Dubai Hills","Arabian Ranches","Motor City",
    ],
    "abu dhabi": [
        "Downtown","Al Reem Island","Khalidiyah","Corniche","Mussafah",
        "Al Ain","Yas Island","Saadiyat Island","Khalifa City","Mohamed Bin Zayed City",
    ],
    "sharjah": [
        "Al Nahda","Rolla","Al Qasimia","Muwailih","Al Khan",
        "Industrial Area","Al Majaz","Al Taawun",
    ],

    # ── SINGAPORE ─────────────────────────────────────────────────────────────
    "singapore": [
        "Orchard","Marina Bay","Clarke Quay","Bugis","Toa Payoh",
        "Tampines","Jurong","Woodlands","Ang Mo Kio","Bedok",
        "Punggol","Sengkang","Bishan","Serangoon","Yishun",
        "Hougang","Pasir Ris","Clementi","Queenstown","Buona Vista",
    ],

    # ── GERMANY ───────────────────────────────────────────────────────────────
    "berlin": [
        "Mitte","Prenzlauer Berg","Friedrichshain","Kreuzberg","Neukölln",
        "Charlottenburg","Schöneberg","Steglitz","Zehlendorf","Pankow",
        "Spandau","Wedding","Tempelhof","Reinickendorf","Treptow",
    ],
    "munich": [
        "Altstadt","Schwabing","Maxvorstadt","Haidhausen","Neuhausen",
        "Sendling","Giesing","Trudering","Bogenhausen","Pasing",
    ],
    "hamburg": [
        "Altona","Eimsbüttel","Harburg","Wandsbek","Bergedorf",
        "St Pauli","HafenCity","Blankenese","Rahlstedt","Lurup",
    ],
    "frankfurt": [
        "Sachsenhausen","Bornheim","Nordend","Westend","Bockenheim",
        "Gallus","Fechenheim","Höchst","Praunheim","Niederrad",
    ],

    # ── FRANCE ────────────────────────────────────────────────────────────────
    "paris": [
        "1st Arrondissement","2nd Arrondissement","3rd Arrondissement",
        "4th Arrondissement","5th Arrondissement","6th Arrondissement",
        "7th Arrondissement","8th Arrondissement","9th Arrondissement",
        "10th Arrondissement","11th Arrondissement","12th Arrondissement",
        "13th Arrondissement","14th Arrondissement","15th Arrondissement",
        "16th Arrondissement","17th Arrondissement","18th Arrondissement",
        "Montmartre","Marais","Saint-Germain","Bastille","Belleville",
        "Versailles","Saint-Denis","Vincennes","Boulogne-Billancourt",
    ],

    # ── NETHERLANDS ───────────────────────────────────────────────────────────
    "amsterdam": [
        "Centrum","Jordaan","De Pijp","Oud-Zuid","Oud-West",
        "Noord","Oost","Nieuw-West","Bijlmer","Bos en Lommer",
    ],

    # ── SPAIN ─────────────────────────────────────────────────────────────────
    "madrid": [
        "Centro","Salamanca","Malasaña","Chueca","Lavapiés",
        "Chamberí","Retiro","Arganzuela","Carabanchel","Vallecas",
        "Getafe","Alcalá de Henares","Leganés","Alcorcón","Móstoles",
    ],
    "barcelona": [
        "Gothic Quarter","Eixample","Gràcia","Barceloneta","Poble Sec",
        "Sant Martí","Sants","Nou Barris","Sant Andreu","Sarrià",
        "Hospitalet","Badalona","Terrassa","Sabadell","Mataró",
    ],

    # ── ITALY ─────────────────────────────────────────────────────────────────
    "rome": [
        "Trastevere","Prati","Pigneto","Testaccio","Monteverde",
        "Esquilino","Parioli","EUR","Ostia","Tiburtino",
    ],
    "milan": [
        "Brera","Navigli","Isola","Porta Romana","City Life",
        "Porta Venezia","Sempione","Lambrate","Sesto San Giovanni","Monza",
    ],

    # ── JAPAN ─────────────────────────────────────────────────────────────────
    "tokyo": [
        "Shibuya","Shinjuku","Harajuku","Akihabara","Asakusa",
        "Ginza","Roppongi","Shimokitazawa","Nakameguro","Ikebukuro",
        "Ueno","Koenji","Kichijoji","Yokohama","Kawasaki",
    ],
    "osaka": [
        "Namba","Shinsaibashi","Umeda","Tennoji","Shinsekai",
        "Dotonbori","Tsuruhashi","Sakaisuji","Kyobashi","Yodogawa",
    ],

    # ── SOUTH EAST ASIA ───────────────────────────────────────────────────────
    "bangkok": [
        "Sukhumvit","Silom","Siam","Chatuchak","Lat Phrao",
        "Nonthaburi","Min Buri","Bang Na","Phra Khanong","Thonburi",
    ],
    "kuala lumpur": [
        "KLCC","Bukit Bintang","Chow Kit","Bangsar","Petaling Jaya",
        "Subang Jaya","Puchong","Cheras","Ampang","Kepong",
        "Sri Petaling","Setapak","Wangsa Maju","Batu Caves",
    ],
    "jakarta": [
        "Sudirman","Kuningan","Kemang","Kebayoran Baru","Menteng",
        "Tanah Abang","Glodok","Kelapa Gading","Cikini","Semanggi",
    ],
    "ho chi minh city": [
        "District 1","District 3","Binh Thanh","District 7","Go Vap",
        "Tan Binh","Binh Duong","Thu Duc","Nha Be",
    ],

    # ── SOUTH AFRICA ──────────────────────────────────────────────────────────
    "johannesburg": [
        "Sandton","Rosebank","Melville","Soweto","Fourways",
        "Randburg","Midrand","Centurion","Boksburg","Springs",
    ],
    "cape town": [
        "CBD","Green Point","Sea Point","Camps Bay","Claremont",
        "Wynberg","Mitchells Plain","Bellville","Stellenbosch","Somerset West",
    ],

    # ── MIDDLE EAST ───────────────────────────────────────────────────────────
    "riyadh": [
        "Al Olaya","Al Malaz","Sulaimania","Al Hamra","Al Nakheel",
        "Al Aqiq","Al Wurud","Al Rawdah","Al Naseem","Al Hazm",
    ],
    "doha": [
        "West Bay","The Pearl","Al Sadd","Al Wakra","Al Rayyan",
        "Lusail","Muaither","Ain Khalid","Old Airport","Madinat Khalifa",
    ],
    "kuwait city": [
        "Salmiya","Hawalli","Farwaniya","Rumaithiya","Mangaf",
        "Fahaheel","Sabah Al-Salem","Mishref","Salwa","Jahra",
    ],

    # ── NEW ZEALAND ───────────────────────────────────────────────────────────
    "auckland": [
        "CBD","Ponsonby","Newmarket","Remuera","Mt Eden",
        "Parnell","Devonport","Takapuna","Manukau","Henderson",
    ],
}

# City aliases (handles slight name variations)
CITY_ALIASES = {
    "new york city": "new york",
    "nyc": "new york",
    "la": "los angeles",
    "dc": "washington dc",
    "washington": "washington dc",
    "bengaluru": "bangalore",
    "bombay": "mumbai",
    "calcutta": "kolkata",
    "madras": "chennai",
    "hcmc": "ho chi minh city",
}


def extract_coordinates_from_url(url: str) -> tuple[float, float]:
    try:
        coordinates = url.split('/@')[-1].split('/')[0]
        return float(coordinates.split(',')[0]), float(coordinates.split(',')[1])
    except Exception:
        return None, None


def detect_city(query: str) -> str | None:
    """Find the best matching city in the query string."""
    q = query.lower()
    # Check aliases first
    for alias, canonical in CITY_ALIASES.items():
        if alias in q:
            return canonical
    # Find longest matching city name
    best = None
    best_len = 0
    for city in CITY_AREAS:
        if city in q and len(city) > best_len:
            best = city
            best_len = len(city)
    return best


def build_search_queue(original_query: str, total: int) -> list[str]:
    """City-level search first, then area-by-area until target is reachable."""
    queue = [original_query]
    if total <= 20:
        return queue

    city = detect_city(original_query)
    if not city:
        return queue

    # Extract the business type — everything before " in "
    parts = re.split(r'\s+in\s+', original_query, flags=re.IGNORECASE)
    biz_type = parts[0].strip()
    city_display = city.title()

    for area in CITY_AREAS[city]:
        queue.append(f"{biz_type} in {area} {city_display}")

    return queue


# ── Global job state ──────────────────────────────────────────────────────────
JOB_STATES: dict = {}


def check_state(job_id: str) -> bool:
    """Returns True if job should stop."""
    state = JOB_STATES.get(job_id, {}).get('status', 'stopped')
    while state == 'paused':
        time.sleep(1)
        state = JOB_STATES.get(job_id, {}).get('status', 'stopped')
    return state == 'stopped'


def log(job_id: str, msg: str):
    if job_id not in JOB_STATES:
        return
    JOB_STATES[job_id]['progress'] = msg
    JOB_STATES[job_id].setdefault('log', []).append(msg)


def run_scraper(job_id: str, search_list: list[str], total: int,
                output_folder: str = "output", no_website_only: bool = False):
    if not search_list:
        return []

    JOB_STATES[job_id] = {
        'status': 'running',
        'progress': 'Initializing...',
        'data': [],
        'log': [],
    }

    try:
        with sync_playwright() as p:
            log(job_id, "Launching Chromium browser...")
            browser = p.chromium.launch(headless=False)
            page = browser.new_page()

            for search_index, original_query in enumerate(search_list):
                if check_state(job_id):
                    break

                safe_name = re.sub(r'[^a-zA-Z0-9_]', '_', original_query)
                file_path = os.path.join(output_folder, f"{safe_name}.json")

                existing_data: list[dict] = []
                seen_businesses: set[str] = set()
                if os.path.exists(file_path):
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            existing_data = json.load(f)
                        for b in existing_data:
                            seen_businesses.add(f"{b.get('name','')}|{b.get('address','')}")
                    except Exception:
                        pass

                total_extracted = len(existing_data)
                full_queue = build_search_queue(original_query, total)

                log(job_id,
                    f"[Query {search_index+1}/{len(search_list)}] '{original_query}' "
                    f"→ {len(full_queue)} area searches queued  (target: {total})")

                for q_idx, query in enumerate(full_queue):
                    if check_state(job_id):
                        break
                    if total_extracted >= total:
                        log(job_id, f"  Target {total} reached!")
                        break

                    log(job_id,
                        f"  [{q_idx+1}/{len(full_queue)}] Searching: '{query}' "
                        f"| Have {total_extracted}/{total}")

                    direct_url = ("https://www.google.com/maps/search/"
                                  + query.replace(" ", "+"))
                    page.goto(direct_url, wait_until="domcontentloaded", timeout=60000)
                    page.wait_for_timeout(4000)

                    for sel in [
                        'button[aria-label="Accept all"]',
                        'button:has-text("Accept all")',
                        'button:has-text("I agree")',
                        'button[jsname="higCR"]',
                    ]:
                        try:
                            btn = page.locator(sel).first
                            if btn.count():
                                btn.click()
                                page.wait_for_timeout(1000)
                                break
                        except Exception:
                            pass

                    if check_state(job_id):
                        break

                    needed = total - total_extracted
                    previously_counted = 0
                    stall = 0

                    while True:
                        if check_state(job_id):
                            break
                        try:
                            page.evaluate(
                                'document.querySelector(\'[role="feed"]\').scrollBy(0, 10000)'
                            )
                        except Exception:
                            page.mouse.wheel(0, 10000)
                        page.wait_for_timeout(2000)

                        current = page.locator(
                            '//a[contains(@href, "https://www.google.com/maps/place")]'
                        ).count()
                        log(job_id, f"    Visible: {current}  |  Need: {needed}")

                        if current >= needed:
                            break
                        if current == previously_counted:
                            stall += 1
                            if stall >= 3:
                                break
                            page.wait_for_timeout(2000)
                        else:
                            previously_counted = current
                            stall = 0

                    if check_state(job_id):
                        break

                    all_links = page.locator(
                        '//a[contains(@href, "https://www.google.com/maps/place")]'
                    ).all()
                    listings = [l.locator("xpath=..") for l in all_links[:needed]]

                    log(job_id, f"    Extracting details for {len(listings)} listings...")

                    new_businesses = BusinessList()

                    for i, listing in enumerate(listings):
                        if check_state(job_id):
                            break
                        if total_extracted >= total:
                            break

                        log(job_id,
                            f"    [{i+1}/{len(listings)}] Extracting... "
                            f"Total so far: {total_extracted}/{total}")

                        try:
                            listing.click()
                            page.wait_for_timeout(3500)

                            biz = Business()
                            biz.name = listing.get_attribute('aria-label') or ""

                            addr_xpath  = '//button[@data-item-id="address"]//div[contains(@class,"fontBodyMedium")]'
                            web_xpath   = '//a[@data-item-id="authority"]//div[contains(@class,"fontBodyMedium")]'
                            phone_xpath = '//button[contains(@data-item-id,"phone:tel:")]//div[contains(@class,"fontBodyMedium")]'
                            rc_xpath    = '//button[@jsaction="pane.reviewChart.moreReviews"]//span'
                            ra_xpath    = '//div[@jsaction="pane.reviewChart.moreReviews"]//div[@role="img"]'

                            biz.address = (
                                page.locator(addr_xpath).all()[0].inner_text()
                                if page.locator(addr_xpath).count() > 0 else ""
                            )

                            key = f"{biz.name}|{biz.address}"
                            if key in seen_businesses:
                                log(job_id, f"    Skipped duplicate: {biz.name}")
                                continue
                            seen_businesses.add(key)

                            biz.website = (
                                page.locator(web_xpath).all()[0].inner_text()
                                if page.locator(web_xpath).count() > 0 else ""
                            )
                            if no_website_only and biz.website:
                                log(job_id, f"    Skipped (has website): {biz.name}")
                                continue

                            biz.phone_number = (
                                page.locator(phone_xpath).all()[0].inner_text()
                                if page.locator(phone_xpath).count() > 0 else ""
                            )
                            if page.locator(rc_xpath).count() > 0:
                                biz.reviews_count = int(
                                    page.locator(rc_xpath).inner_text()
                                    .split()[0].replace(',', '').strip()
                                )
                            if page.locator(ra_xpath).count() > 0:
                                biz.reviews_average = float(
                                    page.locator(ra_xpath)
                                    .get_attribute('aria-label')
                                    .split()[0].replace(',', '.').strip()
                                )
                            biz.latitude, biz.longitude = extract_coordinates_from_url(page.url)

                            new_businesses.business_list.append(biz)
                            total_extracted += 1
                            JOB_STATES[job_id]['data'].append(asdict(biz))

                        except Exception as e:
                            log(job_id, f"    Error on listing: {e}")

                    combined = existing_data + [asdict(b) for b in new_businesses.business_list]
                    existing_data = combined
                    os.makedirs(output_folder, exist_ok=True)
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(combined, f, indent=4, ensure_ascii=False)

                    log(job_id,
                        f"  Saved. Progress for '{original_query}': "
                        f"{total_extracted}/{total}")

                log(job_id,
                    f"Finished '{original_query}': {total_extracted} leads collected.")

            browser.close()

    except Exception as e:
        log(job_id, f"Fatal error: {e}")
        JOB_STATES[job_id]['status'] = 'error'
        return

    if JOB_STATES[job_id]['status'] != 'error':
        log(job_id, "All queries completed.")
        JOB_STATES[job_id]['status'] = 'completed'
