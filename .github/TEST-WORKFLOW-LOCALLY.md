# Testing GitHub Actions Workflow Locally

## 🎯 Three Ways to Test Without Pushing to Main

### Option 1: Manual Docker Build Test (Fastest - Recommended)

Test the exact build commands that GitHub Actions will run:

```bash
cd /Users/alaaalbarazi/Projects/Turath/turath-rdm

# Test main application build
echo "Testing main application build..."
docker build -t turath-rdm:test -f ./Dockerfile .

# If successful, you'll see:
# Successfully built abc123def456
# Successfully tagged turath-rdm:test

# Test frontend build
echo "Testing frontend build..."
docker build -t turath-rdm-frontend:test -f ./docker/nginx/Dockerfile ./docker/nginx/

# If successful, you'll see:
# Successfully built xyz789abc123
# Successfully tagged turath-rdm-frontend:test

# Verify images were created
docker images | grep turath-rdm

# Test run the images (optional)
docker run --rm turath-rdm:test --version
docker run --rm -p 8080:80 turath-rdm-frontend:test  # Test nginx
```

**What to look for:**
- ✅ Both builds complete without errors
- ✅ Images are created successfully
- ✅ No missing files or dependencies

**If builds succeed** → GitHub Actions will work! ✅

---

### Option 2: Test on a Different Branch

Create a test branch to trigger the workflow without affecting main:

```bash
# Create test branch
git checkout -b test/ci-workflow

# Commit the workflow
git add .github/workflows/docker-publish.yml
git commit -m "Test CI/CD workflow"

# Push to test branch
git push origin test/ci-workflow

# Open a Pull Request to main (via GitHub UI)
# The workflow will run but NOT push images (just validate builds)
```

**What happens:**
- ✅ Workflow runs on the PR
- ✅ Builds both images
- ❌ Does NOT push to GHCR (only validates)
- You can see logs in GitHub Actions tab

**If the PR check passes** → Safe to merge to main! ✅

---

### Option 3: Local GitHub Actions Runner (Most Accurate)

Use `act` tool to run GitHub Actions locally:

```bash
# Install act (GitHub Actions local runner)
brew install act

# Test the workflow locally
cd /Users/alaaalbarazi/Projects/Turath/turath-rdm
act -j build

# Or test just the build step without pushing
act -j build --secret GITHUB_TOKEN=fake_token

# If you encounter issues, run with verbose logging
act -j build -v
```

**What `act` does:**
- Runs GitHub Actions in Docker containers
- Simulates the exact GitHub Actions environment
- Shows you the same logs you'd see in GitHub

**Limitations:**
- Requires Docker
- May need GitHub token for some actions
- Can be slower than manual Docker build

---

## 🔍 Verification Checklist

Before pushing to main, verify:

### Main Application Build
```bash
# Build should succeed
docker build -t turath-rdm:test -f ./Dockerfile .

# Check for these files in build context
ls -la Pipfile Pipfile.lock site/

# Verify size (should be reasonable, not huge)
docker images turath-rdm:test
# Should be ~1-2GB, not 10GB+
```

### Frontend Build
```bash
# Build should succeed
docker build -t turath-rdm-frontend:test -f ./docker/nginx/Dockerfile ./docker/nginx/

# Check for required files
ls -la docker/nginx/nginx.conf
ls -la docker/nginx/conf.d/
ls -la docker/nginx/test.key
ls -la docker/nginx/test.crt

# Verify size (should be small)
docker images turath-rdm-frontend:test
# Should be ~200-300MB (nginx base + config)
```

---

## 🚨 Common Issues and Fixes

### Issue 1: Build Context Too Large
```bash
# Symptom: Build takes forever, "Sending build context..."
# Fix: Add to .dockerignore

cat >> .dockerignore << 'EOF'
.venv/
data/
logs/
cantaloupe-cache/
cantaloupe-files/
.git/
*.pyc
__pycache__/
EOF
```

