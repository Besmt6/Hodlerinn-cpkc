# Hodler Inn Deployment Guide (AWS + Hosted MongoDB)

This repository is now prepared for **hosted MongoDB (Atlas)** and no longer requires a local Mongo container in `docker-compose.yml`.

---

## 1) Local/Server Runtime with Docker Compose

### Prerequisites
- Docker + Docker Compose plugin
- A valid MongoDB Atlas connection string

### Setup
```bash
cp .env.example .env
# Edit .env and set at minimum:
# - MONGO_URL
# - ADMIN_PASSWORD
# - REACT_APP_BACKEND_URL
```

### Start
```bash
docker compose up -d --build
```

### Verify
```bash
curl -f http://localhost:8001/health
# expected: {"status":"healthy", ...}
```

---

## 2) AWS Production Architecture (Recommended)

- **ECR**: container image registry
- **ECS Fargate**: run backend/frontend containers
- **ALB**: ingress + TLS termination
- **Route53 + ACM**: DNS + certificates
- **SSM Parameter Store / Secrets Manager**: secrets (`MONGO_URL`, passwords, keys)
- **CloudWatch Logs**: logs/metrics

---

## 3) CI/CD with GitHub Actions

This repo includes two workflows:

1. **CI** (`.github/workflows/ci.yml`)
   - Python syntax check for backend.
   - Frontend install + build.

2. **AWS Deploy** (`.github/workflows/deploy-aws.yml`)
   - Builds backend/frontend images.
   - Pushes to ECR.
   - Updates ECS services.

### Required GitHub Secrets
- `AWS_ROLE_ARN`
- `AWS_REGION`
- `AWS_ACCOUNT_ID`
- `ECR_BACKEND_REPOSITORY`
- `ECR_FRONTEND_REPOSITORY`
- `ECS_CLUSTER`
- `ECS_BACKEND_SERVICE`
- `ECS_FRONTEND_SERVICE`

Use GitHub OIDC with `aws-actions/configure-aws-credentials` (no long-lived AWS keys).

---

## 4) Migration Note (MongoDB)

Old setup used local Mongo (`mongodb://mongodb:27017`).
Now use Atlas in `.env`:

```env
MONGO_URL=mongodb+srv://Hodlerinn:<db_password>@cluster0.hi5zsox.mongodb.net/hodler_inn?retryWrites=true&w=majority&appName=Cluster0
```

> Replace `<db_password>` and avoid committing `.env`.

---

## 5) Minimal ECS Environment Variables

Backend task env vars:
- `MONGO_URL`
- `DB_NAME`
- `ADMIN_PASSWORD`
- `ENCRYPTION_KEY`
- `ADMIN_AUTH_SECRET`
- `CORS_ORIGINS`
- integration secrets as required

Frontend task env vars:
- `REACT_APP_BACKEND_URL` (usually ALB/API domain)

---

## 6) Operational Checklist

- [ ] `CORS_ORIGINS` locked to trusted domains only
- [ ] `ADMIN_PASSWORD` rotated and strong
- [ ] `ADMIN_AUTH_SECRET` explicitly set
- [ ] Atlas network access restricted to VPC egress/NAT IPs
- [ ] ECS task roles least-privilege
- [ ] CloudWatch alarms for 5xx / unhealthy targets
