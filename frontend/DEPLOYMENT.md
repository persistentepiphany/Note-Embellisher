# Frontend Deployment Guide

## Vercel Deployment Setup

### 1. Environment Variables Required

Set these environment variables in your Vercel project settings:

```
VITE_FIREBASE_API_KEY=your_api_key_here
VITE_FIREBASE_AUTH_DOMAIN=note-embellisher-2.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=note-embellisher-2
VITE_FIREBASE_STORAGE_BUCKET=note-embellisher-2.appspot.com
VITE_FIREBASE_MESSAGING_SENDER_ID=113873215178
VITE_FIREBASE_APP_ID=1:113873215178:web:6077e1a7f322f552201e33
VITE_FIREBASE_MEASUREMENT_ID=G-T0G3516BBB
```

### 2. Vercel Project Settings

- **Framework Preset**: Vite
- **Root Directory**: `frontend`
- **Build Command**: `./build.sh` (automatically validates env vars)
- **Output Directory**: `dist`
- **Node.js Version**: 18.x

### 3. Build Process

The build script will:
1. Validate all required environment variables
2. Run `npm run build` with Vite
3. Output to `dist/` directory

### 4. Routing

The app uses React Router. The `vercel.json` configuration:
- Serves static files from filesystem first
- Falls back to `index.html` for client-side routing
- Prevents rewriting of built assets

## Local Development

1. Copy `.env.example` to `.env.local`
2. Fill in your Firebase configuration
3. Run `npm install`
4. Run `npm run dev`

## Troubleshooting

### White Screen on Deployment
- Check Vercel build logs for environment variable validation errors
- Ensure all `VITE_*` variables are set in Vercel project settings
- Verify build completed successfully and `dist/` directory was created

### Build Failures
- Node.js version locked to 18.x for Rollup compatibility
- Check build logs for missing dependencies
- Validate Firebase configuration values