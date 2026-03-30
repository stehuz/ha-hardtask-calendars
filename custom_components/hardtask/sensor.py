import logging
import re
import unicodedata
from datetime import timedelta
from bs4 import BeautifulSoup
import async_timeout

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(minutes=10)

def remove_diacritics(text):
    if not text: return ""
    return "".join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn').lower()

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the sensor platform from the UI."""
    session = async_get_clientsession(hass)
    
    exclude_raw = entry.data.get("exclude_locations", "")
    exclude_list = [remove_diacritics(loc.strip()) for loc in exclude_raw.split(",") if loc.strip()]
    
    courses_coord = await create_courses_coordinator(hass, session, exclude_list)
    rangers_coord = await create_rangers_coordinator(hass, session, exclude_list)

    async_add_entities([
        HardtaskSensor(courses_coord, "Hardtask Courses", "courses"),
        HardtaskSensor(rangers_coord, "Hardtask Rangers", "rangers")
    ], True)

async def create_courses_coordinator(hass, session, exclude_list):
    """Courses Scraper"""
    async def async_update_data():
        try:
            async with async_timeout.timeout(15):
                response = await session.get("https://www.hardtask.cz/cze/kalendar")
                response.raise_for_status()
                html = await response.text()

            soup = BeautifulSoup(html, 'html.parser')
            courses = []
            
            for row in soup.find_all('tr'):
                cells = row.find_all('td', class_='table_content_td')
                if not cells: continue

                d = {"name": "", "instructor": "", "date_time": "", "location": "", "price": "", "url": "", "free_slots": 0}
                for cell in cells:
                    f_name = cell.find('div', class_='mobile_table_field_name')
                    f_val = cell.find('div', class_='mobile_table_field_value')
                    if not f_name or not f_val: continue
                    
                    lbl = f_name.text.strip()
                    
                    if lbl in ["Kurz", "Trénink", "Akce", "Závod"]:
                        link = f_val.find('a')
                        # Clean up nbsp and weird spaces
                        d["name"] = link.text.replace('\xa0', ' ').strip() if link else f_val.get_text(strip=True)
                    elif lbl == "Instruktoři":
                        d["instructor"] = f_val.get_text(", ", strip=True)
                    elif lbl == "Místo":
                        d["location"] = f_val.get_text(" ", strip=True)
                    elif lbl == "Cena vč. DPH":
                        d["price"] = f_val.get_text(" ", strip=True)
                    elif lbl == "Termín":
                        d["date_time"] = re.sub(r'\s+', ' ', f_val.text.replace('-', '')).strip()
                    elif lbl == "":
                        btn = f_val.find(['button', 'div'], class_=re.compile(r'block_button'))
                        if btn and "volno" in btn.text.lower():
                            # FIX: .*? handles the colon (e.g. "volno: 1")
                            m = re.search(r'volno.*?(\d+)', btn.text, re.IGNORECASE)
                            d["free_slots"] = int(m.group(1)) if m else 0
                            
                            p_a = btn.find_parent('a')
                            if p_a and p_a.has_attr('href'):
                                path = p_a['href'].rstrip('\\"')
                                d["url"] = f"https://www.hardtask.cz{path}" if path.startswith("/") else path

                if any(excl in remove_diacritics(d["location"]) for excl in exclude_list):
                    continue

                if d["name"] and d["free_slots"] > 0:
                    d["id"] = f"courses-{d['date_time']}-{d['name']}"
                    courses.append(d)

            return {"courses": courses, "count": len(courses)}
        except Exception as err:
            raise UpdateFailed(f"Courses error: {err}")

    coord = DataUpdateCoordinator(hass, _LOGGER, name="ht_courses", update_method=async_update_data, update_interval=SCAN_INTERVAL)
    await coord.async_config_entry_first_refresh()
    return coord

async def create_rangers_coordinator(hass, session, exclude_list):
    """Rangers Scraper"""
    async def async_update_data():
        try:
            async with async_timeout.timeout(15):
                response = await session.get("https://www.hardtaskrangers.cz/cze/kalendar")
                response.raise_for_status()
                html = await response.text()

            soup = BeautifulSoup(html, 'html.parser')
            courses = []
            
            for row in soup.find_all('tr'):
                cells = row.find_all('td', class_='table_content_td')
                if not cells: continue

                d = {"name": "", "instructor": "", "date_time": "", "location": "", "price": "", "url": "", "free_slots": 0}
                for cell in cells:
                    f_name = cell.find('div', class_='mobile_table_field_name')
                    f_val = cell.find('div', class_='mobile_table_field_value')
                    if not f_name or not f_val: continue
                    
                    lbl = f_name.text.strip()
                    
                    if lbl in ["Kurz", "Trénink", "Akce", "Závod"]:
                        link = f_val.find('a')
                        d["name"] = link.text.replace('\xa0', ' ').strip() if link else f_val.get_text(strip=True)
                    elif lbl == "Instruktoři":
                        d["instructor"] = f_val.get_text(", ", strip=True)
                    elif lbl == "Místo":
                        d["location"] = f_val.get_text(" ", strip=True)
                    elif lbl == "Cena vč. DPH":
                        d["price"] = f_val.get_text(" ", strip=True)
                    elif lbl == "Termín":
                        d["date_time"] = re.sub(r'\s+', ' ', f_val.text.replace('-', '')).strip()
                    elif lbl == "":
                        btn = f_val.find(['button', 'div'], class_=re.compile(r'block_button'))
                        if btn and "volno" in btn.text.lower():
                            # FIX: .*? handles the colon (e.g. "volno: 1")
                            m = re.search(r'volno.*?(\d+)', btn.text, re.IGNORECASE)
                            d["free_slots"] = int(m.group(1)) if m else 0
                            
                            p_a = btn.find_parent('a')
                            if p_a and p_a.has_attr('href'):
                                path = p_a['href'].rstrip('\\"')
                                d["url"] = f"https://www.hardtaskrangers.cz{path}" if path.startswith("/") else path

                if any(excl in remove_diacritics(d["location"]) for excl in exclude_list):
                    continue

                if d["name"] and d["free_slots"] > 0:
                    d["id"] = f"rangers-{d['date_time']}-{d['name']}"
                    courses.append(d)

            return {"courses": courses, "count": len(courses)}
        except Exception as err:
            raise UpdateFailed(f"Rangers error: {err}")

    coord = DataUpdateCoordinator(hass, _LOGGER, name="ht_rangers", update_method=async_update_data, update_interval=SCAN_INTERVAL)
    await coord.async_config_entry_first_refresh()
    return coord

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
