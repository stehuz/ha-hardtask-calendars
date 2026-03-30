# 🎯 Hardtask Calendars for Home Assistant

This custom component scrapes the [Hardtask](https://www.hardtask.cz/) and [Hardtask Rangers](https://www.hardtaskrangers.cz/) websites to track available training courses and free slots directly in Home Assistant.

## ⚙️ Installation via HACS

1. Open HACS in your Home Assistant.
2. Click the three dots in the top right corner and select **Custom repositories**.
3. Paste the URL of this repository and select **Integration** as the category.
4. Click **Download**, then restart Home Assistant.
5. Add the following to your `configuration.yaml`:

```yaml
sensor:
  - platform: hardtask_courses
  - platform: hardtask_rangers
```

6. Restart Home Assistant one last time.

## 📱 Blueprint Notifications
Want to get a push notification to your phone the second a new free slot opens up? Import the official blueprints directly into your Home Assistant:

**For Hardtask Courses (Main Site):**
1. Go to Settings > Automations & Scenes > Blueprints.
2. Click **Import Blueprint** and paste this URL:
`https://raw.githubusercontent.com/stehuz/ha-hardtask-calendars/main/blueprints/hardtask_courses_notifier.yaml`

**For Hardtask Rangers:**
1. Go to Settings > Automations & Scenes > Blueprints.
2. Click **Import Blueprint** and paste this URL:
`https://raw.githubusercontent.com/stehuz/ha-hardtask-calendars/main/blueprints/hardtask_rangers_notifier.yaml`

## 📊 Dashboard Markdown
Add this to a Markdown Card on your dashboard to see your available courses beautifully formatted:
*(Paste your Lovelace Markdown code here!)*
