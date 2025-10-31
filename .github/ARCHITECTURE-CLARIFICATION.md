# Architecture Clarification: Local vs Production

## ⚠️ Important Understanding

**Question**: Why doesn't the production deployment use Docker for PostgreSQL, OpenSearch, and S3?

**Answer**: **It does use them, but via AWS managed services, not Docker containers!**

---

## 🏗️ Two Different Deployment Modes

### 1. **Local Development** (What You See in docker-compose.yml)

```
Your Machine
├── InvenioRDM App (local Python or Docker)
├── PostgreSQL (Docker container) ← postgres:14.13
├── OpenSearch (Docker container) ← opensearchproject/opensearch:2.17.1
├── S3 (Docker container) ← MinIO
├── Redis (Docker container) ← redis:7
├── RabbitMQ (Docker container) ← rabbitmq:3-management
├── Cantaloupe (Docker container) ← edirom/cantaloupe
├── pgAdmin (Docker container) ← dpage/pgadmin4
└── OpenSearch Dashboards (Docker container) ← opensearchproject/opensearch-dashboards
```

**Purpose**: Fast local development without AWS costs

---

### 2. **Production Deployment** (Via Terraform in inveniordm-terraform)

```
AWS Cloud (Deployed via Terraform)
├── InvenioRDM App (ECS Fargate containers)
│   ├── Web UI service
│   ├── Web API service
│   └── Celery worker service
├── PostgreSQL → AWS RDS PostgreSQL 15 ✅
├── OpenSearch → AWS OpenSearch Service ✅
├── S3 → AWS S3 Bucket ✅
├── Redis → AWS ElastiCache Redis ✅
├── RabbitMQ → Amazon MQ (managed RabbitMQ) ✅
├── CDN → CloudFront
└── Load Balancer → Application Load Balancer
```

**Purpose**: Production-grade, scalable, managed infrastructure

---

## 📊 Side-by-Side Comparison

| Component | Local Dev | Production | Why Different? |
|-----------|-----------|------------|----------------|
| **App Container** | Docker or local Python | ECS Fargate | Production needs auto-scaling |
| **PostgreSQL** | Docker: `postgres:14.13` | AWS RDS PostgreSQL 15 | RDS = managed, backups, HA |
| **OpenSearch** | Docker: `opensearchproject/opensearch:2.17.1` | AWS OpenSearch Service | Managed, backups, snapshots |
| **S3 Storage** | Docker: MinIO | AWS S3 | S3 = managed, durable, CDN-ready |
| **Redis** | Docker: `redis:7` | AWS ElastiCache Redis | Managed, HA, automatic failover |
| **RabbitMQ** | Docker: `rabbitmq:3-management` | Amazon MQ | Managed, HA, automatic updates |
| **Frontend** | Local Nginx | ECS + CloudFront CDN | CDN for global distribution |
| **Dev Tools** | ✅ Cantaloupe, pgAdmin, Dashboards | ❌ Not needed | Debug tools only for dev |

---

## 🔍 How They Connect

### Local Development Connection Flow
```
Browser (https://127.0.0.1:5000)
    ↓
InvenioRDM App (local or Docker)
    ↓
PostgreSQL Docker Container (localhost:5432)
    ↓
OpenSearch Docker Container (localhost:9200)
    ↓
MinIO S3 Docker Container (localhost:9000)
```

### Production Connection Flow
```
Browser (https://turath.example.com)
    ↓
CloudFront CDN
    ↓
Application Load Balancer
    ↓
ECS Fargate (InvenioRDM containers)
    ↓
AWS RDS PostgreSQL (managed endpoint)
    ↓
AWS OpenSearch Service (managed endpoint)
    ↓
AWS S3 (managed bucket)
```

---

## 🚀 Deployment Workflow

### Local Development
```bash
# 1. Start Docker services
docker compose up -d

# 2. Run app locally
invenio-cli run

# All services are Docker containers on your machine
```

### Production Deployment
```bash
# 1. Terraform creates AWS infrastructure
cd inveniordm-terraform
terraform apply  # Creates RDS, OpenSearch, S3, etc.

# 2. GitHub Actions builds Docker images
git push  # Triggers CI/CD → builds app images

# 3. Manual deployment (due to AWS MFA)
aws-login  # Mobile 2FA approval
./scripts/deploy.sh  # Updates ECS services with new images
```

---

## 💰 Cost Comparison

### Local Development
- **Cost**: $0 (uses local Docker)
- **Resources**: Your machine's CPU/RAM
- **Limitations**: Not scalable, single-node

### Production (AWS)
- **Cost**: ~$577-720/month
  - RDS PostgreSQL: ~$150/month
  - OpenSearch Service: ~$200/month
  - ECS Fargate: ~$100/month
  - S3: ~$50/month (depends on storage)
  - ElastiCache Redis: ~$50/month
  - Amazon MQ: ~$45/month
  - CloudFront CDN: variable
- **Resources**: Auto-scales based on demand
- **Benefits**: HA, backups, managed updates

---

## 📝 Terraform Infrastructure Files

The production infrastructure is defined in separate Terraform files:

| File | Creates | Local Equivalent |
|------|---------|------------------|
| `5-rds.tf` | AWS RDS PostgreSQL | Docker: postgres:14.13 |
| `9-elk.tf` | AWS OpenSearch Service | Docker: opensearchproject/opensearch |
| `12-s3.tf` | AWS S3 Bucket | Docker: MinIO |
| `8-redis.tf` | AWS ElastiCache Redis | Docker: redis:7 |
| `10-mq.tf` | Amazon MQ (RabbitMQ) | Docker: rabbitmq:3-management |
| `11-cloudront.tf` | CloudFront CDN | (not in local) |
| `ecs-web-ui-service.tf` | ECS Fargate Web UI | Docker: turath-rdm |
| `ecs-web-api-service.tf` | ECS Fargate Web API | Docker: turath-rdm |
| `ecs-celery-service.tf` | ECS Fargate Worker | Docker: turath-rdm (worker) |

---

## 🎯 Key Takeaways

1. **Both use the same services** (PostgreSQL, OpenSearch, S3, Redis, RabbitMQ)
2. **Local uses Docker containers** (free, fast, dev-friendly)
3. **Production uses AWS managed services** (reliable, scalable, $$)
4. **CI/CD builds the app images** (both environments use same app container)
5. **Terraform deploys to AWS** (creates managed services)
6. **docker-compose is for local dev only** (not used in production)

---

## 🔄 Why This Matters

**When you see `docker-compose.yml`:**
- It's **NOT** the production deployment
- It's a **local substitute** for AWS services
- It uses the **same APIs** so the app code works identically

**When you deploy with Terraform:**
- It creates **real AWS services**
- The app **connects the same way** (just different endpoints)
- You get **production-grade** reliability and scaling

---

## 📚 Summary

| Aspect | Local Dev | Production |
|--------|-----------|------------|
| **Where** | Your machine | AWS Cloud |
| **How** | docker-compose.yml | Terraform + ECS |
| **Database** | Docker container | AWS RDS |
| **Search** | Docker container | AWS OpenSearch |
| **Storage** | Docker MinIO | AWS S3 |
| **Cost** | $0 | ~$600/month |
| **Purpose** | Development & testing | Live production system |

Both environments run the **same InvenioRDM application**, just with different infrastructure backends!
