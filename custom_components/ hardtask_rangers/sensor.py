import logging
import re
from datetime import timedelta
from bs4 import BeautifulSoup
import async_timeout
import unicodedata # Přidáno pro odstranění diakritiky

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

_LOGGER = logging.getLogger(__name__)
DOMAIN = "hardtask_rangers"
URL = "https://www.hardtaskrangers.cz/cze/kalendar"
SCAN_INTERVAL = timedelta(minutes=10)

def remove_diacritics(text):
    """Odstraní diakritiku z textu pro spolehlivější vyhledávání."""
    if text is None:
        return ""
    # Normalizuje text a odstraní ne-ASCII znaky (háčky/čárky)
    return "".join(c for c in unicodedata.normalize('NFD', text)
                   if unicodedata.category(c) != 'Mn').lower()

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the sensor platform."""
    session = async_get_clientsession(hass)

    async def async_update_data():
        try:
            async with async_timeout.timeout(10):
                response = await session.get(URL)
                response.raise_for_status()
                html = await response.text()

            soup = BeautifulSoup(html, 'html.parser')
            courses = []

            # Najít všechny řádky tabulky
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

                    if field_name == "Trénink":
                        a_tag = field_value_div.find('a')
                        if a_tag:
                            name = a_tag.text.strip()

                    elif field_name == "Instruktoři":
                        instructor = field_value_div.text.strip()

                    elif field_name == "Místo":
                        # Získat čistý text lokace, handling potential spaces/breaks
                        location = " ".join(field_value_div.stripped_strings)

                    elif field_name == "Cena vč. DPH":
                        price = field_value_div.get_text(" ", strip=True)

                    elif field_name == "Termín":
                        date_time = " ".join(field_value_div.stripped_strings)

                    elif field_name == "":
                        button = field_value_div.find('div', class_='block_button', id=re.compile(r'^training_class_button_'))
                        if button and "Volno" in button.text:
                            match = re.search(r'Volno\s*(\d+)', button.text, re.IGNORECASE)
                            if match:
                                free_slots = int(match.group(1))
                            
                            parent_a = button.find_parent('a')
                            if parent_a and parent_a.has_attr('href'):
                                raw_url = parent_a['href']
                                url = raw_url.rstrip('\\"')
                                if url.startswith("/"):
                                    url = f"https://www.hardtaskrangers.cz{url}"

                if name and date_time and free_slots > 0:
                    
                    # --- VYLEPŠENÁ LOGIKA FILTROVÁNÍ LOKACE ---
                    # Vyčistíme lokaci od diakritiky a převedeme na malá písmena
                    # "Brod 44 (Příbram)" se změní na "brod 44 (pribram)"
                    normalized_location = remove_diacritics(location)
                    
                    # Hledáme "pribram" v očištěném řetězci
                    if "pribram" in normalized_location:
                        continue # Přeskočit tento trénink
                    # ------------------------------------------

                    instructor = re.sub(r'\s+', ' ', instructor).strip()
                    
                    courses.append({
                        "name": name,
                        "instructor": instructor,
                        "date_time": date_time,
                        "location": location, # Původní název pro zobrazení (Brod 44 (Příbram))
                        "price": price,
                        "free_slots": free_slots,
                        "url": url,
                        "id": f"{date_time}-{name}"
                    })

            return {"courses": courses, "count": len(courses)}

        except Exception as err:
            raise UpdateFailed(f"Error communicating with Hardtask Rangers: {err}")

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="hardtask_rangers_coordinator",
        update_method=async_update_data,
        update_interval=SCAN_INTERVAL,
    )

    await coordinator.async_config_entry_first_refresh()
    async_add_entities([HardtaskRangersSensor(coordinator)])


class HardtaskRangersSensor(SensorEntity):
    """Representation of the Hardtask Rangers Sensor."""

    def __init__(self, coordinator):
        self.coordinator = coordinator
        self._attr_name = "Hardtask Rangers Available Trainings"
        self._attr_icon = "mdi:target"

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
