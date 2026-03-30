from homeassistant import config_entries
import voluptuous as vol
from .const import DOMAIN

class HardtaskConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Hardtask."""
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            return self.async_create_entry(title="Hardtask Calendars", data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Optional("exclude_locations", default=""): str,
            }),
        )
