#!/bin/bash

# DialogGuard GitHub Upload Script
# Created for anonymous paper submission

echo "🛡️ DialogGuard GitHub Upload"
echo "=============================="
echo ""

# Navigate to project directory
cd "$(dirname "$0")"

# Initialize git if needed
if [ ! -d ".git" ]; then
    echo "📦 Initializing git repository..."
    git init
    
    echo "🔧 Configuring anonymous git settings..."
    git config user.name "Anonymous Researcher"
    git config user.email "anonymous@example.com"
else
    echo "✅ Git repository already initialized"
fi

# Show current status
echo ""
echo "📋 Current status:"
git status --short

# Add all files
echo ""
echo "📥 Adding files to git..."
git add .

# Create initial commit
echo ""
echo "💾 Creating commit..."
git commit -m "Initial commit: DialogGuard multi-agent evaluation system

- Multi-dimensional risk assessment (DB, MM, PVR, Toxicity)
- Four evaluation mechanisms (Single, Dual, Debate, Voting)
- Interactive web interface with Live Chat mode
- Complete evaluation pipeline with real-time visualization"

# Set main branch
echo ""
echo "🌿 Setting main branch..."
git branch -M main

# Show instructions
echo ""
echo "✅ Local repository is ready!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📤 Next: Push to GitHub"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "After creating the repository on GitHub, run:"
echo ""
echo "  git remote add origin https://github.com/lhannnn/dialogguard-web.git"
echo "  git push -u origin main"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

