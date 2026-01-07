# BLKOUT Research Agent Test Suite

Comprehensive test suite for the BLKOUT Research Agent with focus on date extraction, event deduplication, relevance filtering, and search result processing.

## Test Structure

```
tests/
├── __init__.py                      # Test package initialization
├── conftest.py                      # Pytest fixtures and configuration
├── README.md                        # This file
├── test_agents.py                  # Tests for NewsResearchAgent and EventsDiscoveryAgent
├── test_date_extraction.py         # Tests for date extraction from various formats
├── test_search_filtering.py        # Tests for search result filtering and deduplication
└── fixtures/
    ├── __init__.py
    └── sample_search_results.py    # Sample data for testing
```

## Running Tests

### Quick Start

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_agents.py

# Run specific test class
pytest tests/test_agents.py::TestNewsResearchAgent

# Run specific test
pytest tests/test_agents.py::TestNewsResearchAgent::test_quick_relevance_check_high_relevance
```

### Filtering Tests

```bash
# Run only async tests
pytest -m asyncio

# Run only unit tests (not integration)
pytest -m unit

# Run specific tests by name
pytest -k "relevance"

# Run tests excluding slow tests
pytest -m "not slow"

# Run tests for specific feature
pytest -k "deduplication"
```

### Coverage Analysis

```bash
# Install coverage
pip install pytest-cov

# Run tests with coverage report
pytest --cov=src --cov-report=html

# View coverage report
open htmlcov/index.html
```

### Detailed Output

```bash
# Show local variables on failure
pytest -l

# Show full tracebacks
pytest --tb=long

# Show all captured output
pytest -v -s

# Stop on first failure
pytest -x

# Show slowest tests
pytest --durations=10
```

## Test Categories

### test_agents.py
Tests for the main research agents:

- **TestNewsResearchAgent**: News article discovery and relevance filtering
  - Quick relevance checking (keyword-based)
  - LLM-based relevance analysis
  - High/medium/low relevance detection
  - Case-insensitive matching
  - Filter by relevance score
  - Proper result structure

- **TestEventsDiscoveryAgent**: Event discovery and processing
  - Date extraction from various formats
  - Discovery from search results
  - Discovery from scraping
  - Combined discovery (search + scraping)
  - Event result structure validation

- **TestDeduplication**: URL-based deduplication
  - Exact URL matching
  - First occurrence preservation
  - Case sensitivity

- **TestErrorHandling**: Graceful error handling
  - LLM failure fallback
  - Date extraction error handling
  - Partial success scenarios

### test_date_extraction.py
Comprehensive date extraction testing:

- **TestDateExtractionFromTitle**: Extracting dates from event titles
  - ISO format (2026-01-07)
  - Month abbreviations (Jan 7)
  - Ordinal dates (21st February)

- **TestDateExtractionFromURL**: Extracting dates from URLs
  - `/events/2026-01-07-party`
  - `/2026/01/07/event`
  - `/2026-01-07/`

- **TestDateExtractionFromSnippet**: Extracting from descriptions
  - ISO format in snippet
  - Day names with dates
  - Relative dates
  - Multiple dates

- **TestDateValidation**: Date format and logic validation
  - ISO format compliance
  - Future date checking
  - Invalid date detection
  - Leap year handling
  - Year boundaries

- **TestEdgeCases**: Boundary conditions and special cases
  - No date present
  - Multiple dates (choosing correct one)
  - Past date filtering
  - Ambiguous formats
  - Whitespace handling

- **TestSearchResultDateExtraction**: Combined extraction strategies
  - Priority: URL > ISO snippet > title
  - Fallback strategies
  - Complete search result processing

- **TestLLMDateExtractionSimulation**: LLM capabilities
  - Natural language date parsing
  - Future date validation
  - Multiple date selection

### test_search_filtering.py
Search result filtering and deduplication:

- **TestSearchResultFiltering**: Basic filtering operations
  - Filter by source domain
  - Filter by source name
  - Filter irrelevant results
  - Filter by publish date
  - Filter by content keywords

- **TestURLDeduplication**: URL-based deduplication
  - Exact URL matching
  - First occurrence preservation
  - Case sensitivity
  - Query parameter handling
  - Trailing slash differences

- **TestMultipleSourceDeduplication**: Cross-source deduplication
  - Same event on multiple platforms
  - Real duplicate detection

- **TestSearchResultQuality**: Quality filtering
  - Empty snippet filtering
  - Minimum snippet length
  - Trusted domain filtering

- **TestBatchFiltering**: Bulk operations
  - Complete filter + deduplicate pipeline
  - Order preservation

## Fixtures (conftest.py)

Available fixtures for use in tests:

```python
# Event loop for async tests
@pytest.fixture
def event_loop():
    """Create event loop for async tests"""

# Mock LLM client
@pytest.fixture
def mock_llm_client():
    """Mock LLM client for testing"""

# Mock search agent
@pytest.fixture
def mock_search_agent():
    """Mock search agent for testing"""

# Mock database
@pytest.fixture
def mock_database():
    """Mock database client for testing"""

# Sample data
@pytest.fixture
def sample_search_results():
    """Sample search results for testing"""