### Issue 2: Missing Files
```bash
# Symptom: COPY failed: file not found
# Fix: Verify files exist

# For main app
ls -la Pipfile Pipfile.lock site/

# For frontend
ls -la docker/nginx/nginx.conf
ls -la docker/nginx/conf.d/
```

### Issue 3: Base Image Pull Fails
```bash
# Symptom: Error pulling registry.cern.ch/inveniosoftware/almalinux:1
# Fix: Check internet connection, or use alternative registry

# Test if base image is accessible
docker pull registry.cern.ch/inveniosoftware/almalinux:1
```

### Issue 4: Pipenv Lock Fails
```bash
# Symptom: pipenv lock --clear fails in Dockerfile
# Fix: Update Pipfile.lock locally first

pipenv lock
git add Pipfile.lock
git commit -m "Update Pipfile.lock"
```

---

## 📊 Expected Build Times

| Build | Local Machine | GitHub Actions |
|-------|---------------|----------------|
| Main App (first time) | 10-20 min | 15-25 min |
| Main App (cached) | 2-5 min | 3-7 min |
| Frontend (first time) | 30-60 sec | 1-2 min |
| Frontend (cached) | 10-20 sec | 30-60 sec |

---

## ✅ When Everything Works

You'll see:

```bash
# Main app build
[+] Building 123.4s (15/15) FINISHED
 => [internal] load build definition from Dockerfile
 => [internal] load .dockerignore
 => [internal] load metadata for registry.cern.ch/...
 ...
 => => writing image sha256:abc123...
 => => naming to docker.io/library/turath-rdm:test

# Frontend build
[+] Building 12.3s (8/8) FINISHED
 => [internal] load build definition from Dockerfile
 => [internal] load .dockerignore
 => [internal] load metadata for docker.io/library/nginx:latest
 ...
 => => writing image sha256:xyz789...
 => => naming to docker.io/library/turath-rdm-frontend:test
```

**If you see this** → GitHub Actions will work! 🎉

---

## 🎓 Recommended Testing Flow

```bash
# 1. Quick local test (5 minutes)
docker build -t turath-rdm:test -f ./Dockerfile .
docker build -t turath-rdm-frontend:test -f ./docker/nginx/Dockerfile ./docker/nginx/

# 2. If successful → Test on branch (10 minutes)
git checkout -b test/ci-workflow
git push origin test/ci-workflow
# Create PR and watch GitHub Actions

# 3. If PR passes → Merge to main (automatic deployment)
git checkout main
git merge test/ci-workflow
git push origin main
```

---

## 📞 Quick Test Script

Save this as `test-workflow.sh`:

```bash
#!/bin/bash
set -e

echo "🧪 Testing Docker builds locally..."
echo ""

echo "📦 Building main application..."
docker build -t turath-rdm:test -f ./Dockerfile . && echo "✅ Main app build successful!" || exit 1

echo ""
echo "🌐 Building frontend..."
docker build -t turath-rdm-frontend:test -f ./docker/nginx/Dockerfile ./docker/nginx/ && echo "✅ Frontend build successful!" || exit 1

echo ""
echo "🎉 All builds successful! GitHub Actions should work."
echo ""
echo "📊 Image sizes:"
docker images | grep turath-rdm

echo ""
echo "Next steps:"
echo "1. Create test branch: git checkout -b test/ci-workflow"
echo "2. Push and create PR to validate in GitHub Actions"
echo "3. If PR passes, merge to main"
```

Make it executable:
```bash
chmod +x test-workflow.sh
./test-workflow.sh
```

---

## 🎯 Summary

| Method | Speed | Accuracy | When to Use |
|--------|-------|----------|-------------|
| **Manual Docker Build** | ⚡ Fast (5 min) | 95% | Quick validation |
| **PR Branch** | 🐢 Medium (15 min) | 100% | Before merging |
| **act Tool** | 🐢 Slow (20 min) | 99% | Complex workflows |

**Recommendation**: Start with manual Docker build, then test via PR branch before merging to main.
