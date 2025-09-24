#!/bin/bash
# Production EAS Build Preparation Script
# Moves unnecessary files to /Users/md.rafsan/MM and prepares for production build

echo "🚀 Preparing BTEB Results App for Production EAS Build"
echo "======================================================"

# Create backup directory
BACKUP_DIR="/Users/md.rafsan/MM"
mkdir -p "$BACKUP_DIR"

echo "📁 Created backup directory: $BACKUP_DIR"

# Move unnecessary files and directories
echo "🧹 Moving unnecessary files to backup directory..."

# Move development and testing files
mv bteb_results "$BACKUP_DIR/" 2>/dev/null || echo "bteb_results already moved or doesn't exist"
mv supabase "$BACKUP_DIR/" 2>/dev/null || echo "supabase already moved or doesn't exist"
mv .idea "$BACKUP_DIR/" 2>/dev/null || echo ".idea already moved or doesn't exist"

# Move documentation files
mv APP_SIZE_OPTIMIZATION.md "$BACKUP_DIR/" 2>/dev/null || echo "APP_SIZE_OPTIMIZATION.md already moved or doesn't exist"
mv EAS_BUILD_GUIDE.md "$BACKUP_DIR/" 2>/dev/null || echo "EAS_BUILD_GUIDE.md already moved or doesn't exist"
mv IMPROVEMENTS_SUMMARY.md "$BACKUP_DIR/" 2>/dev/null || echo "IMPROVEMENTS_SUMMARY.md already moved or doesn't exist"

# Move development scripts
mv scripts "$BACKUP_DIR/" 2>/dev/null || echo "scripts already moved or doesn't exist"

# Move test files
find . -name "*.test.*" -exec mv {} "$BACKUP_DIR/" \; 2>/dev/null || echo "No test files found"
find . -name "*test*" -type f -exec mv {} "$BACKUP_DIR/" \; 2>/dev/null || echo "No test files found"

# Move development configuration files
mv eslint.config.js "$BACKUP_DIR/" 2>/dev/null || echo "eslint.config.js already moved or doesn't exist"
mv tsconfig.json "$BACKUP_DIR/" 2>/dev/null || echo "tsconfig.json already moved or doesn't exist"

# Move unused components (keep only essential ones)
mkdir -p "$BACKUP_DIR/components"
mv components/ui "$BACKUP_DIR/components/" 2>/dev/null || echo "components/ui already moved or doesn't exist"

# Move unused hooks
mkdir -p "$BACKUP_DIR/hooks"
mv hooks/use-color-scheme.ts "$BACKUP_DIR/hooks/" 2>/dev/null || echo "use-color-scheme.ts already moved or doesn't exist"
mv hooks/use-color-scheme.web.ts "$BACKUP_DIR/hooks/" 2>/dev/null || echo "use-color-scheme.web.ts already moved or doesn't exist"
mv hooks/use-theme-color.ts "$BACKUP_DIR/hooks/" 2>/dev/null || echo "use-theme-color.ts already moved or doesn't exist"

# Move unused constants
mv constants "$BACKUP_DIR/" 2>/dev/null || echo "constants already moved or doesn't exist"

# Clean up node_modules (will be reinstalled)
echo "🗑️ Cleaning node_modules..."
rm -rf node_modules
rm -f package-lock.json

# Clean up any build artifacts
echo "🗑️ Cleaning build artifacts..."
rm -rf .expo
rm -rf dist
rm -rf build
rm -rf android/app/build
rm -rf ios/build

# Clean up logs and temporary files
echo "🗑️ Cleaning logs and temporary files..."
find . -name "*.log" -delete 2>/dev/null || echo "No log files found"
find . -name "*.tmp" -delete 2>/dev/null || echo "No tmp files found"
find . -name ".DS_Store" -delete 2>/dev/null || echo "No DS_Store files found"

# Clean up git files (optional - uncomment if needed)
# echo "🗑️ Cleaning git files..."
# rm -rf .git
# rm -f .gitignore

echo ""
echo "✅ Production Cleanup Complete!"
echo "==============================="
echo "📁 Backup directory: $BACKUP_DIR"
echo "📦 Moved files:"
echo "   - bteb_results/ (API server)"
echo "   - supabase/ (database files)"
echo "   - .idea/ (IDE files)"
echo "   - Documentation files"
echo "   - Development scripts"
echo "   - Test files"
echo "   - Unused components and hooks"
echo "   - Constants directory"
echo ""
echo "🎯 Ready for EAS Build!"
echo "   Run: eas build --platform all"
echo ""
echo "📝 To restore development files:"
echo "   mv $BACKUP_DIR/* ."
