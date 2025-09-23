# Vercel Configuration for BTEB Results API

## Environment Variables to Set in Vercel:
```
SUPABASE_PRIMARY_URL=https://hddphaneexloretrisiy.supabase.co
SUPABASE_PRIMARY_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhkZHBoYW5lZXhsb3JldHJpc2l5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTg2MTEzNjksImV4cCI6MjA3NDE4NzM2OX0.eMyOCUDI-iqcGY_tJUbAMw41sPnDDXfHbdMJNfcwP-w

SUPABASE_SECONDARY_URL=https://ncjleyktzilulflbjfdg.supabase.co
SUPABASE_SECONDARY_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5jamxleWt0emlsdWxmbGJqZmRnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTg2MjI2OTUsImV4cCI6MjA3NDE5ODY5NX0.ScbXuVjULWWyCJt4IuKhUhSunkRg0H0XVVysR7756b0

SUPABASE_TERTIARY_URL=https://your-tertiary-project.supabase.co
SUPABASE_TERTIARY_KEY=your-tertiary-key

SUPABASE_BACKUP1_URL=https://your-backup1-project.supabase.co
SUPABASE_BACKUP1_KEY=your-backup1-key

SUPABASE_BACKUP2_URL=https://your-backup2-project.supabase.co
SUPABASE_BACKUP2_KEY=your-backup2-key
```

## Vercel Setup Steps:
1. Go to https://vercel.com
2. Sign up with GitHub
3. Click "New Project" → "Import Git Repository"
4. Select your repository: `rafsaan123/probable-meme`
5. Set Root Directory to: `bteb_results`
6. Add all environment variables above
7. Deploy!

## Benefits of Vercel:
- ✅ Serverless functions (perfect for APIs)
- ✅ Global CDN for fast responses
- ✅ No proxy issues (unlike Render)
- ✅ Automatic HTTPS
- ✅ Easy GitHub integration
- ✅ Generous free tier
- ✅ Excellent Python/Flask support

## After Deployment:
- Your API will be available at: `https://your-project-name.vercel.app`
- Update mobile app API URL to the Vercel domain
- Test all endpoints to ensure everything works
