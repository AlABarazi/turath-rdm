# CI/CD Quick Start Guide

**Upstream Repository**: https://github.com/AlABarazi/turath-rdm  
**Infrastructure (Terraform)**: https://github.com/turath-project/inveniordm-terraform

## 🚀 Common Operations

### 1. Trigger a Build

**Automatic triggers:**
```bash
# Push to main branch (builds and pushes images)
git push origin main

# Create a version tag (builds and pushes with version tags)
git tag v1.0.0
git push origin v1.0.0

# Open a PR (builds but doesn't push - validation only)
git checkout -b feature/my-feature
git push origin feature/my-feature
# Then create PR via GitHub UI
```

### 2. Use Built Images Locally

**Pull from GitHub Container Registry:**
```bash
# Login to GHCR (use GitHub Personal Access Token)
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin

# Pull latest main branch image
docker pull ghcr.io/OWNER/turath-rdm:main
docker pull ghcr.io/OWNER/turath-rdm-frontend:main

# Use in docker-compose.full.yml
# (update image: turath-inveniordm:latest to ghcr.io/OWNER/turath-rdm:main)
```

### 3. Check Build Status

**Via GitHub UI:**
1. Go to repository → Actions tab
2. Click on latest workflow run
3. View logs for each step

**Via CLI (using GitHub CLI):**
```bash
# Install gh CLI
brew install gh

# List recent workflow runs
gh run list --workflow=docker-publish.yml

# View specific run
gh run view RUN_ID

# Watch live
gh run watch
```

### 4. Local Build Testing

**Build images locally (same as CI/CD):**
```bash
# Build main application
docker build -t turath-rdm:local \
  --build-arg ENVIRONMENT=PRODUCTION \
  -f Dockerfile .

# Build frontend
docker build -t turath-rdm-frontend:local \
  -f docker/nginx/Dockerfile \
  docker/nginx/

# Test the images
docker compose -f docker-compose.full.yml up -d
```

### 5. Debug Build Failures

**Common issues and fixes:**

**Issue: Pipfile.lock out of sync**
```bash
# Regenerate lock file
pipenv lock
git add Pipfile.lock
git commit -m "Update Pipfile.lock"
```

**Issue: Docker context too large**
```bash
# Check .dockerignore
cat .dockerignore

# Add large directories
echo ".venv/" >> .dockerignore
echo "data/" >> .dockerignore
echo "logs/" >> .dockerignore
```

**Issue: Build arg not passed correctly**
```bash
# Check Dockerfile ARG declarations match workflow
grep "ARG" Dockerfile
```

### 6. Update Workflow

**Modify workflow file:**
```bash
# Edit workflow
vi .github/workflows/docker-publish.yml

# Test locally with act
act -j build

# Commit changes
git add .github/workflows/docker-publish.yml
git commit -m "Update CI/CD workflow"
git push
```

### 7. Enable Branch Protection

**Require CI/CD to pass before merging:**

1. Go to Settings → Branches
2. Add rule for `main` branch
3. Enable: "Require status checks to pass"
4. Select: `build` from docker-publish workflow
5. Enable: "Require branches to be up to date"

### 8. View Built Images

**Check GitHub Packages:**
```bash
# Via GitHub UI
# Repository → Packages (right sidebar)

# Via Docker
docker search ghcr.io/OWNER/turath-rdm

# List tags
curl -H "Authorization: Bearer $GITHUB_TOKEN" \
  https://ghcr.io/v2/OWNER/turath-rdm/tags/list
```

## 📋 Cheat Sheet

### Environment Variables in CI/CD

| Variable | Set Where | Example Value |
|----------|-----------|---------------|
| `REGISTRY` | Workflow env | `ghcr.io` |
| `IMAGE_NAME` | Workflow env | `turath-project/turath-rdm` |
| `GITHUB_TOKEN` | Auto-provided | (secret) |
| `github.actor` | Auto-provided | `username` |

### Image Tags Generated

| Event | Tags Created |
|-------|-------------|
| Push to main | `main`, `main-abc1234` |
| Push tag v1.2.3 | `v1.2.3`, `v1.2`, `1.2.3`, `1.2` |
| PR #123 | `pr-123` (not pushed) |

### Docker Commands

```bash
# Build
docker build -t IMAGE:TAG -f Dockerfile .

# Run
docker run -p 5000:5000 IMAGE:TAG

# Push
docker push IMAGE:TAG

# Pull
docker pull IMAGE:TAG

# Inspect
docker inspect IMAGE:TAG
docker history IMAGE:TAG
```

### Compose Commands

```bash
# Start services
docker compose up -d

# Stop services
docker compose down

# Rebuild services
docker compose up -d --build

# View logs
docker compose logs -f SERVICE_NAME

# Full stack
docker compose -f docker-compose.full.yml up -d
```

## 🔧 Advanced Operations

### Create Personal Access Token (PAT)

**For pulling private images:**
```bash
# 1. GitHub → Settings → Developer settings → Personal access tokens
# 2. Generate new token (classic)
# 3. Scopes: read:packages, write:packages
# 4. Use token to login
echo $PAT | docker login ghcr.io -u USERNAME --password-stdin
```

### Multi-Platform Builds

**Build for ARM and x86:**
```bash
# Setup buildx
docker buildx create --use

# Build for multiple platforms
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t IMAGE:TAG \
  --push \
  .
```

### Cache Management

**Clear GitHub Actions cache:**
```bash
# Via GitHub CLI
gh cache list
gh cache delete CACHE_ID

# Via GitHub UI
# Settings → Actions → Caches
```

### Rollback to Previous Image

**Revert to older version:**
```bash
# List available tags
docker pull ghcr.io/OWNER/turath-rdm:main-abc1234

# Update docker-compose.full.yml
# image: ghcr.io/OWNER/turath-rdm:main-abc1234

# Restart
docker compose -f docker-compose.full.yml up -d
```

## 📚 Further Reading

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Build Documentation](https://docs.docker.com/engine/reference/commandline/build/)
- [GHCR Documentation](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)
- [InvenioRDM Deployment](https://inveniordm.docs.cern.ch/deployment/)
