# Testing Guide for BLKOUT Research Agent

## Quick Start

### 1. Install Test Dependencies

```bash
cd /home/robbe/blkout-platform/apps/research-agent

# Activate virtual environment
source venv/bin/activate

# Install test dependencies
pip install -r requirements-dev.txt
```

### 2. Run All Tests

```bash
# From the project root directory
cd /home/robbe/blkout-platform/apps/research-agent

# Run all tests with verbose output
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=src --cov-report=html

# Run specific test file
pytest tests/test_agents.py -v

# Run specific test class
pytest tests/test_agents.py::TestNewsResearchAgent -v

# Run specific test function
pytest tests/test_agents.py::TestNewsResearchAgent::test_quick_relevance_check_high_relevance -v
```

## Test Organization

The test suite is organized into three main components:

### 1. **test_agents.py** - Agent Functionality Tests
Tests the core behavior of NewsResearchAgent and EventsDiscoveryAgent:

- **Relevance Scoring**: Tests keyword-based and LLM-based relevance detection
- **Date Extraction**: Tests extracting dates from search results
- **Event Discovery**: Tests finding and deduplicating events
- **Error Handling**: Tests graceful failure modes
- **Data Structure**: Tests that results have correct fields

**Run with:**
```bash
pytest tests/test_agents.py -v
```

**Key test classes:**
- `TestNewsResearchAgent` - 10+ tests
- `TestEventsDiscoveryAgent` - 10+ tests
- `TestDeduplication` - 3+ tests
- `TestErrorHandling` - 2+ tests

### 2. **test_date_extraction.py** - Date Format Recognition
Comprehensive tests for extracting and validating dates:

- **Title Extraction**: "BBZ Party Jan 7 2026"
- **URL Extraction**: "/events/2026-01-07-party"
- **Snippet Extraction**: "Event on 2026-01-07"
- **Date Validation**: ISO format, future dates, invalid dates
- **Edge Cases**: Multiple dates, past dates, no dates

**Run with:**
```bash
pytest tests/test_date_extraction.py -v
```

**Key test classes:**
- `TestDateExtractionFromTitle` - Various title formats
- `TestDateExtractionFromURL` - URL patterns
- `TestDateExtractionFromSnippet` - Description parsing
- `TestDateValidation` - Format validation
- `TestEdgeCases` - Boundary conditions
- `TestLLMDateExtractionSimulation` - LLM capabilities

### 3. **test_search_filtering.py** - Result Processing
Tests for filtering and deduplicating search results:

- **URL Deduplication**: Exact matches, case sensitivity, query params
- **Relevance Filtering**: Keyword-based filtering
- **Source Filtering**: Domain and platform filtering
- **Quality Filtering**: Empty snippets, trusted domains
- **Batch Operations**: Pipeline processing

**Run with:**
```bash
pytest tests/test_search_filtering.py -v
```

**Key test classes:**
- `TestSearchResultFiltering` - Basic filtering
- `TestURLDeduplication` - URL-based dedup (5+ tests)
- `TestMultipleSourceDeduplication` - Cross-platform dedup
- `TestSearchResultQuality` - Quality metrics
- `TestBatchFiltering` - Pipeline operations

## Sample Data and Fixtures

### Available Fixtures (conftest.py)

```python
# In any test, use these fixtures:

def test_something(mock_llm_client):
    """Mock LLM client already configured"""
    pass

def test_search(sample_search_results):
    """10 pre-built event search results"""
    pass

def test_articles(sample_article_data):
    """Sample high/medium/low relevance articles"""
    pass

def test_events(sample_event_data):
    """Sample complete/minimal event data"""
    pass

def test_dates(date_extraction_samples):
    """Sample text with various date formats"""
    pass
```

### Using Sample Data

```python
from tests.fixtures.sample_search_results import (
    get_sample_event_search_results,
    get_sample_news_search_results,
    get_duplicate_event_pairs,
    get_date_extraction_test_cases,
)

def test_with_samples():
    """Use pre-built sample data"""
    events = get_sample_event_search_results()
    assert len(events) == 10
```

## Running Specific Test Scenarios

### Test Relevance Scoring

```bash
# Run all relevance tests
pytest tests/test_agents.py::TestNewsResearchAgent -v -k relevance

# Run specific relevance test
pytest tests/test_agents.py::TestNewsResearchAgent::test_quick_relevance_check_high_relevance -v
```

### Test Date Extraction

```bash
# Run all date extraction tests
pytest tests/test_date_extraction.py -v

# Run specific date format test
pytest tests/test_date_extraction.py::TestDateExtractionFromURL -v

# Run edge case tests
pytest tests/test_date_extraction.py::TestEdgeCases -v
```

### Test Deduplication

```bash
# Run URL deduplication tests
pytest tests/test_search_filtering.py::TestURLDeduplication -v

# Run dedup-specific tests
pytest tests/ -v -k "deduplicate"
```

### Test Error Handling

```bash
# Run error handling tests
pytest tests/test_agents.py::TestErrorHandling -v

# Run failure scenarios
pytest tests/ -v -k "error or fail"
```

## Understanding Test Output

### Successful Test Run

