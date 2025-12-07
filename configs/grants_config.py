"""
Grant Funding Research Configuration for BLKOUT

Targets funders aligned with:
- Black LGBTQ+ community support
- Participatory arts
- Gender justice
- Community wealth / cooperative economy
- Independent media / journalism
- UK racial equity
"""

# Search queries for discovering grant opportunities
grant_search_queries = [
    # LGBTQ+ Specific
    "LGBTQ+ grants UK 2024 2025",
    "queer community funding UK",
    "LGBT foundation grants open",
    "Pride funding opportunities UK",

    # Black/POC + LGBTQ+ Intersectional
    "Black LGBTQ grants UK",
    "QTIPOC funding opportunities",
    "racial equity LGBTQ funding",
    "intersectional grants UK",

    # Participatory Arts
    "participatory arts funding UK",
    "community arts grants UK 2025",
    "Arts Council England open funds",
    "creative communities grants",
    "co-created arts funding",

    # Gender Justice
    "gender justice grants UK",
    "trans community funding UK",
    "gender equity funding opportunities",
    "feminist funding UK",

    # Community Wealth / Cooperative
    "community wealth building grants UK",
    "cooperative economy funding",
    "worker cooperative grants UK",
    "community ownership funding",
    "social enterprise grants UK",
    "Power to Change grants",

    # Media / Journalism
    "independent media funding UK",
    "community journalism grants",
    "alternative media funding",
    "digital media grants UK",
    "storytelling grants community",

    # Racial Justice
    "racial justice funding UK",
    "Black community grants UK",
    "anti-racism funding opportunities",
    "Runnymede grants",
    "Baring Foundation grants",

    # Major UK Funders
    "National Lottery Community Fund open",
    "Tudor Trust grants open",
    "Esmee Fairbairn grants open",
    "Paul Hamlyn Foundation grants",
    "Comic Relief grants open",
    "Joseph Rowntree Foundation funding",
    "Lankelly Chase grants",
    "Lloyds Bank Foundation grants",
    "City Bridge Trust grants",
    "Trust for London grants",

    # Health & Wellbeing
    "mental health community grants UK",
    "wellbeing funding LGBTQ",
    "health equity grants UK",
]

# Known funder websites to monitor
funder_websites = [
    # LGBTQ+ Funders
    {"name": "Elton John AIDS Foundation", "url": "https://www.eltonjohnaidsfoundation.org/what-we-do/grant-making/"},
    {"name": "LGBT Foundation", "url": "https://lgbt.foundation/"},
    {"name": "Stonewall", "url": "https://www.stonewall.org.uk/"},

    # Major UK Trusts
    {"name": "National Lottery Community Fund", "url": "https://www.tnlcommunityfund.org.uk/funding"},
    {"name": "Arts Council England", "url": "https://www.artscouncil.org.uk/ProjectGrants"},
    {"name": "Tudor Trust", "url": "https://tudortrust.org.uk/"},
    {"name": "Esmée Fairbairn Foundation", "url": "https://esmeefairbairn.org.uk/"},
    {"name": "Paul Hamlyn Foundation", "url": "https://www.phf.org.uk/"},
    {"name": "Joseph Rowntree Foundation", "url": "https://www.jrf.org.uk/"},
    {"name": "Lankelly Chase", "url": "https://lankellychase.org.uk/"},
    {"name": "Baring Foundation", "url": "https://baringfoundation.org.uk/"},

    # Community Wealth
    {"name": "Power to Change", "url": "https://www.powertochange.org.uk/"},
    {"name": "Cooperative Development Foundation", "url": "https://cdf.coop/"},
    {"name": "Plunkett Foundation", "url": "https://plunkett.co.uk/"},

    # London Specific
    {"name": "City Bridge Trust", "url": "https://www.citybridgetrust.org.uk/"},
    {"name": "Trust for London", "url": "https://trustforlondon.org.uk/"},
    {"name": "London Community Foundation", "url": "https://londoncf.org.uk/"},

    # Racial Justice
    {"name": "Runnymede Trust", "url": "https://www.runnymedetrust.org/"},
    {"name": "Comic Relief", "url": "https://www.comicrelief.com/funding/"},

    # Media
    {"name": "Media Trust", "url": "https://mediatrust.org/"},
    {"name": "JRF Journalism", "url": "https://www.jrf.org.uk/"},
]

# Funder type categories
funder_types = [
    "trust_foundation",
    "lottery",
    "arts_council",
    "lgbtq_specific",
    "racial_justice",
    "gender_justice",
    "community_wealth",
    "media_journalism",
    "corporate",
    "government",
]

# Program areas BLKOUT is eligible for
program_areas = [
    "community_development",
    "arts_culture",
    "health_wellbeing",
    "racial_justice",
    "lgbtq_rights",
    "gender_justice",
    "media_communications",
    "cooperative_economy",
    "youth",
    "mental_health",
    "capacity_building",
    "core_costs",
]

# Keywords indicating high relevance for BLKOUT
high_relevance_keywords = [
    "black lgbtq",
    "black queer",
    "qtipoc",
    "intersectional",
    "queer people of colour",
    "black gay",
    "black trans",
    "community-led",
    "lived experience",
    "cooperative",
    "community ownership",
    "participatory",
    "co-creation",
]

# Keywords for filtering
lgbtq_keywords = [
    "lgbtq", "lgbt", "queer", "gay", "trans", "transgender",
    "pride", "sexual orientation", "gender identity", "nonbinary",
]

black_keywords = [
    "black", "african", "caribbean", "afro", "diaspora",
    "ethnic minority", "bame", "people of colour", "poc",
    "global majority", "racialised",
]

arts_keywords = [
    "arts", "culture", "creative", "participatory", "co-creation",
    "storytelling", "media", "film", "music", "performance",
]

community_wealth_keywords = [
    "cooperative", "co-op", "community ownership", "social enterprise",
    "community wealth", "democratic", "mutual", "worker-owned",
]

# Relevance scoring threshold
relevance_threshold = 60
