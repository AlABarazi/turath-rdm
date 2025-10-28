# Differences from Upstream AlABarazi/turath-rdm

This document highlights the key differences between this local development `turath-rdm` repository and the production deployment via `https://github.com/AlABarazi/turath-rdm` + Terraform infrastructure.

## 🏗️ Architecture Differences

### Key Difference: Local Docker vs AWS Managed Services

**The main difference is NOT missing services, but WHERE they run:**

- **Production (via Terraform)**: Uses AWS managed services
- **Local Development (this repo)**: Uses Docker containers + additional dev tools

### Local Development Additional Services

**Services that are Docker containers locally but AWS managed services in production:**

| Service | Local (Docker) | Production (AWS) | Port(s) |
|---------|----------------|------------------|---------|
| **PostgreSQL** | postgres:14.13 | AWS RDS | 5432 |
| **OpenSearch** | opensearchproject/opensearch:2.17.1 | AWS OpenSearch Service | 9200, 9600 |
| **S3 Storage** | MinIO (minio/minio) | AWS S3 | 9000, 9001 |
| **Redis** | redis:7 | AWS ElastiCache | 6379 |
| **RabbitMQ** | rabbitmq:3-management | Amazon MQ | 5672, 15672 |

**Additional development tools (not in production):**

| Service | Purpose | Port(s) |
|---------|---------|--------|
| **Cantaloupe** | IIIF Image API server | 8182 |
| **OpenSearch Dashboards** | Search index UI | 5601 |
| **pgAdmin** | PostgreSQL admin UI | 5050 |

### Service Configuration Differences

| Service | Production (Terraform) | Local Dev (Docker Compose) | Reason |
|---------|------------------------|----------------------------|--------|
| **Application** | ECS Fargate (3 services: ui, api, worker) | 3 containers (ui, api, worker) | Same structure |
| **Frontend** | Nginx on ECS + CloudFront CDN | Local Nginx container | Production uses CDN |
| **Storage** | AWS S3 | MinIO container | Local development without AWS costs |
| **Database** | AWS RDS PostgreSQL 15 | postgres:14.13 container | Managed vs self-managed |
| **Search** | AWS OpenSearch Service | opensearchproject/opensearch:2.17.1 | Managed vs self-managed |
| **Cache** | AWS ElastiCache Redis | redis:7 container | Managed vs self-managed |
| **Message Queue** | Amazon MQ (RabbitMQ) | rabbitmq:3-management | Managed vs self-managed |

## 📁 File Structure Differences

### Files in This Repo (Not in Upstream)

```
├── .github/
│   ├── CICD.md                          # ← This documentation
│   ├── CICD-QUICKSTART.md              # ← Quick reference
│   └── DIFFERENCES-FROM-UPSTREAM.md    # ← This file
├── cantaloupe-files/                    # ← IIIF source files (if using FilesystemSource)
├── cantaloupe-cache/                    # ← IIIF image cache
├── docker/
│   └── cantaloupe/
│       └── cantaloupe.properties        # ← Cantaloupe configuration
├── scripts/
│   ├── upload_book.py                   # ← Book upload automation
│   ├── records_crud.py                  # ← Record management CLI
│   └── update_manifest_ngrok.py         # ← Manifest URL updater (if using ngrok)
└── data/                                 # ← MinIO data volume
```

### Docker Compose Files

| File | Purpose | Upstream? |
|------|---------|-----------|
| `docker-compose.yml` | Backend services for local dev | ✅ Similar |
| `docker-compose.full.yml` | Full containerized stack | ✅ Similar |
| `docker-services.yml` | Service definitions | ✅ Similar |

**Key differences in docker-compose files:**

