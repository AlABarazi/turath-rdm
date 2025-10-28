# CI/CD Documentation for Turath RDM

## Overview

This repository uses GitHub Actions for continuous integration and deployment. The workflow is adapted from the upstream `https://github.com/AlABarazi/turath-rdm` repository but includes additional considerations for local development infrastructure.

## Workflow Files

### `.github/workflows/docker-publish.yml`

**Trigger Events:**
- Push to `main` branch
- Version tags (`v*`)
- Pull requests to `main` branch

**Built Images:**

1. **Main Application Image** (`ghcr.io/{owner}/turath-rdm:latest`)
   - InvenioRDM core + Turath customizations
   - Built from root `Dockerfile`
   - Includes Python dependencies, extensions, and site customizations

2. **Frontend Image** (`ghcr.io/{owner}/turath-rdm-frontend:latest`)
   - Nginx reverse proxy
   - Built from `docker/nginx/Dockerfile`
   - SSL/TLS configuration for production

**Build Features:**
- ✅ Layer caching via GitHub Actions cache
- ✅ Multi-tag support (branch, semver, SHA)
- ✅ Pull request validation (build only, no push)
- ✅ Automated metadata extraction
- ✅ Build summary in GitHub Actions UI

## Architecture Differences from Upstream

### Services Built by CI/CD

| Service | Image | Built in CI/CD? | Source |
|---------|-------|-----------------|--------|
| **Main App** | `turath-rdm:latest` | ✅ Yes | Root `Dockerfile` |
| **Frontend** | `turath-rdm-frontend:latest` | ✅ Yes | `docker/nginx/Dockerfile` |
| **Cantaloupe** | `edirom/cantaloupe` | ❌ No | Pre-built (IIIF image server) |
| **MinIO** | `minio/minio` | ❌ No | Pre-built (S3-compatible storage) |
| **PostgreSQL** | `postgres:14.13` | ❌ No | Pre-built (database) |
| **OpenSearch** | `opensearchproject/opensearch:2.17.1` | ❌ No | Pre-built (search engine) |
| **Redis** | `redis:7` | ❌ No | Pre-built (cache) |
| **RabbitMQ** | `rabbitmq:3-management` | ❌ No | Pre-built (message queue) |

### Additional Services for Local Development

For local development, this repository uses Docker containers for all backend services. The production deployment (via Terraform) uses AWS managed services instead:

**Local Development (Docker Containers):**

1. **Cantaloupe IIIF Server** (`cantaloupe`)
   - Provides IIIF Image API for book page images
   - Configured with HttpSource to fetch PDFs from InvenioRDM
   - Port: 8182
   - See: `docker-services.yml:122-141`

2. **MinIO S3** (`s3`)
   - Local S3-compatible object storage (replaces AWS S3 for dev)
   - Used for file uploads and IIIF source files
   - Ports: 9000 (API), 9001 (Console)
   - See: `docker-services.yml:104-120`

3. **PostgreSQL** (`db`)
   - Local database container (production uses AWS RDS)
   - Port: 5432
   - See: `docker-services.yml:43-51`

4. **OpenSearch** (`search`)
   - Local search engine container (production uses AWS OpenSearch Service)
   - Ports: 9200, 9600
   - See: `docker-services.yml:68-91`

5. **Redis** (`cache`)
   - Local cache container (production uses AWS ElastiCache)
   - Port: 6379
   - See: `docker-services.yml:37-42`

6. **RabbitMQ** (`mq`)
   - Local message queue container (production uses Amazon MQ)
   - Ports: 5672, 15672
   - See: `docker-services.yml:62-67`

7. **OpenSearch Dashboards** (`opensearch-dashboards`)
   - Web UI for exploring OpenSearch indexes
   - Port: 5601
   - See: `docker-services.yml:92-103`

8. **pgAdmin** (`pgadmin`)
   - PostgreSQL database administration tool
   - Port: 5050
   - See: `docker-services.yml:52-61`

**Production Deployment (AWS Managed Services via Terraform):**
- PostgreSQL → **AWS RDS** (`inveniordm-terraform/5-rds.tf`)
- OpenSearch → **AWS OpenSearch Service** (`inveniordm-terraform/9-elk.tf`)
- S3 → **AWS S3** (`inveniordm-terraform/12-s3.tf`)
- Redis → **AWS ElastiCache** (`inveniordm-terraform/8-redis.tf`)
- RabbitMQ → **Amazon MQ** (`inveniordm-terraform/10-mq.tf`)
- CDN → **CloudFront** (`inveniordm-terraform/11-cloudront.tf`)

