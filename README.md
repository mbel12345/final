# Repos
Github: https://github.com/mbel12345/final/
Dockerhub: https://hub.docker.com/r/msb64/final/

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
Github Actions will run on any pushes or pull requests. Only pull requests will result in the deployment step.
Pre-requisite: In Dockerhub, create an Access Token, then add it to Environment var "DOCKERHUB_TOKEN" in GitHub. Add DOCKERHUB_USERNAME also.

Add these environment variables in Github:
  - POSTGRES_USER = postgres
  - POSTGRES_PASSWORD = postgres
