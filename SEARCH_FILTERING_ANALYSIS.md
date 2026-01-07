# Search Query Relevance Filtering Analysis - Research Agent

**Date**: January 7, 2026
**Status**: Critical Issues Identified
**Priority**: High - Directly impacts community content discovery

---

## Executive Summary

The Research Agent's search filtering is allowing irrelevant results (Q-Tip musician Wikipedia, Misery game, BBC Broadcasting House) to pass through because of three critical gaps:

1. **No pre-filtering for obvious non-content sources** (Wikipedia articles, gaming wikis)
2. **Weak URL/domain validation** (accepts any Wikipedia/generic result)
3. **Lenient relevance thresholds** (70 is too low for intersectional content)
4. **Inadequate negative keyword filtering** (no exclusion lists)

---

## Root Cause Analysis

### Problem 1: Wikipedia & Generic Reference Pages

**Current behavior**: Query "Black queer UK" returns Wikipedia article "Q-Tip (musician)" because:
- DuckDuckGo returns ANY result matching keywords
- No source domain filtering
- "Black" in artist name matches `black_keywords`
- No exclusion of non-event/non-news sources

**Why it happens**:
```python
# src/agents.py line 75-80 (NEWS AGENT)
has_black = any(kw in text_lower for kw in black_keywords)  # "black" matches ANYWHERE
has_lgbtq = any(kw in text_lower for kw in lgbtq_keywords)

if has_black and has_lgbtq:
    return 85 if has_uk else 75  # PASSES with score 75!
```

The logic doesn't distinguish between "Black queer activist" (relevant) and "Black musician, LGBTQ band" (irrelevant).

### Problem 2: Non-UK Content

**Current behavior**: Returns results about:
- US Pride events (relevant keywords but wrong geography)
- Global LGBTQ+ content
- No mandatory UK location validation

**Why it happens**:
```python
# Line 77: UK validation is OPTIONAL not mandatory
has_uk = any(kw in text_lower for kw in uk_keywords)

if has_black and has_lgbtq:
    return 85 if has_uk else 75  # Still scores 75 without UK!
```

### Problem 3: Gaming & Entertainment False Positives

**Current behavior**: Returns unrelated results:
- "Misery" (video game with LGBTQ+ character)
- Entertainment wikis
- No domain validation

**Why it happens**: Keyword matching without context checking.

### Problem 4: LLM Fallback is Also Weak

**Current behavior** (src/agents.py line 124-142):
- LLM scoring can still output low scores
- Fallback still uses `relevance_threshold = 70`
- No filtering of Wikipedia/generic sources before LLM

---

## Code Changes Needed

### 1. Enhanced Pre-Filtering (src/agents.py)

**Add domain blacklist and positive source whitelist**:
- Reject Wikipedia, Wikia, generic wikis, Reddit (mostly off-topic)
- Require at least one of: news site, event platform, community org, verified source
- Add strict URL pattern validation

### 2. Improved Keyword Scoring (configs/blkout_config.py)

**Add explicit filtering rules**:
- Negative keywords (exclude unrelated content)
- Geographic requirements (UK mandatory for news/events)
- Content type requirements (must be news, event, or community content)

### 3. Stricter Relevance Thresholds

- News: 75+ (up from 70)
- Events: 80+ (more selective)
- Require both Black AND LGBTQ+ keywords (not just one or the other)

### 4. Better Search Queries

- Add negative search operators: `-wikipedia -wiki -game -musician`
- Require event/news keywords in queries
- Add UK/location requirement

---

## Specific Issues in Code

### File: `/home/robbe/blkout-platform/apps/research-agent/configs/blkout_config.py`

**Lines 77-94 (events_search_queries):**
```python
"Misery QTIPOC",  # ← This is a VIDEO GAME, not an event
"Hungama queer",  # ← Searches for the band, not events
```

**Problem**: Generic search terms return entertainment results, not community events.

**Lines 156-178 (keyword lists):**
```python
black_keywords = [
    "black", "african", "caribbean", ...  # ← "black" alone matches "Black Mirror" TV show
]
```

**Problem**: Single keywords are too broad.

**Line 181 (relevance_threshold = 70):**
```python
relevance_threshold = 70  # ← Too lenient for intersectional content
```

**Problem**: Scores 70+ can still be irrelevant (musician named Black with LGBTQ+ band members).

---

### File: `/home/robbe/blkout-platform/apps/research-agent/src/agents.py`

