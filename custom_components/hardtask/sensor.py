import logging
import re
import unicodedata
from datetime import timedelta
from bs4 import BeautifulSoup
import async_timeout

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.sensor import PLATFORM_SCHEMA, SensorEntity
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

_LOGGER = logging.getLogger(__name__)
DOMAIN = "hardtask"
SCAN_INTERVAL = timedelta(minutes=10)

# Validation schema for configuration.yaml
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional("exclude_locations", default=[]): vol.All(cv.ensure_list, [cv.string]),
})

CONFIG_DATA = {
    "courses": {"url": "https://www.hardtask.cz/cze/kalendar", "name": "Hardtask Courses"},
    "rangers": {"url": "https://www.hardtaskrangers.cz/cze/kalendar", "name": "Hardtask Rangers"}
}

def remove_diacritics(text):
    if not text: return ""
    return "".join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn').lower()

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    session = async_get_clientsession(hass)
    # Get the list of excluded locations from YAML, normalized to lowercase/no accents
    exclude_list = [remove_diacritics(loc) for loc in config.get("exclude_locations")]
    
    sensors = []
    for key, info in CONFIG_DATA.items():
        coordinator = await create_coordinator(hass, session, key, info["url"], exclude_list)
        sensors.append(HardtaskSensor(coordinator, info["name"], key))

    async_add_entities(sensors, True)

async def create_coordinator(hass, session, key, url, exclude_list):
    async def async_update_data():
        try:
            async with async_timeout.timeout(10):
                response = await session.get(url)
                response.raise_for_status()
                html = await response.text()

            soup = BeautifulSoup(html, 'html.parser')
            courses = []
            rows = soup.find_all('tr')

            for row in rows:
                cells = row.find_all('td', class_='table_content_td')
                if not cells: continue

                name = instructor = date_time = location = price = reg_url = ""
                free_slots = 0

                for cell in cells:
                    f_name_div = cell.find('div', class_='mobile_table_field_name')
                    f_val_div = cell.find('div', class_='mobile_table_field_value')
                    if not f_name_div or not f_val_div: continue
                    
                    f_name = f_name_div.text.strip()
                    if f_name in ["Kurz", "Trénink"]:
                        name = f_val_div.find('a').text.strip() if f_val_div.find('a') else ""
                    elif f_name == "Instruktoři":
                        instructor = f_val_div.get_text(", ", strip=True)
                    elif f_name == "Místo":
                        location = f_val_div.get_text(" ", strip=True)
                    elif f_name == "Cena vč. DPH":
                        price = f_val_div.get_text(" ", strip=True)
                    elif f_name == "Termín":
                        date_time = re.sub(r'\s+', ' ', f_val_div.text.replace('-', '')).strip()
                    elif f_name == "":
                        btn = f_val_div.find(['button', 'div'], class_=re.compile(r'block_button'))
                        if btn and "volno" in btn.text.lower():
                            match = re.search(r'volno\s*(\d+)', btn.text, re.IGNORECASE)
                            free_slots = int(match.group(1)) if match else 0
                            parent_a = btn.find_parent('a')
                            if parent_a and parent_a.has_attr('href'):
                                base = "https://www.hardtask.cz" if key == "courses" else "https://www.hardtaskrangers.cz"
                                reg_url = parent_a['href'].rstrip('\\"')
                                if reg_url.startswith("/"): reg_url = f"{base}{reg_url}"

                # Check if this location's normalized name is in our exclusion list
                loc_normalized = remove_diacritics(location)
                if any(excl in loc_normalized for excl in exclude_list):
                    continue

                if name and date_time and free_slots > 0:
                    courses.append({
                        "name": name, "instructor": instructor, "date_time": date_time,
                        "location": location, "price": price, "free_slots": free_slots,
                        "url": reg_url, "id": f"{key}-{date_time}-{name}"
                    })
            return {"courses": courses, "count": len(courses)}
        except Exception as err:
            raise UpdateFailed(f"Update failed for {key}: {err}")

    coordinator = DataUpdateCoordinator(
        hass, _LOGGER, name=f"hardtask_{key}_coordinator",
        update_method=async_update_data, update_interval=SCAN_INTERVAL,
    )
    await coordinator.async_config_entry_first_refresh()
    return coordinator

class HardtaskSensor(SensorEntity):
    def __init__(self, coordinator, name, key):
        self.coordinator = coordinator
        self._attr_name = name
        self._attr_unique_id = f"hardtask_{key}_sensor"
        self._attr_icon = "mdi:target" if key == "rangers" else "mdi:shield-check"

    @property
    def native_value(self):
        return self.coordinator.data.get("count", 0) if self.coordinator.data else 0

    @property
    def extra_state_attributes(self):
        return {"courses": self.coordinator.data.get("courses", [])} if self.coordinator.data else {"courses": []}

    async def async_update(self):
        await self.coordinator.async_request_refresh()