## Docker Compose Configurations

### `docker-compose.yml` (Development)
- Starts backend services only
- Used with `invenio-cli run` for local development
- Application runs outside Docker (in virtual environment)
- Includes all additional services (Cantaloupe, MinIO, etc.)

### `docker-compose.full.yml` (Full Stack)
- Containerizes everything including the application
- Used with `invenio-cli containers start`
- Production-like environment
- Includes frontend Nginx proxy
- Three application containers: `web-ui`, `web-api`, `worker`

### `docker-services.yml` (Service Definitions)
- Base definitions for all services
- Extended by other compose files
- Contains environment variables and configurations

## Deployment Workflow

### Development
```bash
# Start backend services
docker compose up -d

# Run application locally
invenio-cli run
```

### Production-like Testing
```bash
# Build and start everything
invenio-cli containers start --lock --build --setup
```

### Production Deployment (AWS)
Based on memories and Terraform setup:

1. **Local Build & Push** (after CI/CD builds images):
   ```bash
   # Pull from GHCR
   docker pull ghcr.io/{owner}/turath-rdm:main
   docker pull ghcr.io/{owner}/turath-rdm-frontend:main
   
   # Tag for ECR (if needed)
   docker tag ghcr.io/{owner}/turath-rdm:main {aws-ecr-url}/turath-rdm:latest
   docker push {aws-ecr-url}/turath-rdm:latest
   ```

2. **Deploy to ECS** (manual due to SAML/MFA constraints):
   ```bash
   # Authenticate with AWS
   aws-login
   
   # Deploy via Terraform or deployment script
   ./scripts/deploy.sh
   ```

## Environment Variables for CI/CD

The workflow uses these secrets/variables:

| Variable | Source | Purpose |
|----------|--------|---------|
| `GITHUB_TOKEN` | Auto-provided | Authenticate to GHCR |
| `github.actor` | Auto-provided | GitHub username |
| `github.repository` | Auto-provided | Repository name |

**No additional secrets needed** - the workflow uses GitHub's built-in authentication.

## Image Tagging Strategy

Built images get multiple tags:

- `main` - Latest from main branch
- `pr-{number}` - Pull request builds (not pushed)
- `v1.2.3` - Semantic version tags
- `v1.2` - Major.minor version
- `main-{sha}` - Commit SHA (for rollbacks)

## Future Enhancements

### Potential Additional Workflows

1. **Testing Workflow** (`test.yml`)
   ```yaml
   - Run Python tests (pytest)
   - Run JavaScript tests
   - Code linting (flake8, eslint)
   - Security scanning (trivy, snyk)
   ```

2. **Integration Testing** (`integration.yml`)
   ```yaml
   - Spin up full stack with docker-compose.full.yml
   - Run API tests
   - Test IIIF manifest generation
   - Test search functionality
   ```

3. **Deployment Workflow** (`deploy.yml`)
   ```yaml
   - Deploy to staging on merge to develop
   - Deploy to production on version tag
   - (Blocked by AWS SAML/MFA - needs manual step)
   ```

## Troubleshooting

### Build Failures

**Issue**: Dockerfile build fails
- Check `Dockerfile` syntax
- Verify base image availability
- Check Pipfile.lock is committed

**Issue**: Frontend build fails
- Check `docker/nginx/Dockerfile`
- Verify nginx configuration files exist
- Check SSL certificate paths

### Image Push Failures

**Issue**: Permission denied to GHCR
- Ensure repository settings allow package publishing
- Verify GitHub Actions permissions in Settings > Actions

**Issue**: Image too large
- Use `.dockerignore` to exclude unnecessary files
- Use multi-stage builds
- Clean up cache layers

### Local Testing

Test the workflow locally using `act`:
```bash
# Install act
brew install act

# Run workflow locally
act -j build
```

## References

- Upstream repository: https://github.com/turath-project/turath-inveniordm
- InvenioRDM docs: https://inveniordm.docs.cern.ch
- Docker Buildx: https://docs.docker.com/buildx/
- GitHub Actions: https://docs.github.com/en/actions
- GHCR: https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry
