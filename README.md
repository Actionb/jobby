# jobby

## Installation

### Requirements

Docker must be installed:  
* Linux: https://docs.docker.com/engine/install/ (or use docker's own [convenience script](https://get.docker.com/))
* Windows: https://docs.docker.com/desktop/install/windows-install/

### Linux

1. download the archive: https://github.com/Actionb/jobby/archive/refs/heads/main.tar.gz
2. unpack: 
   ```shell
   mkdir ~/jobby && tar -xf jobby-main.tar.gz -C ./jobby && cd ./jobby/jobby-main
   ```
3. run the installation script:
   ```shell
   python3 install.py --uid=$(id -u) --gid=$(id -g) --password=supersecret
   ```
   It is recommended to pass the UID and GID to avoid permission issues with docker volumes.


All-in-one, copy and paste directly into your terminal:
```shell
curl -fsL https://github.com/Actionb/jobby/archive/refs/heads/main.tar.gz -o /tmp/jobby.tar.gz
mkdir ~/jobby && tar -xf /tmp/jobby.tar.gz -C ~/jobby && cd ~/jobby/jobby-main
python3 install.py --uid=$(id -u) --gid=$(id -g) --password=supersecret
rm /tmp/jobby.tar.gz
```

After the installation is complete, the app should be accessible under: http://localhost:8787/jobby/

## Development

### Requirements

Postgres must be installed: https://www.postgresql.org/download/

### Install project
1. Clone repository:
    ```shell
    git clone https://github.com/Actionb/jobby.git
    cd jobby
    ```
2. Activate virtual environment:
    ```shell
    python3 -m venv .venv && source .venv/bin/activate
    ```
3. Install dependencies:
    ```shell
    pip install -r requirements/dev.txt
    ```
4. Create development database:
    ```shell
    createdb jobby
    ```
5. Run migrations:
    ```shell
    python manage.py migrate
    ```
6. (optional) Install pre-commit hooks (see: [pipx](https://pipx.pypa.io/latest/installation/#installing-pipx) and [pre-commit](https://pre-commit.com/#install)):
    ```shell
    python3 -m pip install --user pipx
    python3 -m pipx ensurepath
    pipx install pre-commit
    pre-commit install
    ```
 
### Development server

To start the Django development server use
```shell
python manage.py runserver
```

### Run tests

Use 
```shell
make test
```
to run tests with coverage, and then check the coverage report with
```shell
firefox htmlcov/index.html
```

#### Playwright

To run playwright tests, make sure you have installed the browsers:
```shell
playwright install
```
Then run the tests with:
```shell
make test-pw
```

### Linting and formatting

Use 
```shell
make lint
```
to run linters.
Use
```shell
make reformat
```
to auto-reformat python code.

### Check for security vulnerabilities

Invoke [pip-audit](https://pypi.org/project/pip-audit/) with:
```shell
make audit
```
 
### Adding dependencies

To add dependencies, check `requirements/README.md` for a How-To.