# Development Guidelines for atlas_mcp

## Development

* When adding new functionality, please introduce a simple unit test to test.
* When tracking down a bug at the request of the user, please generate a test case that triggers the bug before fixing the bug.
* Linting: both `black` and `flake8` should pass. Lines can be up to 99 characters long.

## Tests

* Run tests with `pytest`. Make sure to setup the virtual environment first!
* When authoring new test, put them in a file `tests/test_xxx.py` where `xxx` is the name of the file of the function you are testing.
