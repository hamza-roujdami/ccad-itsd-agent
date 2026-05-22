# Teams App — IT Service Desk

Personal tab that embeds the Clinical ITSM Agent web UI inside Microsoft Teams.

## How it works

```
Teams → Personal Tab (iframe) → Your React UI (Container Apps, UAE North)
                                  └── FastAPI /chat → Agent → ManageEngine MCP
```

All data stays in UAE. No Azure Bot Service required.

## Setup

### 1. Replace placeholders in manifest.json

| Placeholder | Value | Example |
|---|---|---|
| `{{APP_ID}}` | Generate a new GUID | `a1b2c3d4-e5f6-7890-abcd-ef1234567890` |
| `{{BASE_URL}}` | Your deployed React UI URL | `https://ca-frontend-xxxx.azurecontainerapps.io` |
| `{{DOMAIN}}` | Domain without https:// | `ca-frontend-xxxx.azurecontainerapps.io` |
| `{{ENTRA_CLIENT_ID}}` | Your Entra ID app registration client ID | `12345678-abcd-...` |

### 2. Add icons

Create two PNG icons in this folder:
- `color.png` — 192x192 full color app icon
- `outline.png` — 32x32 transparent outline icon

### 3. Package the app

```bash
cd teams-app
zip -r itsd-agent.zip manifest.json color.png outline.png
```

### 4. Upload to Teams

**For testing:**
1. Open Teams → Apps → Manage your apps → Upload a custom app
2. Select `itsd-agent.zip`
3. The "IT Support" tab appears in your sidebar

**For org-wide deployment:**
1. Go to Teams Admin Center → Manage apps → Upload new app
2. Upload `itsd-agent.zip`
3. Set app policies to make it available to all users

### 5. Teams SSO (optional)

To auto-authenticate users via their Teams login, add this to your React app:

```javascript
import * as microsoftTeams from "@microsoft/teams-js";

microsoftTeams.app.initialize().then(() => {
  microsoftTeams.authentication.getAuthToken().then((token) => {
    // Send token to your FastAPI backend as Bearer header
    // Backend validates with Entra ID → knows who the user is
  });
});
```

Install: `npm install @microsoft/teams-js`

## Sovereignty

All message data flows:
- Teams → iframe loads your UAE-hosted web UI
- Web UI → FastAPI agent in UAE North Container Apps
- Agent → ManageEngine MCP via UAE APIM
- **No data leaves UAE**

Azure Bot Service (Global) is NOT used.
