All contributions to *ormar* are welcomed!

## Issues

To make it as simple as possible for us to help you, please include the following:

*  OS 
*  python version
*  ormar version
*  database backend (mysql, sqlite or postgresql)

Please try to always include the above unless you're unable to install *ormar* or **know** it's not relevant
to your question or feature request.

## Pull Requests

It should be quite straight forward to get started and create a Pull Request.

!!! note
    Unless your change is trivial (typo, docs tweak etc.), please create an issue to discuss the change before
    creating a pull request.

To make contributing as easy and fast as possible, you'll want to run tests and linting locally. 

You'll need to have **python 3.6**, **3.7**, or **3.8**, **virtualenv**, and **git** installed.

```bash
# 1. clone your fork and cd into the repo directory
git clone git@github.com:<your username>/ormar.git
cd ormar

# 2. Set up a virtualenv for running tests
virtualenv -p `which python3.7` env
source env/bin/activate
# (or however you prefer to setup a python environment, 3.6 will work too)

# 3. Install ormar, dependencies and test dependencies
pip install -r requirements.txt

# 4. Checkout a new branch and make your changes
git checkout -b my-new-feature-branch
# make your changes...

# 5. Formatting and linting
# ormar uses black for formatting, flake8 for linting and mypy for type hints check
# run all of the following as all those calls will be run on travis after every push
black ormar
flake8 ormar
mypy --config-file mypy.ini ormar

# 6. Run tests
# on localhost all tests are run against sglite backend
# rest of the backends will be checked after push
pytest -svv --cov=ormar --cov=tests --cov-fail-under=100 --cov-report=term-missing

# 7. Build documentation
mkdocs build
# if you have changed the documentation make sure it builds successfully
# you can also use `mkdocs serve` to serve the documentation at localhost:8000

# ... commit, push, and create your pull request
```