**Lines 65-83 (NewsResearchAgent._quick_relevance_check):**
```python
has_black = any(kw in text_lower for kw in black_keywords)
has_lgbtq = any(kw in text_lower for kw in lgbtq_keywords)
has_uk = any(kw in text_lower for kw in uk_keywords)

if has_black and has_lgbtq:
    return 85 if has_uk else 75  # ← Returns 75 even without UK content!
elif has_black or has_lgbtq:
    return 40  # ← Single keyword gets 40 (still passes filter)
```

**Problems**:
1. No domain/source validation
2. UK is optional (should be mandatory)
3. Single keywords pass too high
4. No context about what "black" and "lgbtq" refer to

**Lines 98-103 (Quick filter pass criteria):**
```python
for result in all_results:
    combined_text = f"{result.title} {result.snippet}"
    quick_score = self._quick_relevance_check(combined_text)
    if quick_score >= 40:  # ← VERY lenient, 40 out of 100
        candidates.append((result, quick_score))
```

**Problem**: Score of 40 is barely-relevant but still includes content.

---

### File: `/home/robbe/blkout-platform/apps/research-agent/src/search.py`

**Lines 28-59 (SearchAgent.search):**
```python
# No pre-filtering of results
# No validation of source domains
# No rejection of Wikipedia, generic wikis, etc.
```

**Problem**: DuckDuckGo returns raw results with no filtering.

---

## Examples of Current Failures

### Example 1: Q-Tip Musician Wikipedia
- Search query: "Black queer UK"
- Result: Wikipedia article about Q-Tip (musician)
- Snippet: "...African-American hip-hop artist..."
- Quick score: 75 (has "black" and somehow LGBTQ+ keyword matched)
- Why it passed:
  - "Black" in title (is musician)
  - Wikipedia not filtered out
  - No source domain validation

### Example 2: Misery Video Game
- Search query: "Misery QTIPOC"
- Result: Video game wiki about Misery (indie game)
- Snippet: "...features queer character..."
- Quick score: 80+ (has both "queer" and relevant keyword)
- Why it passed:
  - Keyword match with "queer"
  - Non-event content not rejected
  - Gaming wiki not excluded

### Example 3: BBC Broadcasting House
- Search query: "Black Pride UK"
- Result: BBC article about Broadcasting House building
- Snippet: "...historic building, pride of British architecture..."
- Quick score: 60+ ("Pride" matched)
- Why it passed:
  - "Pride" matched (word overloading)
  - News source (BBC) seems legitimate
  - No context validation

---

## Recommended Solutions

### High Priority (Implement First)

1. **Add URL domain blacklist/whitelist**
   - Reject: wikipedia.org, wiki.*, reddit.com, imdb.com, metacritic.com
   - Prefer: news sites, org.uk domains, event platforms

2. **Stricter keyword combination rules**
   - Must have high-relevance term OR (Black AND LGBTQ+ AND UK)
   - Single keywords insufficient

3. **Add negative keywords to queries**
   - `-wikipedia -wiki -game -musician -band -actor -movie`

4. **Raise relevance threshold**
   - News: 75+ (from 70)
   - Events: 80+ (from 75)

### Medium Priority

5. **Add content type validation**
   - Verify content is news, event, or community-focused
   - Reject entertainment/celebrity content

6. **Improve search query specificity**
   - Replace generic terms with event/news keywords
   - "Black LGBTQ community event UK" instead of just keywords

### Lower Priority

7. **Add geographic filtering**
   - Require UK location in news results
   - Optional for broader research

---

## Files to Modify

1. `/home/robbe/blkout-platform/apps/research-agent/configs/blkout_config.py`
   - Add negative keywords
   - Add domain whitelist/blacklist
   - Raise thresholds
   - Improve search queries

2. `/home/robbe/blkout-platform/apps/research-agent/src/agents.py`
   - Add domain validation in _quick_relevance_check
   - Stricter keyword combination logic
   - Raise filter thresholds
   - Add negative keyword filtering

3. `/home/robbe/blkout-platform/apps/research-agent/src/search.py`
   - Add source filtering options
   - Pre-filter results before returning

---

## Testing Strategy

After implementation, run:
```bash
python main.py --test
```

Verify:
- No Wikipedia articles in results
- No video game wikis
- No off-topic music/entertainment content
- At least 8-9/10 results are genuinely relevant
- All events are UK-focused
- All news has community relevance
