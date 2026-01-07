# Code Changes Summary - Search Query Filtering Improvements

**Quick Reference Guide**
**Date**: January 7, 2026

---

## Problem Statement

Search results were including:
- Wikipedia articles about musicians named "Black"
- Video game wikis (Misery, etc.)
- Non-UK content
- Entertainment content not relevant to BLKOUT community

**Root cause**: No domain filtering, too-lenient keyword scoring, weak thresholds.

---

## Solution: Three-Layer Filtering

### Layer 1: Domain Validation
**File**: `configs/blkout_config.py` (lines 206-257)

```python
# REJECT these domains immediately
domain_blacklist = [
    "wikipedia.org", "reddit.com", "imdb.com",
    "fandom.com", "twitch.tv", "steam.powered.com",
]

# PREFER these domains (high quality)
domain_whitelist = [
    # News organizations
    "bbc.co.uk", "theguardian.com", "pinknews.co.uk",

    # Event platforms
    "outsavvy.com", "eventbrite.co.uk",

    # Community organizations
    "stonewall.org.uk", "londonlgbtqcentre.org",
]
```

### Layer 2: Negative Keywords
**File**: `configs/blkout_config.py` (lines 184-204)

```python
negative_keywords = [
    # Entertainment (musician, band, actor, movie)
    "musician", "band", "rapper", "singer", "artist",

    # Gaming (game, video game, character)
    "game", "video game", "esports",

    # Non-UK (usa, america, california)
    "usa", "america", "us pride",

    # Generic sources (wikipedia, wiki, reddit)
    "wikipedia", "wiki", "encyclopedia",
]
```

**Logic**: If content contains "musician" (or similar), it gets scored very low (15/100) unless it also has high-relevance keywords like "black queer".

### Layer 3: Stricter Thresholds
**File**: `configs/blkout_config.py` (lines 259-264)

```python
# News articles must score >= 75 (was 70)
relevance_threshold = 75

# Events must score >= 80 (even stricter)
event_relevance_threshold = 80

# Quick filter pass threshold raised to 45 (was 40)
```

---

## Code Changes by File

### File 1: `configs/blkout_config.py`

#### Change A: Search Query Improvements

**Before:**
```python
events_search_queries = [
    "site:outsavvy.com Black LGBTQ",
    "Misery QTIPOC",        # ← Returns game wiki
    "Hungama queer",        # ← Returns music band
]
```

**After:**
```python
events_search_queries = [
    "site:outsavvy.com Black LGBTQ",
    "site:eventbrite.co.uk Black queer",
    "Black LGBTQ events London -wiki -game",  # ← Negative operators
    "Hungama London music event LGBTQ",       # ← Added "event" context
    "BBZ London queer party events",          # ← Clear event keywords
]
```

#### Change B: Added Domain Filtering Lists

```python
# NEW: Domain blacklist (lines 206-218)
domain_blacklist = [
    "wikipedia.org", "en.wikipedia.org",
    "reddit.com", "www.reddit.com",
    "imdb.com", "www.imdb.com",
    "fandom.com", "wiki.fandom.com",
    "twitch.tv", "steam.powered.com",
]

# NEW: Domain whitelist (lines 220-257)
domain_whitelist = [
    "bbc.co.uk", "theguardian.com",
    "pinknews.co.uk", "attitude.co.uk",
    "outsavvy.com", "eventbrite.co.uk",
    "londonlgbtqcentre.org", "stonewall.org.uk",
    # ... plus social platforms
]
```

#### Change C: Added Negative Keywords

```python
# NEW: Negative keywords list (lines 184-204)
negative_keywords = [
    "musician", "band", "rapper", "singer", "artist", "actor",
    "game", "video game", "gaming", "esports",
    "usa", "america", "california", "new york",
    "wikipedia", "wiki", "reddit", "tutorial", "guide",
]
```

#### Change D: Raised Thresholds

```python
# BEFORE: relevance_threshold = 70
# AFTER:
relevance_threshold = 75

# NEW:
event_relevance_threshold = 80
```

---

### File 2: `src/agents.py`

