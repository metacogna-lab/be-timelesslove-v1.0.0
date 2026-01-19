#!/bin/bash
# Complete Supabase setup: Create bucket and provide migration instructions

set -e

PROJECT_REF="fjevxcnpgydosicdyugt"
BUCKET_NAME="memories"
MIGRATIONS_DIR="backend/db/migrations"

echo "=========================================="
echo "Supabase Complete Setup"
echo "=========================================="
echo ""

# Step 1: Create Storage Bucket
echo "=========================================="
echo "STEP 1: Create Storage Bucket"
echo "=========================================="
echo ""
echo "Creating bucket via Supabase Management API..."
echo ""

# Get API keys from environment or config
if [ -f "backend/.env" ]; then
    source <(grep -E '^SUPABASE_(URL|SERVICE_ROLE_KEY)=' backend/.env | sed 's/^/export /')
fi

if [ -z "$SUPABASE_URL" ] || [ -z "$SUPABASE_SERVICE_ROLE_KEY" ]; then
    echo "⚠️  SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY not found in backend/.env"
    echo ""
    echo "Manual bucket creation required:"
    echo "1. Go to: https://supabase.com/dashboard/project/$PROJECT_REF"
    echo "2. Navigate to: Storage > Buckets"
    echo "3. Click 'New bucket'"
    echo "4. Name: $BUCKET_NAME"
    echo "5. Public: No (private bucket)"
    echo "6. File size limit: 50MB"
    echo "7. Click 'Create bucket'"
    echo ""
else
    # Try to create bucket via API
    BUCKET_URL="${SUPABASE_URL}/storage/v1/bucket"
    
    # Check if bucket exists
    CHECK_RESPONSE=$(curl -s -w "\n%{http_code}" \
        -H "Authorization: Bearer $SUPABASE_SERVICE_ROLE_KEY" \
        -H "apikey: $SUPABASE_SERVICE_ROLE_KEY" \
        "$BUCKET_URL" 2>/dev/null || echo "ERROR")
    
    HTTP_CODE=$(echo "$CHECK_RESPONSE" | tail -n1)
    BODY=$(echo "$CHECK_RESPONSE" | sed '$d')
    
    if [ "$HTTP_CODE" = "200" ]; then
        if echo "$BODY" | grep -q "\"name\":\"$BUCKET_NAME\""; then
            echo "✓ Bucket '$BUCKET_NAME' already exists"
        else
            # Create bucket
            CREATE_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST \
                -H "Authorization: Bearer $SUPABASE_SERVICE_ROLE_KEY" \
                -H "apikey: $SUPABASE_SERVICE_ROLE_KEY" \
                -H "Content-Type: application/json" \
                -d "{\"name\":\"$BUCKET_NAME\",\"public\":false,\"file_size_limit\":52428800}" \
                "$BUCKET_URL" 2>/dev/null || echo "ERROR")
            
            CREATE_HTTP_CODE=$(echo "$CREATE_RESPONSE" | tail -n1)
            
            if [ "$CREATE_HTTP_CODE" = "200" ] || [ "$CREATE_HTTP_CODE" = "201" ]; then
                echo "✓ Successfully created bucket '$BUCKET_NAME'"
            elif [ "$CREATE_HTTP_CODE" = "409" ]; then
                echo "✓ Bucket '$BUCKET_NAME' already exists"
            else
                echo "⚠️  Failed to create bucket (HTTP $CREATE_HTTP_CODE)"
                echo "   Use manual method above"
            fi
        fi
    else
        echo "⚠️  Could not check/create bucket via API (HTTP $HTTP_CODE)"
        echo "   Use manual method above"
    fi
fi

echo ""

# Step 2: Apply Migrations
echo "=========================================="
echo "STEP 2: Apply Database Migrations"
echo "=========================================="
echo ""

if [ ! -d "$MIGRATIONS_DIR" ]; then
    echo "✗ Migrations directory not found: $MIGRATIONS_DIR"
    exit 1
fi

MIGRATION_FILES=$(ls -1 "$MIGRATIONS_DIR"/*.sql 2>/dev/null | grep -v "_combined" | sort)

if [ -z "$MIGRATION_FILES" ]; then
    echo "✗ No migration files found in $MIGRATIONS_DIR"
    exit 1
fi

echo "Found migration files:"
for file in $MIGRATION_FILES; do
    echo "  - $(basename $file)"
done
echo ""

# Create combined migration file
COMBINED_FILE="$MIGRATIONS_DIR/_combined_all_migrations.sql"
echo "-- Combined Migration for Timeless Love" > "$COMBINED_FILE"
echo "-- Generated automatically - Apply via Supabase SQL Editor" >> "$COMBINED_FILE"
echo "-- Source: Individual migration files in this directory" >> "$COMBINED_FILE"
echo "" >> "$COMBINED_FILE"

for file in $MIGRATION_FILES; do
    echo "-- ========================================" >> "$COMBINED_FILE"
    echo "-- Migration: $(basename $file)" >> "$COMBINED_FILE"
    echo "-- ========================================" >> "$COMBINED_FILE"
    echo "" >> "$COMBINED_FILE"
    cat "$file" >> "$COMBINED_FILE"
    echo "" >> "$COMBINED_FILE"
    echo "" >> "$COMBINED_FILE"
done

echo "✓ Combined migration file created: $COMBINED_FILE"
echo ""

echo "To apply migrations:"
echo "1. Open Supabase Dashboard: https://supabase.com/dashboard/project/$PROJECT_REF"
echo "2. Go to: SQL Editor"
echo "3. Choose one of the following:"
echo ""
echo "   Option A - Apply all at once (recommended):"
echo "   - Copy entire contents of: $COMBINED_FILE"
echo "   - Paste into SQL Editor"
echo "   - Click 'Run'"
echo ""
echo "   Option B - Apply individually:"
for file in $MIGRATION_FILES; do
    echo "   - $(basename $file)"
done
echo "     (Apply in order, one at a time)"
echo ""

# Step 3: Verification
echo "=========================================="
echo "STEP 3: Verification"
echo "=========================================="
echo ""

echo "After applying migrations, verify setup:"
echo ""
echo "1. Check tables exist (run in SQL Editor):"
echo ""
cat << 'SQL'
SELECT 
  table_name,
  CASE WHEN EXISTS (
    SELECT 1 FROM pg_tables 
    WHERE tablename = table_name AND schemaname = 'public'
  ) THEN '✓ EXISTS' ELSE '✗ MISSING' END AS status
FROM (VALUES 
  ('family_units'), ('user_profiles'), ('invites'), ('user_sessions'),
  ('memories'), ('memory_media'), ('memory_reactions'), ('memory_comments'),
  ('analytics_events'), ('analytics_metrics')
) AS t(table_name)
ORDER BY table_name;
SQL

echo ""
echo "2. Check storage bucket:"
echo "   - Go to: Storage > Buckets"
echo "   - Verify '$BUCKET_NAME' exists"
echo ""

echo "=========================================="
echo "Setup Instructions Complete"
echo "=========================================="
echo ""
echo "Summary:"
echo "  ✓ Combined migration file ready: $COMBINED_FILE"
echo "  ⚠️  Apply migrations manually via Supabase Dashboard"
echo "  ⚠️  Verify bucket creation manually if API method failed"
echo ""
echo "Next steps:"
echo "1. Apply migrations in Supabase SQL Editor"
echo "2. Verify bucket exists in Storage"
echo "3. Run verification queries"
echo "4. Test backend connection"
echo ""

