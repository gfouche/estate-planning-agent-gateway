# Unit Tests for Estate Planning Agent Gateway

This directory contains unit tests for the Estate Planning Agent Gateway project.

## Setup

Before running the tests, make sure you have the required dependencies:

```bash
pip install -r requirements-test.txt
```

## Running Tests

You can run the tests using either unittest or pytest.

### Using unittest

```bash
python run_tests.py
```

### Using pytest

```bash
pytest
```

For a coverage report:

```bash
pytest --cov=../../infrastructure --cov=../../ep_agent
```

## Test Structure

- `test_setup_identity.py` - Tests for the `infrastructure/setup_identity.py` module
- More test files will be added as the project grows

## Writing New Tests

When adding new tests:

1. Create a new file named `test_<module_name>.py`
2. Import the module you want to test
3. Create a class that inherits from `unittest.TestCase`
4. Write test methods that start with `test_`
5. Use mocks as needed to isolate the code being tested