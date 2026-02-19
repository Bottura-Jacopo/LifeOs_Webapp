# LifeOs_Webapp

## Run DB
docker compose up -d

## Run API
cd backend
python -m venv .venv
# activate venv...
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
