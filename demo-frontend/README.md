# Demo Frontend - Timeless Love

🚀 **Ready-to-run Next.js demo** for testing backend API integration and Supabase storage.

## ⚡ Quick Start (3 Commands)

```bash
cd demo-frontend
npm install
npm run dev
```

Open http://localhost:3000 🎉

## 📦 What's Included

### Features
- ✅ **Authentication** - Sign up/Login with Supabase
- ✅ **File Upload** - Multi-file upload with progress tracking
- ✅ **Memory Creation** - Rich metadata (title, description, location, tags)
- ✅ **Feed Display** - Beautiful gallery with signed URLs
- ✅ **Social Interactions** - Reactions (❤️👍😊🎉👏) and comments
- ✅ **TypeScript** - Fully typed API client and components
- ✅ **Error Handling** - User-friendly error messages
- ✅ **Responsive Design** - Mobile-first UI with Tailwind CSS

### Tech Stack
- **Next.js 14** - React framework
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **Supabase** - Auth + Storage
- **FastAPI** - Backend integration

## 🔧 Setup

### 1. Install Dependencies

```bash
npm install
```

### 2. Configure Environment

Copy `.env.example` to `.env.local` and fill in:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=https://fjevxcnpgydosicdyugt.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-supabase-anon-key
```

Get Supabase keys from: Dashboard > Settings > API

### 3. Start Backend

In a separate terminal:

```bash
cd ..  # Go to backend directory
uvicorn app.main:app --reload
```

### 4. Run Demo

```bash
npm run dev
```

Visit http://localhost:3000

## 🎯 Test Flow (5 minutes)

### Step 1: Authentication
1. Click "Sign Up"
2. Enter email and password
3. Check email for verification link
4. Click link to verify
5. Sign in with credentials

### Step 2: Upload Memory
1. Click "Upload Memory" tab
2. Fill form:
   - Title: "My First Memory"
   - Description: "Testing upload"
   - Tags: "test, demo"
3. Select 1-2 images
4. Click "Create Memory"
5. Watch progress bars
6. ✅ Success!

### Step 3: View Feed
1. Click "Feed" tab
2. See your memory
3. Images display in gallery
4. Click reaction emojis
5. View comments

## 📚 Documentation

- **[QUICK_START.md](./QUICK_START.md)** - Detailed 5-minute setup guide
- **[DEMO_SUMMARY.md](./DEMO_SUMMARY.md)** - Complete feature overview
- **[../FRONTEND_INTEGRATION.md](../FRONTEND_INTEGRATION.md)** - Full API reference

## 🐛 Troubleshooting

### "Module not found"
```bash
npm install
```

### "Authentication failed"
- Check `.env.local` has correct Supabase keys
- Verify email is confirmed

### "Upload failed"
- Ensure backend is running: `curl http://localhost:8000/health`
- Check Supabase "memories" bucket exists

### "Media not loading"
- Refresh feed to regenerate signed URLs
- Check browser console for errors

See [QUICK_START.md](./QUICK_START.md) for more troubleshooting.

## 🎨 Components

```
components/
├── AuthDemo.tsx           # Login/Signup UI
├── MemoryUploadDemo.tsx   # File upload with progress
└── FeedDemo.tsx           # Feed display with reactions
```

## 🔌 API Endpoints Used

| Endpoint | Purpose |
|----------|---------|
| `POST /api/v1/storage/upload-url` | Get signed upload URL |
| `POST /api/v1/memories` | Create memory record |
| `GET /api/v1/feed` | Get feed items |
| `GET /api/v1/storage/media/{id}/url` | Get media access URL |
| `POST /api/v1/feed/memories/{id}/reactions` | Add reaction |

## 🚀 Next Steps

1. **Customize** - Edit components to match your design
2. **Extend** - Add comments UI, search, filters
3. **Deploy** - Deploy to Vercel/Netlify
4. **Integrate** - Connect to your production backend

## 📖 Learn More

- [Next.js Documentation](https://nextjs.org/docs)
- [Supabase Docs](https://supabase.com/docs)
- [Tailwind CSS](https://tailwindcss.com/docs)
- [TypeScript Handbook](https://www.typescriptlang.org/docs)

## 💡 Tips

- **Hot Reload:** Edit components and see changes instantly
- **DevTools:** Use React DevTools for debugging
- **TypeScript:** Leverage autocomplete in VS Code
- **Console:** Check browser console for API logs

---

**Ready to test?** Start with [QUICK_START.md](./QUICK_START.md) 🚀
