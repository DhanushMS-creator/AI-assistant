# Beginner's Guide to Deployment Breakdown

This guide assumes you are starting from scratch on your computer and want to get your AI Assistant running on the internet for free using Render.com.

---

## Phase 1: Preparation (Before you start)

### 1. Get your Accounts Ready
*   **GitHub**: Go to [github.com](https://github.com/) and sign up if you haven't. This is where your code will live.
*   **Render**: Go to [render.com](https://render.com/). Click "Get Started" and **sign up using your GitHub account**. This makes connecting them much easier.

### 2. Gather your Secrets
You need two keys from your project. Keep them ready in a text file or just know where they are:
1.  **Gemini API Key**: Should be in your `server/.env` file.
2.  **Google Cloud Credentials**: Should be in `server/credentials.json`. Open this file and copy **everything** inside it (the curly braces `{ ... }` and all text between them).

---

## Phase 2: Put your Code on GitHub

If your code is already on GitHub, skip to Phase 3. If not, follow these steps in your VSC terminal:

1.  **Initialize Git**:
    ```bash
    git init
    ```

2.  **Add your files**:
    ```bash
    git add .
    ```

3.  **Commit your changes**:
    ```bash
    git commit -m "Initial commit for deployment"
    ```

4.  **Create a Repository on GitHub**:
    *   Go to GitHub.com.
    *   Click the **+** icon in the top right -> **New repository**.
    *   Name it `personal-ai-assistant`.
    *   **Important**: Select **Private** if you want to keep your keys secret (safer), or **Public** (but ensure `.env` and `credentials.json` are NOT uploaded - our `.gitignore` handles this, but be careful).
    *   Click **Create repository**.

5.  **Connect and Push**:
    *   Copy the commands GitHub shows you under "…or push an existing repository from the command line". They look like this:
    ```bash
    git remote add origin https://github.com/YOUR_USERNAME/personal-ai-assistant.git
    git branch -M main
    git push -u origin main
    ```
    *   Paste and run them in your terminal.

---

## Phase 3: Deployment on Render

Now we tell Render to take your code from GitHub and run it.

1.  **Go to Dashboard**: Log in to [dashboard.render.com](https://dashboard.render.com/).
2.  **Create Blueprint**:
    *   Click the blue **"New +"** button.
    *   Select **"Blueprint"**.
    *   You should see your repository `personal-ai-assistant` in the list. Click **Connect**.
    *   Give it a name (e.g., `my-ai-assistant`).
    *   Click **Apply**.

3.  **Wait for Initial Setup**:
    *   Render will read the `render.yaml` file I created for you.
    *   It will automatically set up a **Database**, a **Web Service** (backend), and a **Static Site** (frontend).
    *   **Don't panic** if you see "Failed" for the API service initially. We haven't added the secrets yet!

---

## Phase 4: Add Your Secrets (Crucial Step)

The server needs your private keys to talk to Google.

1.  **Find the API Service**:
    *   On your Render Dashboard, click on the **Service** named **api** (it corresponds to the python backend).

2.  **Go to Environment**:
    *   Click the **"Environment"** tab on the left sidebar.

3.  **Add Gemini Key**:
    *   Checking the list, you might see `DATABASE_URL` already there. Leave it alone.
    *   Click **"Add Environment Variable"**.
    *   **Key**: `GEMINI_API_KEY`
    *   **Value**: Paste your actual Gemini API key (starting with `AIza...`).

4.  **Add Google Cloud Credentials**:
    *   Click **"Add Environment Variable"** again.
    *   **Key**: `GOOGLE_CREDENTIALS_JSON`
    *   **Value**: Paste the **entire content** of `credentials.json` you copied in Phase 1.

5.  **Save**:
    *   Click **"Save Changes"**.

---

## Phase 5: Live!

Render will automatically restart the server.

1.  Wait for the logs to show "Application startup complete".
2.  Go to your Dashboard, click on the **web** service (the frontend).
3.  Click the link (e.g., `https://my-ai-assistant.onrender.com`).
4.  **Done!** Your app is now live on the internet.

### Troubleshooting
*   **Database Error**: Make sure the `render.yaml` created the database. You should see a "PostgreSQL" service in your dashboard.
*   **Voice not working**: Check if you copied the `credentials.json` fastidiously into the environment variable. It must be valid JSON.
