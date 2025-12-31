# Deployment Guide

## Option 1: Streamlit Cloud (Recommended - Free & Easy)

Streamlit Cloud is the easiest way to deploy your app. It's free and made specifically for Streamlit apps.

### Steps:

1. **Go to Streamlit Cloud**
   - Visit: https://share.streamlit.io/
   - Sign in with your GitHub account

2. **Deploy Your App**
   - Click "New app"
   - Select your GitHub repository: `spy-volatility-regimes`
   - Select branch: `main` (or `master`)
   - Main file path: `streamlit_app.py`
   - App URL: Will be auto-generated (e.g., `your-app-name.streamlit.app`)

3. **Click "Deploy"**
   - Streamlit Cloud will automatically:
     - Install dependencies from `requirements.txt`
     - Deploy your app
     - Give you a public URL

4. **Your App is Live!**
   - Your app will be accessible at: `https://your-app-name.streamlit.app`
   - Any push to GitHub will automatically redeploy the app

### Benefits:
- ✅ Free forever
- ✅ Automatic deployments on git push
- ✅ Public URL (shareable)
- ✅ No server management
- ✅ HTTPS enabled by default

---

## Option 2: Railway (Alternative)

1. Go to https://railway.app
2. Sign in with GitHub
3. Click "New Project" → "Deploy from GitHub repo"
4. Select your repository
5. Railway will auto-detect it's a Streamlit app
6. Add environment variables if needed
7. Deploy!

---

## Option 3: Render (Alternative)

1. Go to https://render.com
2. Sign in with GitHub
3. Click "New +" → "Web Service"
4. Connect your GitHub repository
5. Settings:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `streamlit run streamlit_app.py --server.port=$PORT --server.address=0.0.0.0`
6. Deploy!

---

## Option 4: Heroku (More Complex)

1. Install Heroku CLI
2. Create `Procfile`:
   ```
   web: streamlit run streamlit_app.py --server.port=$PORT --server.address=0.0.0.0
   ```
3. Deploy using Heroku CLI

---

## Recommended: Streamlit Cloud

For Streamlit apps, **Streamlit Cloud is the best choice** because:
- It's made specifically for Streamlit
- Zero configuration needed
- Free tier is generous
- Automatic deployments
- Easy to use

Just connect your GitHub repo and you're done!

