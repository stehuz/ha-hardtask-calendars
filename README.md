🎯 Hardtask Calendars for Home Assistant
A unified Home Assistant integration that tracks available courses and training sessions from both Hardtask and Hardtask Rangers. It automatically monitors free slots and provides detailed course information (instructors, location, price) directly in your dashboard.

✨ Features
Two-in-One: Monitors both Hardtask.cz and HardtaskRangers.cz.

Automatic Filtering: Easily exclude specific locations (like "Příbram") via your configuration.

Rich Attributes: Each sensor provides a full list of available courses with direct registration links.

Push Notifications: Includes blueprints to alert your phone the moment a new slot opens up.

🚀 Installation
1. Via HACS (Recommended)
Open HACS in your Home Assistant.

Click the three dots in the top right and select Custom repositories.

Paste: https://github.com/stehuz/ha-hardtask

Select Integration as the category and click Add.

Click Download, then Restart Home Assistant.

2. Manual Installation
Copy the custom_components/hardtask/ folder into your Home Assistant config/custom_components/ directory.

Restart Home Assistant.

⚙️ Configuration
Add the following to your configuration.yaml file. You can optionally use exclude_locations to filter out training sites you don't want to see.

```YAML
sensor:
  - platform: hardtask
    exclude_locations:
      - "Příbram"
      - "Ostrava"
```
Note: The filter is case-insensitive and handles accents (diacritics) automatically. If a location contains your excluded word, it will be hidden.

📱 Blueprints (Notifications)
Get a notification on your phone the second a course becomes available. Import these directly into Home Assistant by pasting these URLs into the "Import Blueprint" section:

Hardtask Courses (Main Site):
https://github.com/stehuz/ha-hardtask/blob/main/blueprints/notify_courses.yaml

Hardtask Rangers:
https://github.com/stehuz/ha-hardtask/blob/main/blueprints/notify_rangers.yaml

📊 Dashboard Display
Use a Markdown Card to display your courses in a beautiful table:

1. Markdown Card: Hardtask Courses (Main Site)
```YAML
type: markdown
title: "🛡️ Hardtask: Main Courses"
content: >
  | Date & Time | Course | Instructor | Location | Price | Slots | Link |

  | :--- | :--- | :--- | :--- | :--- | :---: | :---: |

  {% for course in state_attr('sensor.hardtask_courses', 'courses') -%}

  | {{ course.date_time }} | {{ course.name }} | {{ course.instructor }} | {{
  course.location }} | {{ course.price }} | **{{ course.free_slots }}** |
  [Register]({{ course.url }}) |

  {% endfor %}
```
2. Markdown Card: Hardtask Rangers (Trainings)
```YAML
type: markdown
title: "🎯 Hardtask: Rangers Trainings"
content: >
  | Date & Time | Training | Instructor | Location | Price | Slots | Link |

  | :--- | :--- | :--- | :--- | :--- | :---: | :---: |

  {% for course in state_attr('sensor.hardtask_rangers', 'courses') -%}

  | {{ course.date_time }} | {{ course.name }} | {{ course.instructor }} | {{
  course.location }} | {{ course.price }} | **{{ course.free_slots }}** |
  [Register]({{ course.url }}) |

  {% endfor %}
```

🛠️ Troubleshooting
If the sensors show 0 or Unknown:

Check your home-assistant.log for any errors related to hardtask.

Ensure you have beautifulsoup4 installed (it should be handled automatically).

Open an issue on this repository if the website layout has changed.
