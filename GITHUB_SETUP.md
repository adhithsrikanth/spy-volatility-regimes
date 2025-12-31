# GitHub Setup Instructions

## Step 1: Create Initial Commit

```bash
cd /Users/adhith/spy_volatility_regimes
git commit -m "Initial commit: Volatility Regime Analyzer"
```

## Step 2: Create GitHub Repository

1. Go to [GitHub](https://github.com) and sign in
2. Click the **+** icon in the top right → **New repository**
3. Name it: `spy-volatility-regimes` (or any name you prefer)
4. **Do NOT** initialize with README, .gitignore, or license (we already have these)
5. Click **Create repository**

## Step 3: Connect Local Repository to GitHub

After creating the repository, GitHub will show you commands. Use these:

```bash
# Add the remote repository (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/spy-volatility-regimes.git

# Rename branch to 'main' (GitHub's default)
git branch -M main

# Push your code
git push -u origin main
```

## Alternative: Using SSH (if you have SSH keys set up)

```bash
git remote add origin git@github.com:YOUR_USERNAME/spy-volatility-regimes.git
git branch -M main
git push -u origin main
```

## Step 4: Verify

Go to your GitHub repository page and verify all files are there:
- `streamlit_app.py`
- `volatility_regimes.py`
- `requirements.txt`
- `README.md`
- `.gitignore`

## Future Updates

To push future changes:

```bash
git add .
git commit -m "Your commit message"
git push
```

## Optional: Add Repository Description

On GitHub, you can add a description like:
"Interactive Streamlit dashboard for visualizing market volatility regimes with S&P 500 stocks"

