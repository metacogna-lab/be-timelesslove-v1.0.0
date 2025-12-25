# Quick Start Guide - Demo Frontend

Get the demo frontend running in 5 minutes!

## Prerequisites

- Node.js 18+ installed
- Backend server running (`uvicorn app.main:app --reload`)
- Supabase project configured

## Step 1: Install Dependencies

```bash
cd demo-frontend
npm install
```

## Step 2: Configure Environment

```bash
# Copy the example env file
cp .env.example .env.local

# Edit .env.local with your values
```

Required environment variables:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=https://fjevxcnpgydosicdyugt.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
```

**Get your Supabase keys:**
1. Go to https://app.supabase.com
2. Select your project
3. Settings > API
4. Copy "Project URL" and "anon public" key

## Step 3: Start Backend

In a separate terminal:

```bash
cd ..  # Go to backend directory
uvicorn app.main:app --reload
```

Backend should be running at http://localhost:8000

## Step 4: Start Frontend

```bash
npm run dev
```

Frontend will start at http://localhost:3000

## Step 5: Test the Flow

### 5.1 Register/Login
1. Open http://localhost:3000
2. Click "Sign Up"
3. Enter email and password
4. Check your email for verification link (Supabase will send it)
5. Click verification link
6. Go back and sign in

### 5.2 Upload a Memory
1. Click "Upload Memory" tab
2. Fill in:
   - Title: "My Test Memory"
   - Description: "Testing the upload flow"
   - Location: "Home"
   - Tags: "test, demo"
3. Click "Choose Files" and select 1-2 images
4. Click "Create Memory"
5. Watch the progress bar
6. Success! Memory is uploaded

### 5.3 View Feed
1. Click "Feed" tab
2. See your uploaded memory
3. Click reaction emojis (❤️, 👍, etc.)
4. View comments section

## Troubleshooting

### "Failed to get upload URL"

**Problem:** Backend isn't running or not accessible

**Solution:**
```bash
# Check backend is running
curl http://localhost:8000/health

# Should return: {"status": "healthy"}
```

### "Authentication failed"

**Problem:** Supabase configuration issue

**Solution:**
1. Verify `.env.local` has correct Supabase URL and anon key
2. Check Supabase project is active
3. Try signing up with a different email

### "Upload failed: 403 Forbidden"

**Problem:** Storage bucket permissions

**Solution:**
1. Go to Supabase Dashboard > Storage
2. Ensure "memories" bucket exists
3. Check RLS policies allow authenticated users to upload

### "Media not displaying"

**Problem:** Signed URLs not generated or expired

**Solution:**
1. Refresh the feed
2. Check browser console for errors
3. Verify backend storage service is configured correctly

## API Testing with cURL

Test backend endpoints directly:

```bash
# 1. Get auth token (after signing up/in)
TOKEN="your-supabase-access-token"

# 2. Test health endpoint
curl http://localhost:8000/health

# 3. Test authenticated endpoint
curl http://localhost:8000/api/v1/memories \
  -H "Authorization: Bearer $TOKEN"

# 4. Test upload URL generation
curl -X POST http://localhost:8000/api/v1/storage/upload-url \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "memory_id": "550e8400-e29b-41d4-a716-446655440000",
    "file_name": "test.jpg",
    "mime_type": "image/jpeg"
  }'
```

## Development Tips

### Hot Reload

Both frontend and backend support hot reload:
- Frontend: Edit files in `components/` or `app/` - auto-refreshes
- Backend: Edit files in `app/` - uvicorn auto-reloads

### Debugging

**Frontend:**
- Open browser DevTools (F12)
- Console tab shows API requests/responses
- Network tab shows all HTTP traffic

**Backend:**
- Check terminal running uvicorn
- Logs show all incoming requests
- Add `print()` statements for debugging

### Reset Demo

To start fresh:

```bash
# 1. Delete Supabase data
# Go to Supabase Dashboard > Table Editor > memories table > Delete all rows

# 2. Delete Supabase storage
# Go to Supabase Dashboard > Storage > memories bucket > Delete all files

# 3. Sign up with new account
```

## What's Next?

Now that the demo is working:

1. **Customize UI** - Edit components in `components/`
2. **Add Features** - Implement comments, search, filters
3. **Production Deploy** - Deploy to Vercel/Netlify
4. **Backend Enhance** - Add more endpoints, webhooks
5. **Real-time Updates** - Add Supabase realtime subscriptions

## Useful Commands

```bash
# Install dependencies
npm install

# Start dev server
npm run dev

# Build for production
npm run build

# Start production server
npm start

# Lint code
npm run lint

# Clear Next.js cache
rm -rf .next
```

## File Structure

```
demo-frontend/
├── app/
│   ├── page.tsx           # Main page (tabs)
│   ├── layout.tsx         # App layout
│   └── globals.css        # Global styles
├── components/
│   ├── AuthDemo.tsx       # Login/signup
│   ├── MemoryUploadDemo.tsx  # File upload
│   └── FeedDemo.tsx       # Feed display
├── lib/
│   ├── api-client.ts      # API utilities
│   └── types.ts           # TypeScript types
├── .env.local             # Environment config
├── package.json           # Dependencies
└── README.md              # Documentation
```

## Support

- **Backend API Docs**: http://localhost:8000/docs
- **Supabase Dashboard**: https://app.supabase.com
- **Next.js Docs**: https://nextjs.org/docs
- **Issue?** Check `FRONTEND_INTEGRATION.md` for detailed API reference

---

**Ready to build!** 🚀

You now have a working demo that integrates:
- ✅ Supabase authentication
- ✅ File uploads to Supabase Storage
- ✅ Backend API calls
- ✅ Feed display with reactions
- ✅ Error handling
- ✅ TypeScript types
