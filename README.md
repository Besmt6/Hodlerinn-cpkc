# Hodler Inn CPKC Portal

Hotel/kiosk system with:
- FastAPI backend (`backend/`)
- React frontend (`frontend/`)
- Dockerized runtime and AWS CI/CD workflows

## Hosted MongoDB (Atlas)
This project now expects an external MongoDB connection string.

Example:
```env
MONGO_URL=mongodb+srv://Hodlerinn:<db_password>@cluster0.hi5zsox.mongodb.net/hodler_inn?retryWrites=true&w=majority&appName=Cluster0
```

## Local Run (Docker)
```bash
cp .env.example .env
# edit .env with real values

docker compose up -d --build
```

- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8001`

## CI/CD
- CI workflow: `.github/workflows/ci.yml`
- AWS deploy workflow: `.github/workflows/deploy-aws.yml`

See full deployment instructions in `DEPLOY_README.md`.