#### Change A: Updated Imports (lines 18-30)

```python
from configs.blkout_config import (
    news_search_queries,
    events_search_queries,
    high_relevance_keywords,
    black_keywords,
    lgbtq_keywords,
    uk_keywords,
    # NEW:
    negative_keywords,
    domain_blacklist,
    domain_whitelist,
    event_relevance_threshold,
)
```

#### Change B: New Helper Methods in NewsResearchAgent (lines 69-97)

```python
def _is_domain_acceptable(self, url: str) -> bool:
    """Check if domain is acceptable for news/events content"""
    url_lower = url.lower()
    domain = self._extract_domain(url_lower)

    # REJECT blacklisted domains
    for blacklisted in domain_blacklist:
        if blacklisted in domain:
            return False

    # PREFER whitelisted sources
    for whitelisted in domain_whitelist:
        whitelisted_clean = whitelisted.replace("*.", "")
        if whitelisted_clean in domain or domain.endswith(whitelisted_clean):
            return True

    # Accept others if they pass keyword checks
    return True

def _extract_domain(self, url: str) -> str:
    """Extract domain from URL"""
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        domain = parsed.netloc.replace("www.", "").lower()
        return domain
    except:
        return ""
```

#### Change C: Improved _quick_relevance_check Method (lines 99-149)

**Key improvements:**

```python
def _quick_relevance_check(self, text: str, url: str = "") -> int:
    """Fast keyword-based relevance check before LLM analysis

    Returns:
        -1: Rejected (domain blacklist, negative keywords)
        0-45: Too low relevance
        46-74: Borderline (needs LLM review)
        75+: High confidence match
    """
    text_lower = text.lower()

    # STEP 1: Domain-based rejection (FIRST CHECK)
    if url and not self._is_domain_acceptable(url):
        return -1  # Signal immediate rejection

    # STEP 2: Negative keywords (penalize entertainment/gaming)
    for neg_term in negative_keywords:
        if neg_term in text_lower:
            # Unless overridden by high-relevance keywords
            has_high_relevance = any(
                term in text_lower for term in high_relevance_keywords
            )
            if not has_high_relevance:
                return 15  # Very low, likely false positive

    # STEP 3: High-relevance terms (strongest signal)
    for term in high_relevance_keywords:
        if term in text_lower:
            return 95

    # STEP 4: Black + LGBTQ+ + UK (strict requirement)
    has_black = any(kw in text_lower for kw in black_keywords)
    has_lgbtq = any(kw in text_lower for kw in lgbtq_keywords)
    has_uk = any(kw in text_lower for kw in uk_keywords)

    if has_black and has_lgbtq and has_uk:
        return 85  # Strong match

    # STEP 5: Weaker combinations get much lower scores
    if has_black and has_lgbtq:
        return 60  # DOWN from 75 (now borderline, needs LLM)
    elif (has_black or has_lgbtq) and has_uk:
        return 50  # DOWN from 40
    elif has_black or has_lgbtq:
        return 25  # DOWN from 40 (single keyword alone)

    return 10  # No relevant keywords
```

**Comparison table:**

| Scenario | Before | After | Why Changed |
|----------|--------|-------|-------------|
| High-relevance term ("black queer") | 95 | 95 | Same (correct) |
| Black + LGBTQ+ + UK | 85 | 85 | Same (correct) |
| Black + LGBTQ+, no UK | 75 | 60 | Now borderline (needs LLM) |
| Single keyword only | 40 | 25 | Too lenient before |
| Domain rejected | N/A | -1 | NEW |

#### Change D: Updated research() Method (lines 151-180)

```python
async def research(self, time_range: str = "w") -> List[DiscoveredArticle]:
    # ... search code ...

    # Phase 2: Quick filter with domain and keyword validation
    candidates = []
    rejected = []
    for result in all_results:
        combined_text = f"{result.title} {result.snippet}"
        # NOW PASSES URL TO CHECK DOMAIN
        quick_score = self._quick_relevance_check(combined_text, url=result.url)

        if quick_score == -1:
            # Domain rejection (Wikipedia, gaming, etc)
            rejected.append((result, "domain_blacklist"))
        elif quick_score >= 45:  # UP from 40 (stricter)
            candidates.append((result, quick_score))
        else:
            rejected.append((result, f"low_score_{quick_score}"))

    print(f"[NewsAgent] {len(candidates)} candidates passed quick filter")
    print(f"[NewsAgent] {len(rejected)} results rejected (domain/keywords)")
    # ... LLM analysis ...
```