1. **docker-compose.yml** (Backend Services):
   ```yaml
   # THIS REPO: Includes Cantaloupe + MinIO
   services:
     cantaloupe:
       image: edirom/cantaloupe
       ports: ["8182:8182"]
       environment:
         - CANTALOUPE_SOURCE_STATIC=HttpSource
         - CANTALOUPE_HTTPSOURCE_BASICLOOKUPSTRATEGY_URL_PREFIX=https://host.docker.internal:5000/records/
     s3:
       image: minio/minio
       ports: ["9000:9000", "9001:9001"]
   
   # UPSTREAM: Standard InvenioRDM services only
   ```

2. **docker-compose.full.yml** (Full Stack):
   ```yaml
   # THIS REPO: Three app containers + additional services
   services:
     web-ui:        # UI application
     web-api:       # REST API application
     worker:        # Celery worker
     scheduler:     # Celery beat scheduler
     cantaloupe:    # IIIF server
     s3:            # MinIO
   
   # UPSTREAM: Similar structure, minus Cantaloupe/MinIO
   ```

## 🔧 Configuration Differences

### Environment Variables

**This Repo (docker-compose.full.yml):**
```yaml
environment:
  # MinIO configuration for local S3
  - AWS_ACCESS_KEY_ID=minioadmin
  - AWS_SECRET_ACCESS_KEY=minioadmin
  - AWS_DEFAULT_REGION=us-east-1
  - AWS_ENDPOINT_URL=http://s3:9000
  - AWS_S3_ADDRESSING_STYLE=path
  - AWS_S3_SIGNATURE_VERSION=s3v4
  - S3_BUCKET_NAME=turath-files
```

**Upstream:**
- Production-ready AWS S3 configuration
- No local MinIO references

### Cantaloupe Configuration

**HttpSource Mode (Current):**
```properties
# docker/cantaloupe/cantaloupe.properties
source.static = HttpSource
HttpSource.lookup_strategy = BasicLookupStrategy
HttpSource.BasicLookupStrategy.url_prefix = https://127.0.0.1:5000/records/
HttpSource.allow_insecure = true
```

**This configuration:**
- Fetches PDFs from InvenioRDM on demand
- No file duplication
- Single source of truth

## 🐳 CI/CD Workflow Differences

### Workflow File: `.github/workflows/docker-publish.yml`

| Aspect | Upstream | This Repo |
|--------|----------|-----------|
| **Images Built** | App + Frontend | App + Frontend (same) |
| **Tagging Strategy** | Branch, tag, SHA | Branch, tag, SHA (same) |
| **Caching** | GitHub Actions cache | GitHub Actions cache (same) |
| **Documentation** | Minimal | ✅ Extensive docs (CICD.md, QUICKSTART.md) |
| **Build Summary** | ❌ None | ✅ GitHub Actions summary with all services listed |

### Additional Documentation

This repo adds:
- `.github/CICD.md` - Comprehensive CI/CD documentation
- `.github/CICD-QUICKSTART.md` - Quick reference guide
- `.github/DIFFERENCES-FROM-UPSTREAM.md` - This file

## 📊 Deployment Differences

### Upstream (Production)
```bash
# Uses production AWS services
- ECS Fargate for containers
- RDS PostgreSQL for database
- OpenSearch Service for search
- S3 for file storage
- CloudFront for CDN
- GitHub Actions → AWS ECR → ECS
```

### This Repo (Development)
```bash
# Local development setup
- Docker Compose for all services
- Local PostgreSQL container
- Local OpenSearch container
- MinIO for S3 simulation
- Cantaloupe for IIIF images
- Direct development via invenio-cli
```

## 🔄 Workflow Comparison

### Upstream Development Workflow
```bash
1. Clone repo
2. invenio-cli install
3. invenio-cli services setup
4. invenio-cli run
5. Work on features
6. Push → GitHub Actions builds → AWS deployment
```

### This Repo Development Workflow
```bash
1. Clone repo
2. invenio-cli install
3. docker compose up -d         # ← Includes Cantaloupe + MinIO
4. invenio-cli run
5. Work on features
6. Test with Mirador viewer     # ← IIIF functionality
7. Test book upload scripts     # ← Custom scripts
8. Push → GitHub Actions builds images
9. Manual deployment (due to AWS SAML/MFA constraints)
```