```
tests/test_agents.py::TestNewsResearchAgent::test_quick_relevance_check_high_relevance PASSED [2%]
tests/test_agents.py::TestNewsResearchAgent::test_quick_relevance_check_medium_relevance PASSED [4%]
```

### Failed Test

```
tests/test_agents.py::TestNewsResearchAgent::test_quick_relevance_check_high_relevance FAILED [2%]

AssertionError: assert 85 == 95
  expected 95 but got 85
```

### Test with Warnings

```
tests/test_agents.py::TestNewsResearchAgent::test_quick_relevance_check_high_relevance PASSED [2%]
  (warnings suppressed with --disable-warnings)
```

## Coverage Analysis

### Generate Coverage Report

```bash
# Create HTML coverage report
pytest tests/ --cov=src --cov-report=html

# View the report
open htmlcov/index.html
```

### Coverage Targets

The test suite aims for:
- **Statements**: >80% coverage
- **Branches**: >75% coverage
- **Functions**: >80% coverage
- **Lines**: >80% coverage

Check coverage:
```bash
pytest tests/ --cov=src --cov-report=term-missing
```

## Async Tests

### Running Async Tests Only

```bash
pytest tests/ -v -m asyncio
```

### Running Non-Async Tests

```bash
pytest tests/ -v -m "not asyncio"
```

### Debugging Async Tests

```bash
# Show full output including prints
pytest tests/test_agents.py -v -s

# Show local variables on failure
pytest tests/test_agents.py -v -l

# Increase timeout for slow tests
pytest tests/test_agents.py -v --timeout=300
```

## Continuous Integration

### For CI/CD Pipelines

```bash
# Complete test suite with coverage and detailed reporting
pytest tests/ \
  -v \
  --tb=short \
  --cov=src \
  --cov-report=term-missing \
  --cov-report=xml \
  --junit-xml=test-results.xml
```

### GitHub Actions / GitLab CI

The tests are designed to run in:
- GitHub Actions workflows
- GitLab CI/CD pipelines
- Jenkins
- Local CI systems

## Troubleshooting

### Pytest Not Found

```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Install test requirements
pip install -r requirements-dev.txt

# Verify installation
pytest --version
```

### Import Errors

```bash
# Ensure PYTHONPATH includes project root
export PYTHONPATH="${PYTHONPATH}:/home/robbe/blkout-platform/apps/research-agent"

# Run pytest
pytest tests/ -v
```

### Async Test Issues

```bash
# Check pytest-asyncio is installed
pip install pytest-asyncio

# If still failing, run with verbose output
pytest tests/test_agents.py -v -s --tb=long
```

### Module Not Found

```bash
# Run from project root
cd /home/robbe/blkout-platform/apps/research-agent

# Ensure venv is activated
source venv/bin/activate

# Run tests
pytest tests/ -v
```

### Slow Tests

```bash
# See which tests are slowest
pytest tests/ -v --durations=10

# Run only fast tests
pytest tests/ -v -m "not slow"

# Run specific fast test
pytest tests/test_date_extraction.py -v
```

## Test Development

### Adding New Tests

1. Create test file in `tests/` with `test_` prefix
2. Create test class with `Test` prefix
3. Create test method with `test_` prefix

```python
# tests/test_new_feature.py
import pytest

class TestNewFeature:
    """Test new feature implementation"""

    def test_basic_case(self, fixture):
        """Test basic functionality"""
        assert function(input) == expected

    @pytest.mark.asyncio
    async def test_async_case(self, mock_llm_client):
        """Test async functionality"""
        result = await async_function()
        assert result is not None
```

### Using Fixtures

```python
def test_with_fixtures(mock_llm_client, sample_search_results):
    """Use multiple fixtures in one test"""
    # mock_llm_client is already configured
    # sample_search_results is already loaded
    pass
```

### Mocking External Services

```python
from unittest.mock import patch, AsyncMock

def test_with_mocks():
    """Test with mocked dependencies"""
    with patch("src.agents.get_llm_client") as mock_get:
        mock_client = AsyncMock()
        mock_get.return_value = mock_client

        # Now LLM calls are mocked
        agent = NewsResearchAgent()
```

## Performance Testing

### Benchmark Specific Operations

```bash
# Show timing for each test
pytest tests/ -v --durations=0

# Show 10 slowest tests
pytest tests/ -v --durations=10

# Profile specific test
pytest tests/test_agents.py::TestNewsResearchAgent::test_research_filters_by_relevance -v --durations=0
```

### Performance Targets

- Unit tests: <100ms each
- Integration tests: <1 second each
- Full test suite: <60 seconds

## Documentation

For detailed test documentation, see:
- `tests/README.md` - Full test documentation
- `pytest.ini` - Pytest configuration
- `conftest.py` - Fixture definitions
- `test_*.py` files - Individual test docstrings

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest-Asyncio](https://pytest-asyncio.readthedocs.io/)
- [Python unittest.mock](https://docs.python.org/3/library/unittest.mock.html)
- [Testing Best Practices](https://docs.pytest.org/en/stable/how-to.html)

## Support

For questions about tests:

1. Check test docstrings for explanation
2. Review `tests/README.md` for detailed documentation
3. Check individual test implementations for examples
4. Review fixtures in `conftest.py` for mock setup