#### Change E: New Methods in EventsDiscoveryAgent (lines 275-334)

```python
def _is_domain_acceptable(self, url: str) -> bool:
    """Check if domain is acceptable for events content"""
    url_lower = url.lower()
    domain = self._extract_domain(url_lower)

    # REJECT blacklisted domains
    for blacklisted in domain_blacklist:
        if blacklisted in domain:
            return False

    # WHITELIST event platforms (strongly preferred)
    event_whitelist = ["outsavvy", "eventbrite", "moonlight", "londonlgbtq",
                      "designmynight", "eventim", "ticketmaster"]
    for whitelisted in event_whitelist:
        if whitelisted in domain:
            return True

    # Accept social platforms (for announcements)
    social = ["instagram", "facebook", "twitter", "x.com"]
    for soc in social:
        if soc in domain:
            return True

    return True  # Other sources OK if they pass keyword checks

def _is_likely_event(self, text: str) -> bool:
    """Check if content appears to be an actual event"""
    text_lower = text.lower()

    # Negative indicators (NOT an event)
    non_event_terms = [
        "musician", "band", "game", "character",
        "tv show", "movie", "film", "wikipedia",
    ]
    for term in non_event_terms:
        if term in text_lower:
            # Unless it has clear event indicators
            event_terms = ["event", "party", "night", "club", "show",
                          "performance", "live", "happening", "gig"]
            if not any(et in text_lower for et in event_terms):
                return False

    # Positive indicators (IS an event)
    event_terms = [
        "event", "party", "night", "club", "gathering",
        "show", "performance", "live", "gig", "festival",
    ]
    return any(term in text_lower for term in event_terms)
```

#### Change F: Updated discover_from_search() (lines 336-395)

```python
async def discover_from_search(self) -> List[DiscoveredEvent]:
    """Discover events via web search"""
    print("[EventsAgent] Searching for QTIPOC events...")

    results = await self.search.search_qtipoc_events()
    events = []
    rejected = []

    for result in results:
        combined_text = f"{result.title} {result.snippet}"

        # Filter 1: Domain validation
        if not self._is_domain_acceptable(result.url):
            rejected.append((result, "domain_blacklist"))
            continue

        # Filter 2: Check if it's actually an event
        if not self._is_likely_event(combined_text):
            rejected.append((result, "not_event"))
            continue

        # Filter 3: Must contain BOTH Black AND LGBTQ+ keywords
        text_lower = combined_text.lower()
        has_black = any(kw in text_lower for kw in black_keywords)
        has_lgbtq = any(kw in text_lower for kw in lgbtq_keywords)
        has_uk = any(kw in text_lower for kw in uk_keywords)

        if not (has_black and has_lgbtq):  # BOTH required
            rejected.append((result, "weak_keywords"))
            continue

        # Extract date and build event
        extracted_date = await self._extract_date_from_text(...)
        relevance = 95 if any(kw in text_lower for kw in high_relevance_keywords) \
                    else 85 if has_uk else 75

        events.append(DiscoveredEvent(...))

    print(f"[EventsAgent] {len(events)} events passed filters")
    print(f"[EventsAgent] {len(rejected)} results rejected")
    return events
```

---

## Impact by Use Case

### Case 1: Search "Black queer UK"

**Before:**
- Result: Q-Tip Wikipedia article
- Score: 75 (has "Black", somehow LGBTQ matched)
- Outcome: INCLUDED (wrong)

**After:**
- Result: Q-Tip Wikipedia article
- Domain check: wikipedia.org → blacklist
- Score: -1
- Outcome: REJECTED immediately (correct)