## 🎯 Feature Differences

| Feature | Upstream | This Repo |
|---------|----------|-----------|
| **Basic InvenioRDM** | ✅ Yes | ✅ Yes |
| **IIIF Support** | ❓ Unknown | ✅ Yes (Cantaloupe) |
| **Mirador Viewer** | ❓ Unknown | ✅ Yes |
| **Book Upload Scripts** | ❌ No | ✅ Yes (scripts/) |
| **HOCR Full-text Search** | ❌ No | 🚧 In development |
| **Local S3 (MinIO)** | ❌ No | ✅ Yes |
| **Database Admin UI** | ❌ No | ✅ Yes (pgAdmin) |
| **Search UI** | ❌ No | ✅ Yes (OpenSearch Dashboards) |

## 🔐 AWS Integration Differences

### Upstream (Production AWS)
- Direct AWS S3 integration
- CloudFront CDN
- ECS deployment
- RDS managed database
- OpenSearch Service

### This Repo (Hybrid Approach)
- Local development: MinIO
- Production: AWS S3 (via Terraform)
- Local development: Docker containers
- Production: ECS Fargate
- **Constraint**: SAML/MFA prevents full automation
- **Solution**: Semi-automated deployment with manual AWS login

## 📈 Scalability Differences

| Aspect | Upstream | This Repo |
|--------|----------|-----------|
| **File Storage** | AWS S3 (scalable) | MinIO (local dev) → S3 (prod) |
| **Image Serving** | ❓ Unknown | Cantaloupe (can scale with ECS) |
| **Search** | Managed OpenSearch | Self-managed OpenSearch |
| **Database** | RDS (managed) | Docker (dev) → RDS (prod) |

## 🛠️ Maintenance Differences

### Upstream
- Focused on production deployment
- Minimal local development tools
- CI/CD for automated deployment

### This Repo
- Rich local development environment
- Extensive tooling and scripts
- Comprehensive documentation
- Semi-automated deployment (AWS constraints)
- Additional monitoring/admin interfaces

## 📝 Documentation Differences

| Type | Upstream | This Repo |
|------|----------|-----------|
| **README** | Basic | ✅ Comprehensive |
| **CI/CD Docs** | ❌ Minimal | ✅ Extensive (this file + 2 others) |
| **Architecture Docs** | ❌ Minimal | ✅ Detailed (docker-compose comments) |
| **Deployment Guide** | ❌ Minimal | ✅ Multiple guides |
| **Troubleshooting** | ❌ None | ✅ Included in docs |

## 🎓 Summary

**This repository extends the upstream with:**
1. ✅ Full IIIF support via Cantaloupe
2. ✅ Rich local development environment
3. ✅ Extensive documentation and tooling
4. ✅ Additional admin interfaces (pgAdmin, OpenSearch Dashboards)
5. ✅ Book upload and management scripts
6. ✅ Mirador viewer integration

**While maintaining compatibility for:**
- Core InvenioRDM functionality
- Docker-based deployment
- GitHub Actions CI/CD
- Production AWS deployment (with manual step)

## 🔄 Syncing from Upstream

If you want to pull updates from upstream:

```bash
# Add upstream remote (if not already added)
git remote add upstream https://github.com/AlABarazi/turath-rdm.git

# Fetch upstream changes
git fetch upstream

# Review changes
git log upstream/main

# Merge (carefully, to avoid overwriting custom features)
git merge upstream/main
# OR cherry-pick specific commits
git cherry-pick COMMIT_SHA
```

**⚠️ Warning**: Be careful when merging - preserve:
- Cantaloupe configuration
- MinIO setup
- Custom scripts
- Enhanced documentation
- Additional services in docker-compose files
