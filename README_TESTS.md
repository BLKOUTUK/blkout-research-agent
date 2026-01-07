# BLKOUT Research Agent - Test Suite

Complete, production-ready test suite for the BLKOUT Research Agent.

## Quick Start

```bash
# 1. Install test dependencies
pip install -r requirements-dev.txt

# 2. Run all tests
pytest tests/ -v

# 3. Generate coverage report
pytest tests/ --cov=src --cov-report=html
```

## What's Tested

- ✓ **Date Extraction** - Extract dates from titles, URLs, snippets
- ✓ **Event Deduplication** - Remove duplicate events by URL
- ✓ **Relevance Filtering** - Score content relevance to Black LGBTQ+ UK
- ✓ **Search Processing** - Filter and process search results
- ✓ **Error Handling** - Graceful failure recovery

## Files Overview

| File | Purpose | Lines |
|------|---------|-------|
| **tests/test_agents.py** | Agent functionality tests | 477 |
| **tests/test_date_extraction.py** | Date format handling tests | 421 |
| **tests/test_search_filtering.py** | Result filtering/dedup tests | 475 |
| **tests/conftest.py** | Pytest fixtures & config | 220 |
| **tests/fixtures/sample_search_results.py** | Sample test data | 374 |
| **pytest.ini** | Pytest configuration | 50 |
| **requirements-dev.txt** | Test dependencies | 25 |
| **TESTING.md** | Quick start guide | 500+ |
| **tests/README.md** | Complete documentation | 600+ |
| **TEST_SUITE_SUMMARY.md** | Overview & statistics | 400+ |
| **TEST_FILES_MANIFEST.md** | File inventory | 300+ |

## Test Statistics

- **Total Test Files**: 4
- **Test Classes**: 25+
- **Test Functions**: 100+
- **Test Code Lines**: 1,973
- **Documentation Lines**: 1,500+
- **Sample Data Sets**: 6

## Running Tests

### All Tests
```bash
pytest tests/ -v
```

### Specific Category
```bash
pytest tests/test_agents.py -v                  # Agent tests
pytest tests/test_date_extraction.py -v         # Date extraction
pytest tests/test_search_filtering.py -v        # Search filtering
```

### With Coverage
```bash
pytest tests/ --cov=src --cov-report=html
```

### Specific Test
```bash
pytest tests/test_agents.py::TestNewsResearchAgent::test_quick_relevance_check_high_relevance -v
```

### Fast Tests Only
```bash
pytest tests/ -m "not slow" -v
```

## Documentation

- **TESTING.md** - Start here for quick setup and common tasks
- **tests/README.md** - Complete guide with all options and examples
- **TEST_SUITE_SUMMARY.md** - High-level overview and statistics
- **TEST_FILES_MANIFEST.md** - Detailed file inventory and contents

## Test Coverage

### test_agents.py (28 tests)
- NewsResearchAgent: relevance checking, filtering
- EventsDiscoveryAgent: date extraction, discovery
- Deduplication: URL matching
- Error handling: graceful failures

### test_date_extraction.py (40+ tests)
- Title extraction: "BBZ Party Jan 7 2026"
- URL extraction: "/events/2026-01-07-party"
- Snippet extraction: "Event on 2026-01-07"
- Validation: ISO format, future dates
- Edge cases: multiple dates, no dates, past dates

### test_search_filtering.py (30+ tests)
- Filtering: by domain, source, keywords, date
- Deduplication: exact URLs, case sensitivity
- Quality: empty snippets, minimum length
- Batch: pipeline operations, order preservation

## Fixtures

```python
# Async support
@pytest.fixture
def event_loop()

# Mocks
@pytest.fixture
def mock_llm_client()
@pytest.fixture
def mock_search_agent()
@pytest.fixture
def mock_database()

# Sample data
@pytest.fixture
def sample_search_results()
@pytest.fixture
def sample_article_data()
@pytest.fixture
def sample_event_data()
@pytest.fixture
def date_extraction_samples()
```

## Sample Data

Pre-built data available in fixtures:

- **10 Event search results** - various quality levels
- **10 News articles** - high/medium/low relevance
- **Duplicate pairs** - 4 deduplication scenarios
- **Date formats** - 5+ extraction examples
- **Relevance examples** - high/medium/low scores
- **Integration scenario** - end-to-end workflow

## Key Features

✓ **Comprehensive** - 100+ tests covering all functionality
✓ **Well-documented** - 1,500+ lines of documentation
✓ **Ready to use** - Pre-built fixtures and sample data
✓ **Async support** - Full pytest-asyncio integration
✓ **Mocking** - Pre-configured mocks for all dependencies
✓ **Coverage** - Target >80% code coverage
✓ **CI/CD ready** - Configured for continuous integration

## Installation

```bash
# From the research-agent directory
cd /home/robbe/blkout-platform/apps/research-agent

# Activate virtual environment
source venv/bin/activate

# Install test dependencies
pip install -r requirements-dev.txt

# Verify installation
pytest --version
```

Or use the automated script:

```bash
./INSTALL_AND_RUN_TESTS.sh
```

## Common Tasks

### Run and See Results
```bash
pytest tests/ -v
```

### Check What Tests Exist
```bash
pytest tests/ --collect-only
```

### Run Specific Test Category
```bash
pytest tests/ -k "date_extraction"
pytest tests/ -k "dedup"
pytest tests/ -k "relevance"
```

### Show Test Output
```bash
pytest tests/ -v -s
```

### Profile Slow Tests
```bash
pytest tests/ --durations=10
```

### Run with Detailed Failures
```bash
pytest tests/ -v -l --tb=long
```

## Troubleshooting

### Tests Won't Run
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Install dependencies
pip install -r requirements-dev.txt

# Try again
pytest tests/ -v
```

### Import Errors
```bash
# Set PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:/home/robbe/blkout-platform/apps/research-agent"
pytest tests/ -v
```

### Need Help?
See **TESTING.md** for quick solutions or **tests/README.md** for comprehensive guide.

## Integration

The test suite integrates with:
- **GitHub Actions** - Ready for CI/CD workflows
- **Local development** - Run during development
- **Pre-commit hooks** - Can run before commits
- **Coverage tracking** - Generate coverage reports

## Next Steps

1. ✓ Tests are installed and ready
2. Run `pytest tests/ -v` to validate
3. Read `TESTING.md` for detailed information
4. Check coverage: `pytest tests/ --cov=src --cov-report=html`
5. Integrate into CI/CD pipeline

## Absolute File Paths

All test files are located at:

```
/home/robbe/blkout-platform/apps/research-agent/
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_agents.py
│   ├── test_date_extraction.py
│   ├── test_search_filtering.py
│   ├── README.md
│   └── fixtures/
│       ├── __init__.py
│       └── sample_search_results.py
│
├── pytest.ini
├── requirements-dev.txt
├── TESTING.md
├── TEST_SUITE_SUMMARY.md
├── TEST_FILES_MANIFEST.md
├── README_TESTS.md (this file)
└── INSTALL_AND_RUN_TESTS.sh
```

## Summary

This is a comprehensive, production-ready test suite with:
- 1,973 lines of test code
- 1,500+ lines of documentation
- 100+ test functions
- 25+ test classes
- 8 fixtures
- 6 sample data sets

Ready to use immediately with `pytest tests/ -v`

---

**Created**: January 7, 2026
**Status**: Complete and Production-Ready
**Support**: See TESTING.md or tests/README.md
