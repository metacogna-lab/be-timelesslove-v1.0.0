#!/bin/bash
# Apply Supabase migrations and create storage bucket
# This script combines all migrations and applies them via Supabase CLI

set -e

echo "=========================================="
echo "Supabase Setup: Migrations & Bucket"
echo "=========================================="
echo ""

PROJECT_REF="fjevxcnpgydosicdyugt"
MIGRATIONS_DIR="backend/db/migrations"
BUCKET_NAME="memories"

# Check if Supabase CLI is installed
if ! command -v supabase &> /dev/null; then
    echo "✗ Supabase CLI not found"
    echo "  Install: https://supabase.com/docs/guides/cli"
    exit 1
fi

echo "✓ Supabase CLI installed"
echo ""

# Check project link
echo "Checking project link..."
if ! supabase projects list 2>&1 | grep -q "$PROJECT_REF"; then
    echo "⚠️  Project not linked. Linking now..."
    supabase link --project-ref "$PROJECT_REF" 2>&1 || {
        echo "✗ Failed to link project"
        echo "  You may need to authenticate: supabase login"
        exit 1
    }
fi

echo "✓ Project linked: $PROJECT_REF"
echo ""

# Create combined migration file
echo "Preparing migrations..."
COMBINED_MIGRATION="/tmp/timelesslove_combined_migration.sql"

cat > "$COMBINED_MIGRATION" << 'EOF'
-- Combined Migration for Timeless Love
-- Generated automatically - DO NOT EDIT
-- Source: backend/db/migrations/001-004

EOF

# Combine all migration files
for migration in "$MIGRATIONS_DIR"/*.sql; do
    if [ -f "$migration" ]; then
        echo "-- Migration: $(basename $migration)" >> "$COMBINED_MIGRATION"
        echo "--" >> "$COMBINED_MIGRATION"
        cat "$migration" >> "$COMBINED_MIGRATION"
        echo "" >> "$COMBINED_MIGRATION"
        echo "-- End of $(basename $migration)" >> "$COMBINED_MIGRATION"
        echo "" >> "$COMBINED_MIGRATION"
    fi
done

echo "✓ Combined migration file created: $COMBINED_MIGRATION"
echo ""

# Apply migrations via Supabase Dashboard SQL Editor (manual step)
echo "=========================================="
echo "Migration Application"
echo "=========================================="
echo ""
echo "To apply migrations:"
echo "1. Open Supabase Dashboard: https://supabase.com/dashboard/project/$PROJECT_REF"
echo "2. Go to SQL Editor"
echo "3. Copy the contents of the combined migration file:"
echo "   cat $COMBINED_MIGRATION"
echo ""
echo "OR apply individual migrations in order:"
for migration in "$MIGRATIONS_DIR"/*.sql; do
    if [ -f "$migration" ]; then
        echo "   - $(basename $migration)"
    fi
done
echo ""

# Storage bucket creation
echo "=========================================="
echo "Storage Bucket Creation"
echo "=========================================="
echo ""
echo "To create the '$BUCKET_NAME' storage bucket:"
echo "1. Open Supabase Dashboard: https://supabase.com/dashboard/project/$PROJECT_REF"
echo "2. Go to Storage > Buckets"
echo "3. Click 'New bucket'"
echo "4. Name: $BUCKET_NAME"
echo "5. Public: No (private bucket)"
echo "6. File size limit: 50MB"
echo "7. Click 'Create bucket'"
echo ""

# Alternative: Try via Python script
echo "Attempting bucket creation via Python..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if command -v python3 &> /dev/null; then
    python3 "$SCRIPT_DIR/create_bucket.py" "$BUCKET_NAME" 2>&1 || {
        echo "⚠️  Python bucket creation failed - use manual method above"
    }
else
    echo "⚠️  Python3 not found - use manual method above"
fi

echo ""
echo "=========================================="
echo "Verification"
echo "=========================================="
echo ""
echo "After applying migrations and creating bucket, verify:"
echo ""
echo "1. Check tables exist:"
echo "   Run in SQL Editor:"
echo "   SELECT table_name FROM information_schema.tables"
echo "   WHERE table_schema = 'public' AND table_name IN ("
echo "     'family_units', 'user_profiles', 'invites', 'user_sessions',"
echo "     'memories', 'memory_media', 'memory_reactions', 'memory_comments',"
echo "     'analytics_events', 'analytics_metrics'"
echo "   );"
echo ""
echo "2. Check bucket exists:"
echo "   Go to Storage > Buckets and verify '$BUCKET_NAME' exists"
echo ""

echo "=========================================="
echo "Setup Complete"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Apply migrations (see instructions above)"
echo "2. Create storage bucket (see instructions above)"
echo "3. Verify setup using verification queries"
echo "4. Test backend connection"
echo ""

