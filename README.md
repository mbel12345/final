# Repos
Github: https://github.com/mbel12345/final/<br>
Dockerhub: https://hub.docker.com/r/msb64/final/

# New Feature (Statistics Page)

Key stats for the user:
- Total Calculations - Number of calculations of each type, and grand total of all calculations
- Total Calculations - Pie chart showing this information
- Calculations Per Day - Line graph showing the number of calculations of a selected type (or all) for a given day
- Average Operands - Average number of operands for calculations of each type, and average for all calculations
- Average Result - Average result for calculations of each type, and average for all calculations

User can filter basesd on Calculation Type (for the Calculations Per Day), Start Time (UTC), and End Time (UTC).

User can easily switch between the Dashboard and Statistics pages using the Navigation at the top.

To demonstrate adding a new database model, I created CalcsPerDay table (a cache) that stores user_id, calc_type, date, count.<br>
This table is intended to be updated daily (if this was in a PROD environment), so that computing the count does not have to be re-done for days farther back than a week ago.<br>
For a given user-calc_type-date combo, if it is not in the cache and/or it is less than 7 days ago, CalcsPerDay is recalculated on the fly to ensure the data does not become stale.<br>
These recalculations are saved/cached to CalcsPerDay.

I added schemas for each response type in the /statistics API calls.

I placed all /statistics routes in routers/statistics.py and all HTML for statistics in templates/statistics.html.

All statistics tests are either in tests/integration/test_statistics_routes.py or tests/e2e/test_statistics_ui.py.<br>
Another test improvement was standardizing the creation of dummy data to prevent duplicate user failures when running without dropping DB first (always use get_unique_user_data function).<br>
Various functions such as goto (for playwright) and login (in UI) were moved to conftest.py to allow me to reuse code and separate the statistics test from the ever-growing test_routes.py and test_ui.py.

To help test the Calculations Per Day line graph in the UI (in addition to playwright tests), I wrote a standalone python script that writes dummy data to CalcsPerDay for previous dates.<br>
To run the script:<br>
python3 -m tests.e2e.add_test_data

# Project Setup

## Set up Repo
In Github:
Create new repo called final and make sure it is public

In WSL/VS Code Terminal:
```bash
mkdir final
cd final/
git init
git branch -m main
git remote add origin git@github.com:mbel12345/final.git
vim README.md
git add . -v
git commit -m "Initial commit"
git push -u origin main
```

## Set up virtual environment
In WSL/VS Code Terminal:
```bash
python3 -m venv venv
source venv/bin/activate
python3 -m pip install -r requirements.txt
playwright install
```

## Build image and start container
Note: This must be already running for all local testing
In WSL/VS Code Terminal:
```bash
docker compose down -v
docker compose up --build
```

## Access the app in browser

Go to: http://localhost:8000/

## Run test cases locally (including Playwright and route testing)

In second WSL/VS Code Terminal:
```bash
pytest
```

To run the test cases while preserving the database, copy .env_local to .env, which has DROP_DB=False

## Run FastAPI app locally
In WSL/VS Code Terminal:
```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

## Configure Github Actions
Github Actions will run on any pushes or pull requests. Only pull requests will result in the deployment step.<br>
Pre-requisite: In Dockerhub, create an Access Token, then add it to Environment var "DOCKERHUB_TOKEN" in GitHub. Add DOCKERHUB_USERNAME also.

Add these environment variables in Github:
  - POSTGRES_USER = postgres
  - POSTGRES_PASSWORD = postgres
