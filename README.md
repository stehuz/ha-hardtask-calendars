# 🛡️ Hardtask Calendars for Home Assistant

A custom Home Assistant integration that monitors upcoming firearms training courses and events from [Hardtask.cz](https://www.hardtask.cz/) and [HardtaskRangers.cz](https://www.hardtaskrangers.cz/). 

Built for modern Home Assistant standards, this integration uses a clean UI setup (Config Flow) and completely replaces legacy YAML configurations.

## ✨ Features
* **Dual Monitoring:** Creates separate sensors for Main Courses and Rangers Trainings.
* **UI Configuration:** Set up entirely via the Home Assistant UI.
* **Location Filtering:** Exclude specific locations (e.g., Příbram, Ostrava) directly in the setup wizard.
* **Rich Attributes:** Stores full course details (date, instructor, location, price, available slots, and registration links) in the sensor attributes.
* **HACS Compatible:** Fully structured for installation via the Home Assistant Community Store.

## 📦 Installation

### HACS (Recommended)
1. Open HACS in Home Assistant.
2. Click the 3 dots in the top right corner and select **Custom repositories**.
3. Add the URL to this repository and select **Integration** as the category.
4. Click **Download**.
5. Restart Home Assistant.

### Manual Installation
1. Download the `hardtask` folder from this repository.
2. Copy the folder into your `config/custom_components/` directory.
3. Restart Home Assistant.

## ⚙️ Configuration
This integration is configured via the UI. **Do not add it to your `configuration.yaml`.**

1. Go to **Settings > Devices & Services**.
2. Click **+ Add Integration** in the bottom right corner.
3. Search for **Hardtask**.
4. In the configuration prompt, enter any locations you wish to filter out, separated by commas (e.g., `Příbram, Ostrava`). Leave blank to include all locations.
5. Click **Submit**.

## 📊 Provided Entities
The integration creates two sensors that update every 10 minutes:

* `sensor.hardtask_courses` - Shows the total count of available Main Courses.
* `sensor.hardtask_rangers` - Shows the total count of available Rangers Trainings.

Both sensors contain a `courses` attribute, which is an array of dictionaries containing the parsed data for each available event.

## 💻 Dashboard Configuration
You can display the available courses in a clean grid using standard Markdown cards. Add the following YAML to your dashboard.

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

📱 Blueprints (Notifications)
Get a notification on your phone the second a course becomes available. Import these directly into Home Assistant by pasting these URLs into the "Import Blueprint" section:

Hardtask Courses (Main Site):
https://github.com/stehuz/ha-hardtask/blob/main/blueprints/notify_courses.yaml

Hardtask Rangers:
https://github.com/stehuz/ha-hardtask/blob/main/blueprints/notify_rangers.yaml

🛠️ Troubleshooting
If the sensors show 0 or Unknown:
Check your home-assistant.log for any errors related to hardtask.
Ensure you have beautifulsoup4 installed (it should be handled automatically).
Open an issue on this repository if the website layout has changed.
