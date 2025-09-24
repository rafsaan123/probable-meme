#!/bin/bash
# Production EAS Build Script for BTEB Results App (Android Focus)

echo "🚀 Starting Production EAS Build for BTEB Results App (Android)"
echo "=============================================================="

# Install dependencies
echo "📦 Installing production dependencies..."
npm install

# Clean any existing builds
echo "🧹 Cleaning existing builds..."
npx expo install --fix

# Prebuild for Android only (iOS has CocoaPods issues)
echo "🔨 Prebuilding for Android platform..."
npx expo prebuild --platform android --clean

# Build for Android only
echo "🏗️ Building for Android (Production)..."
echo ""

# Start the build process for Android
eas build --platform android --profile production

echo ""
echo "✅ Android build process completed!"
echo "📱 Check your EAS dashboard for build status and download links"
echo "🔗 EAS Dashboard: https://expo.dev/accounts/mdrafsan0038/projects/bteb-result"
echo ""
echo "📝 Note: iOS build skipped due to CocoaPods configuration issues"
echo "   To build iOS later, ensure Xcode and CocoaPods are properly configured"
