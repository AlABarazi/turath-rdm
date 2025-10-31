#!/bin/bash
# Test script to verify Docker builds work before pushing to GitHub Actions

set -e  # Exit on any error

echo "🧪 Testing CI/CD Docker Builds Locally"
echo "========================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Change to repo root
cd "$(dirname "$0")/.."

echo "📍 Working directory: $(pwd)"
echo ""

# Test 1: Main Application Build
echo "${YELLOW}📦 Test 1: Building main application image...${NC}"
echo "Command: docker build -t turath-rdm:test -f ./Dockerfile ."
echo ""

if docker build -t turath-rdm:test -f ./Dockerfile . ; then
    echo ""
    echo "${GREEN}✅ Main application build SUCCESSFUL!${NC}"
else
    echo ""
    echo "${RED}❌ Main application build FAILED!${NC}"
    echo "Check the error messages above."
    exit 1
fi

echo ""
echo "---"
echo ""

# Test 2: Frontend Build
echo "${YELLOW}🌐 Test 2: Building frontend (Nginx) image...${NC}"
echo "Command: docker build -t turath-rdm-frontend:test -f ./docker/nginx/Dockerfile ./docker/nginx/"
echo ""

if docker build -t turath-rdm-frontend:test -f ./docker/nginx/Dockerfile ./docker/nginx/ ; then
    echo ""
    echo "${GREEN}✅ Frontend build SUCCESSFUL!${NC}"
else
    echo ""
    echo "${RED}❌ Frontend build FAILED!${NC}"
    echo "Check the error messages above."
    exit 1
fi

echo ""
echo "========================================"
echo "${GREEN}🎉 ALL BUILDS SUCCESSFUL!${NC}"
echo "========================================"
echo ""

# Show image sizes
echo "📊 Built images:"
docker images | head -1
docker images | grep "turath-rdm.*test"

echo ""
echo "${GREEN}✅ GitHub Actions workflow should work!${NC}"
echo ""
echo "📝 Next steps:"
echo "1. Review the image sizes above (should be reasonable)"
echo "2. Test on a branch:"
echo "   git checkout -b test/ci-workflow"
echo "   git push origin test/ci-workflow"
echo "   Then create a Pull Request"
echo "3. If PR checks pass, merge to main"
echo ""
echo "Optional: Test run the images:"
echo "  docker run --rm turath-rdm:test --version"
echo "  docker run --rm -p 8080:80 turath-rdm-frontend:test"
