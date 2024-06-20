# jobby

## Installation

This will install the app into a docker container on your system.
After the installation is complete, the app should be accessible under: http://localhost/jobby/

### Linux

It is recommended to pass the UID and GID to avoid permission issues with docker volumes:
```sh
python install.py --uid="$(id -u)" --gid="$(id -g)" --password=supersecret
```


## Development

### Install project
1. Clone repository:
	```commandline
	git clone https://github.com/Actionb/jobby.git
	cd jobby
	```
2. Activate virtual environment:
	```commandline
	python3 -m venv .venv && source .venv/bin/activate
	```
3. Install dependencies:
	```commandline
	pip install -r requirements/dev.txt
	```
4. Run migrations:
	```commandline
	python manage.py migrate
	```
5. (optional) Install pre-commit hooks (see: [pipx](https://pipx.pypa.io/latest/installation/#installing-pipx) and [pre-commit](https://pre-commit.com/#install)):
	```commandline
	python3 -m pip install --user pipx
	python3 -m pipx ensurepath
	pipx install pre-commit
	pre-commit install
	```
 
### Development server

To start the Django development server use
```commandline
python manage.py runserver
```

### Run tests

Use 
```commandline
make test
```
to run tests with coverage, and then check the coverage report with
```commandline
firefox htmlcov/index.html
```

#### Playwright

To run playwright tests, make sure you have installed the browsers:
```commandline
playwright install
```
Then run the tests with:
```commandline
make test-pw
```

### Linting and formatting

Use 
```commandline
make lint
```
to run linters.
Use
```commandline
make reformat
```
to auto-reformat python code.

### Check for security vulnerabilities

Invoke [pip-audit](https://pypi.org/project/pip-audit/) with:
```commandline
make audit
```
 
### Adding dependencies

To add dependencies, check `requirements/README.md` for a How-To.