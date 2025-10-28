#!/bin/bash
# Test the built Docker images locally with full stack

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

cd "$(dirname "$0")/.."

echo "${BLUE}🧪 Testing Full Stack with Built Images${NC}"
echo "========================================"
echo ""

# Check if test images exist
if ! docker images | grep -q "turath-rdm.*test"; then
    echo "${RED}❌ Test images not found!${NC}"
    echo "Run ./scripts/test-ci-builds.sh first to build test images"
    exit 1
fi

echo "${YELLOW}📦 Starting services...${NC}"
echo ""

# Start services
docker compose -f docker-compose.test.yml up -d

echo ""
echo "${YELLOW}⏳ Waiting for services to start (60 seconds)...${NC}"
sleep 60

echo ""
echo "${YELLOW}🔍 Checking service health...${NC}"
echo ""

# Check if services are running
echo "Services status:"
docker compose -f docker-compose.test.yml ps

echo ""
echo "${YELLOW}📊 Checking logs for errors...${NC}"
echo ""

# Check for obvious errors in web-ui logs
if docker compose -f docker-compose.test.yml logs web-ui | grep -i "error" | grep -v "stderr" | head -5; then
    echo "${YELLOW}⚠️  Found some errors in logs (check above)${NC}"
else
    echo "${GREEN}✅ No obvious errors in web-ui logs${NC}"
fi

echo ""
echo "${YELLOW}🌐 Testing website access...${NC}"
echo ""

# Test HTTP access
if curl -sSf http://127.0.0.1 > /dev/null 2>&1; then
    echo "${GREEN}✅ HTTP access works (http://127.0.0.1)${NC}"
else
    echo "${RED}❌ HTTP access failed${NC}"
fi

# Test HTTPS access (ignore cert issues)
if curl -sSfk https://127.0.0.1 > /dev/null 2>&1; then
    echo "${GREEN}✅ HTTPS access works (https://127.0.0.1)${NC}"
else
    echo "${RED}❌ HTTPS access failed${NC}"
fi

echo ""
echo "========================================"
echo "${GREEN}✅ Local deployment test complete!${NC}"
echo "========================================"
echo ""
echo "📝 Next steps:"
echo ""
echo "1. Open browser and visit:"
echo "   ${BLUE}https://127.0.0.1${NC}"
echo "   (Accept self-signed certificate warning)"
echo ""
echo "2. Test the application:"
echo "   - Browse records"
echo "   - Search functionality"
echo "   - Upload a book (if applicable)"
echo ""
echo "3. View logs:"
echo "   docker compose -f docker-compose.test.yml logs -f web-ui"
echo ""
echo "4. When done testing, stop services:"
echo "   docker compose -f docker-compose.test.yml down"
echo ""
echo "5. If everything works, proceed with GitHub Actions test!"
echo ""
