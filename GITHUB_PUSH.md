# Quick GitHub Push Guide

## 🚀 Fastest Way (All-in-One Script)

Simply run this command in PowerShell from `f:\Assignment`:

```powershell
.\setup_github.ps1
```

This script will:
1. ✅ Create 22 incremental commits
2. ✅ Guide you to create GitHub repo
3. ✅ Configure Git remote
4. ✅ Push code to GitHub with your token

---

## 📋 Step-by-Step Manual Method

If the automated script doesn't work, follow these manual steps:

### 1. Create Commits
```powershell
.\create_commits.ps1
```

### 2. Create GitHub Repository
- Go to https://github.com/new
- Repository name: `contract-intelligence-api`
- Keep it **PUBLIC**
- **Do NOT** check "Initialize with README"
- Click "Create repository"

### 3. Configure Git
```powershell
# Set your identity (if not already set)
git config user.name "Your Name"
git config user.email "your.email@example.com"

# Add remote (replace YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/contract-intelligence-api.git

# Set branch to main
git branch -M main
```

### 4. Push with Token

**Option A: Embed token in URL (Quick)**
```powershell
git remote set-url origin https://YOUR_GITHUB_TOKEN@github.com/YOUR_USERNAME/contract-intelligence-api.git
git push -u origin main

# Change back to regular URL (removes token from config)
git remote set-url origin https://github.com/YOUR_USERNAME/contract-intelligence-api.git
```

**Option B: Use Credential Helper**
```powershell
git push -u origin main
# Username: YOUR_GITHUB_USERNAME
# Password: YOUR_GITHUB_PERSONAL_ACCESS_TOKEN
```

---

## ✅ Verify Success

After pushing, check:

1. **View on GitHub:**
   ```
   https://github.com/YOUR_USERNAME/contract-intelligence-api
   ```

2. **Check commit history:**
   - Should see 22+ commits
   - Each with descriptive messages
   - Shows incremental development

3. **Verify all files are there:**
   - ✅ README.md, DESIGN.md
   - ✅ api/, contract_intelligence/
   - ✅ docker-compose.yml, Dockerfile
   - ✅ prompts/, eval/, tests/

---

## 🔧 Troubleshooting

**Issue**: "fatal: remote origin already exists"
```powershell
git remote remove origin
git remote add origin https://github.com/YOUR_USERNAME/contract-intelligence-api.git
```

**Issue**: "Authentication failed"
- Make sure you're using the token as password, not your GitHub password
- Use your Personal Access Token from GitHub settings

**Issue**: "refusing to merge unrelated histories"
- This means you initialized the GitHub repo with README
- Delete the repo and create a new one **without** initializing

**Issue**: Token not working
- Check token hasn't expired
- Make sure you have correct permissions on the token

---

## 🎯 What You'll Have

After successful push:
- ✅ GitHub repository with all code
- ✅ 22 commits showing incremental work
- ✅ Professional commit messages
- ✅ Complete documentation
- ✅ Ready for assignment submission

---

## 📦 Repository Should Include

```
✅ Source code (api/, contract_intelligence/)
✅ Tests (tests/)
✅ Docker setup (Dockerfile, docker-compose.yml)
✅ README with API examples
✅ DESIGN.md with architecture
✅ prompts/ with LLM rationale
✅ eval/ with Q&A dataset and script
✅ All documentation
```

---

## 🔗 Submit This

Once pushed, submit:
1. **GitHub URL**: `https://github.com/YOUR_USERNAME/contract-intelligence-api`
2. **Loom Video**: (record following LOOM_SCRIPT.md)

Done! 🎉