### Case 2: Search "Misery QTIPOC"

**Before:**
- Result: Misery game wiki
- Score: 80+ (has "queer")
- Outcome: INCLUDED (wrong)

**After:**
- Result: Misery game wiki
- Domain check: fandom.com → blacklist
- Score: -1
- Outcome: REJECTED (correct)

### Case 3: Search "Black Pride UK"

**Before:**
- Result: BBC article about "Broadcasting House - pride of British architecture"
- Score: 60+ ("Pride" matched, wrong context)
- Outcome: Passed to LLM (wasted API call)

**After:**
- Result: Same BBC article
- Domain check: bbc.co.uk → whitelist (good source)
- Negative keywords: None found
- Keyword combo: No "black" + no "lgbtq" keywords
- Score: 10
- Outcome: REJECTED before LLM (correct, faster)

### Case 4: Search "BBZ London" (real venue)

**Before:**
- Result: https://outsavvy.com/event/bbz-london-pride
- Title: "BBZ London Pride Party - QTIPOC Celebration"
- Score: 75
- Outcome: INCLUDED, needs LLM confirmation

**After:**
- Result: https://outsavvy.com/event/bbz-london-pride
- Domain check: outsavvy.com → whitelist (trusted event platform)
- Event check: "party", "pride" → YES, is event
- Keywords: "QTIPOC" → high-relevance term
- Score: 95
- Outcome: ACCEPTED immediately (correct, no LLM needed)

---

## Testing the Changes

### Quick Test
```bash
cd /home/robbe/blkout-platform/apps/research-agent
python main.py --test
```

### Expected Output for News

```
[NewsAgent] Starting research with 14 queries...
[NewsAgent] Found 60 raw results
[NewsAgent] 12 candidates passed quick filter
[NewsAgent] 48 results rejected (domain/keywords)
[NewsAgent] Found 8 relevant articles
```

All 8 articles should be:
- From UK news sources or LGBTQ+ media
- About Black LGBTQ+ community (not just "Black" or just "LGBTQ+")
- Actually news (not entertainment/gaming)

### Expected Output for Events

```
[EventsAgent] Searching for QTIPOC events...
[EventsAgent] Found 25 search results
[EventsAgent] 6 events passed filters
[EventsAgent] 19 results rejected
```

All 6 events should be:
- Real events (not bands/musicians/games)
- UK-focused
- Black LGBTQ+ community events

---

## Deployment Checklist

- [ ] Review `configs/blkout_config.py` changes
- [ ] Review `src/agents.py` changes
- [ ] Run `python main.py --test`
- [ ] Verify no Wikipedia/gaming results
- [ ] Verify rejection logging shows domains and reasons
- [ ] Commit: `git commit -m "Improve search filtering: domain validation, negative keywords, stricter thresholds"`
- [ ] Push to main branch
- [ ] Monitor production results for 24 hours

---

## Files Modified

| File | Lines | Changes |
|------|-------|---------|
| `configs/blkout_config.py` | 77-98 | Improved event search queries |
| | 184-204 | Added negative_keywords |
| | 206-218 | Added domain_blacklist |
| | 220-257 | Added domain_whitelist |
| | 259-264 | Raised thresholds |
| `src/agents.py` | 18-30 | Updated imports |
| | 69-97 | Added domain helper methods |
| | 99-149 | Improved _quick_relevance_check |
| | 151-180 | Updated research() with logging |
| | 275-334 | Added event filtering methods |
| | 336-395 | Updated discover_from_search() |

**Total lines added**: ~250
**Total lines modified**: ~40
**Breaking changes**: None (backward compatible)

---

## Next Steps

1. Test thoroughly with `python main.py --test`
2. Monitor production logs for rejection patterns
3. Collect user feedback on result quality
4. Consider adding geographic pre-filtering (postcode validation)
5. Consider geographic pre-filtering (postcode validation)
6. Plan A/B test with and without stricter filtering

---

**Status**: Ready for review and deployment
**Date**: January 7, 2026
**Estimated time to review**: 10 minutes
**Estimated time to test**: 5 minutes
