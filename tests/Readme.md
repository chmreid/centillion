# Tests

## How to Run

### Running All Tests

From the root of the centillion repository, run:

```
pytest tests
```

### Running Specific Tests

From the root of the centillion repository, run:

```
pytest tests/test_X.py
```

## Standalone vs Integration Tests

There are two kinds of tests here, standalone tests and integration tests.

Standalone tests do not make any external API calls, everything is mocked
and done locally. Real API credentials are not required.

Integration testsmake real API calls to external APIs, so they require real
API credentials. These tests are performed on Travis, which has an encrypted
copy of valid API credentials for the centillion travis test account.

## List of Tests

List of tests, in logical order, and a brief description of what it tests:

- `test_config.py` tests the static Config class

- `test_doctypes.py` tests the base Doctype class and related utilities

- `test_doctypes_github.py` tests all Github Doctype classes and related utilities

- `test_doctypes_gdrive.py` tests all Google Drive Doctype classes and related utilities 

## Test Support 

Support for testing is provided by several modules:

* `context.py` defines several useful context managers

* `decorators.py` defines decorators that control how and when tests are run

* `fixtures.py` defines test fixtures that are generally useful for multiple tests

* `mixins.py` defines mixin classes for methods used by multiple tests