@pytest.fixture
def sample_article_data():
    """Sample article data for relevance testing"""

@pytest.fixture
def sample_event_data():
    """Sample event data for testing"""

@pytest.fixture
def date_extraction_samples():
    """Sample text with various date formats"""
```

## Sample Data (fixtures/sample_search_results.py)

Pre-built sample data sets:

- `get_sample_event_search_results()`: 10 diverse event results
  - Complete events with all fields
  - Minimal events with missing data
  - Duplicates and similar events
  - High/medium/low relevance
  - Various date formats

- `get_sample_news_search_results()`: 10 news articles
  - High relevance (explicit Black LGBTQ+ UK content)
  - Medium relevance (partial intersectionality)
  - Low relevance (unrelated content)

- `get_duplicate_event_pairs()`: Test data for deduplication
  - Exact duplicates (should deduplicate)
  - Different events (should NOT deduplicate)
  - Same content, different domains
  - URL variations

- `get_date_extraction_test_cases()`: Date format examples
  - ISO format variations
  - Natural language formats
  - No date cases

- `get_relevance_test_cases()`: Relevance scoring examples
  - High relevance threshold
  - Medium relevance
  - Low relevance

- `get_integration_test_scenario()`: Complete workflow scenario

## Key Testing Patterns

### Testing Async Code

```python
@pytest.mark.asyncio
async def test_async_function(mock_llm_client):
    """Test async function"""
    # Mock async calls
    mock_llm_client.complete = AsyncMock(return_value="2026-01-07")

    # Call async function
    result = await agent.method()

    # Assert results
    assert result == expected
```

### Testing with Mocks

```python
def test_with_mocks(mock_llm_client):
    """Test with mocked dependencies"""
    with patch("src.agents.get_llm_client", return_value=mock_llm_client):
        # Code using mocked LLM
        agent = NewsResearchAgent()
        # Agent uses mocked LLM instead of real one
```

### Testing Edge Cases

```python
def test_edge_case():
    """Test boundary conditions"""
    # Empty input
    result = process([])
    assert result == []

    # None input
    result = process(None)
    assert result is None

    # Very large input
    large_input = [x for x in range(10000)]
    result = process(large_input)
    assert len(result) == 10000
```

## Common Issues and Solutions

### AsyncIO Warnings

If you see `RuntimeWarning: Event loop is closed`:

```python
# Use fixture provided in conftest.py
@pytest.fixture
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
```

### Mock Not Being Used

Ensure patching is done at the import location:

```python
# Correct - patch where it's imported
with patch("src.agents.get_llm_client", return_value=mock):
    agent = NewsResearchAgent()

# Wrong - patch where it's defined
with patch("src.llm.get_llm_client", return_value=mock):
    # This won't affect agents.py if it imports the original
```

### Test Discovery Not Working

Ensure:
1. Test files start with `test_`
2. Test classes start with `Test`
3. Test functions start with `test_`
4. Files are in `tests/` directory

## Performance Benchmarks

Target test execution times:

- Unit tests: < 5 seconds total
- Integration tests: < 30 seconds
- Full suite: < 1 minute

Run with timing:

```bash
pytest --durations=10
```

## Continuous Integration

For CI/CD pipelines, use:

```bash
# Fail fast, show output, generate coverage
pytest -x -v --cov=src --cov-report=term-missing:skip-covered --cov-report=xml
```

## Contributing Tests

When adding new tests:

1. Follow existing naming conventions
2. Add docstrings explaining what is tested
3. Use meaningful assertion messages
4. Group related tests in classes
5. Use fixtures instead of hardcoding data
6. Mock external dependencies
7. Test both success and failure paths
8. Include edge cases

Example:

```python
class TestNewFeature:
    """Test new feature implementation"""

    def test_basic_functionality(self, fixture):
        """Test basic behavior of new feature"""
        result = feature_function(valid_input)
        assert result == expected_output

    def test_error_handling(self):
        """Test error handling in new feature"""
        with pytest.raises(ValueError):
            feature_function(invalid_input)

    def test_edge_case(self):
        """Test boundary condition"""
        result = feature_function(boundary_input)
        assert result == boundary_output
```

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest Async](https://pytest-asyncio.readthedocs.io/)
- [Mock/Patch Guide](https://docs.python.org/3/library/unittest.mock.html)
- [Fixtures Guide](https://docs.pytest.org/en/stable/how-to_fixture.html)

## Troubleshooting

### Tests Won't Import Modules

```bash
# Add current directory to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:/home/robbe/blkout-platform/apps/research-agent"
pytest

# Or run from project root
cd /home/robbe/blkout-platform/apps/research-agent
pytest
```

### Import Errors

Ensure virtual environment is activated:

```bash
cd /home/robbe/blkout-platform/apps/research-agent
source venv/bin/activate
pytest
```

### Async Test Timeouts

Increase timeout in pytest.ini:

```ini
[pytest]
timeout = 300  # seconds
```

Or per test:

```python
@pytest.mark.timeout(60)
async def test_long_operation():
    ...
```

## Contact

For test-related questions or issues, refer to the main project documentation.
