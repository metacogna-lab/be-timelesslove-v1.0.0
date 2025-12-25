#!/bin/bash
# Quick Supabase readiness check script

echo "=========================================="
echo "Supabase Readiness Check"
echo "=========================================="
echo ""

# Check if Supabase CLI is installed
if ! command -v supabase &> /dev/null; then
    echo "✗ Supabase CLI not found"
    echo "  Install: https://supabase.com/docs/guides/cli"
    exit 1
fi

echo "✓ Supabase CLI installed"
echo ""

# Check project list
echo "Checking projects..."
PROJECTS=$(supabase projects list 2>&1)

if echo "$PROJECTS" | grep -q "fjevxcnpgydosicdyugt"; then
    echo "✓ TimelessLove project found"
    echo "$PROJECTS" | grep "fjevxcnpgydosicdyugt"
else
    echo "✗ TimelessLove project not found in list"
    echo "$PROJECTS"
fi

echo ""
echo "=========================================="
echo "Manual Verification Required"
echo "=========================================="
echo ""
echo "Due to authentication requirements, please verify:"
echo ""
echo "1. Database Tables:"
echo "   - Run SQL in Supabase Dashboard SQL Editor"
echo "   - See: backend/docs/supabase/READINESS_CHECKLIST.md"
echo ""
echo "2. Storage Buckets:"
echo "   - Check Supabase Dashboard > Storage > Buckets"
echo "   - Verify 'memories' bucket exists"
echo ""
echo "3. Environment Variables:"
echo "   - Check backend/.env file exists"
echo "   - Verify SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_ROLE_KEY"
echo ""
echo "4. CORS Configuration:"
echo "   - Verify CORS_ORIGINS includes app.timelesslove.ai"
echo ""
echo "For detailed checklist, see:"
echo "  backend/docs/supabase/READINESS_CHECKLIST.md"
echo ""

