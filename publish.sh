#!/bin/bash

echo "🌿 Syncing notes from Obsidian vault..."
cp -r "/Users/prashanthns/Library/Mobile Documents/iCloud~md~obsidian/Documents/notes-remote/." ~/Sites/notes-daktre/content/

echo "📦 Staging changes..."
cd ~/Sites/notes-daktre
git add .

echo "💬 Committing..."
TIMESTAMP=$(date "+%Y-%m-%d %H:%M")
git commit -m "Publish notes – $TIMESTAMP"

echo "🚀 Pushing to GitHub..."
git push origin v4

echo "✅ Done! Site will update in ~2 minutes at notes.daktre.com"
