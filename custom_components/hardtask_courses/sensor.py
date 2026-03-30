import logging
import re
from datetime import timedelta
from bs4 import BeautifulSoup
import async_timeout

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

_LOGGER = logging.getLogger(__name__)
DOMAIN = "hardtask_courses"
URL = "https://www.hardtask.cz/cze/kalendar"
SCAN_INTERVAL = timedelta(minutes=10)

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    session = async_get_clientsession(hass)

    async def async_update_data():
        try:
            async with async_timeout.timeout(10):
                response = await session.get(URL)
                response.raise_for_status()
                html = await response.text()

            soup = BeautifulSoup(html, 'html.parser')
            courses = []

            rows = soup.find_all('tr')

            for row in rows:
                cells = row.find_all('td', class_='table_content_td')
                if not cells:
                    continue

                name = ""
                instructor = ""
                date_time = ""
                location = ""
                price = ""
                free_slots = 0
                url = ""

                for cell in cells:
                    field_name_div = cell.find('div', class_='mobile_table_field_name')
                    field_value_div = cell.find('div', class_='mobile_table_field_value')
                    
                    if not field_name_div or not field_value_div:
                        continue
                        
                    field_name = field_name_div.text.strip()

                    if field_name == "Kurz":
                        a_tag = field_value_div.find('a')
                        if a_tag:
                            name = a_tag.text.strip()

                    elif field_name == "Instruktoři":
                        instructor = field_value_div.get_text(", ", strip=True)

                    elif field_name == "Místo":
                        location = field_value_div.get_text(" ", strip=True)

                    elif field_name == "Cena vč. DPH":
                        price = field_value_div.get_text(" ", strip=True)

                    elif field_name == "Termín":
                        date_time = field_value_div.text.replace('-', '').strip()
                        date_time = re.sub(r'\s+', ' ', date_time)

                    elif field_name == "":
                        button = field_value_div.find('button', class_=re.compile(r'block_button'))
                        if button and "volno" in button.text.lower():
                            match = re.search(r'volno[:\s]*(\d+)', button.text, re.IGNORECASE)
                            if match:
                                free_slots = int(match.group(1))
                            
                            parent_a = button.find_parent('a')
                            if parent_a and parent_a.has_attr('href'):
                                raw_url = parent_a['href']
                                url = raw_url.rstrip('\\"')
                                if url.startswith("/"):
                                    url = f"https://www.hardtask.cz{url}"

                if name and date_time and free_slots > 0:
                    courses.append({
                        "name": name,
                        "instructor": instructor,
                        "date_time": date_time,
                        "location": location,
                        "price": price,
                        "free_slots": free_slots,
                        "url": url,
                        "id": f"HT-{date_time}-{name}"
                    })

            return {"courses": courses, "count": len(courses)}

        except Exception as err:
            raise UpdateFailed(f"Error communicating with Hardtask Courses: {err}")

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="hardtask_courses_coordinator",
        update_method=async_update_data,
        update_interval=SCAN_INTERVAL,
    )

    await coordinator.async_config_entry_first_refresh()
    async_add_entities([HardtaskCoursesSensor(coordinator)])


class HardtaskCoursesSensor(SensorEntity):
    def __init__(self, coordinator):
        self.coordinator = coordinator
        self._attr_name = "Hardtask Courses Available"
        self._attr_icon = "mdi:shield-check"

    @property
    def native_value(self):
        if self.coordinator.data:
            return self.coordinator.data.get("count", 0)
        return 0

    @property
    def extra_state_attributes(self):
        if self.coordinator.data:
            return {"courses": self.coordinator.data.get("courses", [])}
        return {"courses": []}

    async def async_update(self):
        await self.coordinator.async_request_refresh()
