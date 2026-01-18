# Deployment Guide for Render

This guide will help you deploy your Personal AI Assistant to Render.com for free.

## Prerequisites
1.  A GitHub account.
2.  A [Render.com](https://render.com) account (you can sign up with GitHub).
3.  Your code pushed to a GitHub repository.

## Step 1: Prepare Your Environment Variables
You will need the following secrets ready to paste into Render:
-   `GEMINI_API_KEY`: Your Google Gemini API key.
-   `GOOGLE_APPLICATION_CREDENTIALS`: (See Step 4 below)

## Step 2: Create a Blueprint Instance on Render
1.  Go to the [Render Dashboard](https://dashboard.render.com/).
2.  Click **"New +"** and select **"Blueprint"**.
3.  Connect your GitHub repository.
4.  Render will detect the `render.yaml` file in your repository.
5.  Click **"Apply"**.

## Step 3: Configure the Services
Render will create three services for you:
1.  **db**: A PostgreSQL database (Free).
2.  **api**: The FastAPI backend (Free - spins down on idle).
3.  **web**: The React frontend (Free).

Wait for the initial build. The **api** service might fail initially because it's missing the Google Credentials. This is normal.

## Step 4: Add Google Cloud Credentials
Since we cannot upload the `credentials.json` file directly to Render easily, we will paste its content as an environment variable.

1.  Open your local `server/credentials.json` file.
2.  Copy the **entire content** (it's a JSON string).
3.  Go to the **Render Dashboard**.
4.  Click on the **"api"** service (the Web Service).
5.  Go to **"Environment"**.
6.  Add a new environment variable:
    -   **Key**: `GOOGLE_CREDENTIALS_JSON`
    -   **Value**: Paste the JSON content you copied.
7.  **Save Changes**. Render will automatically redeploy the API.

> **Note**: I have updated `server/auth.py` and `server/voice_handler.py` to check for `GOOGLE_CREDENTIALS_JSON` if the file is missing.

## Step 5: Verification
1.  Once all services are green (Live), click the URL of the **web** service.
2.  Try logging in and sending a message.
3.  The database is now persistent!
