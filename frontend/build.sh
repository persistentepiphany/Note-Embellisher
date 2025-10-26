#!/bin/bash

# Build script with environment validation
echo "🔍 Validating environment variables..."

# Check for required Firebase variables
required_vars=("VITE_FIREBASE_API_KEY" "VITE_FIREBASE_AUTH_DOMAIN" "VITE_FIREBASE_PROJECT_ID" "VITE_FIREBASE_STORAGE_BUCKET" "VITE_FIREBASE_MESSAGING_SENDER_ID" "VITE_FIREBASE_APP_ID")

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "❌ Missing required environment variable: $var"
        echo "Please set all required VITE_* variables in your Vercel project settings."
        exit 1
    fi
done

echo "✅ All required environment variables are set"
echo "🏗️  Starting build process..."

# Run the build
npm run build

if [ $? -eq 0 ]; then
    echo "✅ Build completed successfully"
else
    echo "❌ Build failed"
    exit 1
fi