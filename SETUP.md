# Setup Guide

## 1. Gemini API Key (Brain)
1. Go to [Google AI Studio](https://aistudio.google.com/).
2. Keep it free (if applicable) or link billing.
3. Click "Get API Key".
4. Copy the key.
5. Paste it into `server/.env` as `GEMINI_API_KEY`.

## 2. Google Cloud Credentials (Voice)
> **Note**: This requires a Google Cloud account with billing enabled (though there is a free tier).
> **Alternative**: If this is too difficult, let me know, and I can switch the code to use the **Browser's Built-in Speech API** (free, no setup required).

### Steps to get the JSON file:
1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. **Create a New Project** (e.g., "Personal-Assistant").
3. **Enable APIs**:
   - Go to "APIs & Services" > "Library".
   - Search for **"Cloud Speech-to-Text API"** and click **Enable**.
   - Search for **"Cloud Text-to-Speech API"** and click **Enable**.
4. **Create Service Account**:
   - Go to "APIs & Services" > "Credentials".
   - Click "Create Credentials" > "Service Account".
   - Give it a name (e.g., "voice-bot").
   - Click "Create and Continue".
   - **Role**: Select "Project" > "Owner" (easiest for personal use) or specifically "Cloud Speech Client" and "Cloud Text-to-Speech Admin".
   - Click "Done".
5. **Download Key**:
   - Click on the newly created email address of the service account.
   - Go to the **"Keys"** tab.
   - Click "Add Key" > "Create new key".
   - Select **JSON** and click "Create".
   - A file will download automatically.
6. **Install**:
   - Rename the file to `credentials.json` (or something simple).
   - Move it to the `server/` folder (e.g., `server/credentials.json`).
   - Update `server/.env`:
     ```env
     GOOGLE_APPLICATION_CREDENTIALS=server/credentials.json
     ```
