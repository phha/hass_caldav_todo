import logging
import caldav
from caldav.objects import Calendar
from homeassistant.helpers.entity import generate_entity_id
import voluptuous as vol
from datetime import timedelta
from typing import List, Optional
from homeassistant.components.binary_sensor import ENTITY_ID_FORMAT, PLATFORM_SCHEMA, BinarySensorEntity
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import (
    ConfigType,
    DiscoveryInfoType,
    HomeAssistantType,
)
from homeassistant.const import (
    CONF_NAME,
    CONF_PASSWORD,
    CONF_URL,
    CONF_USERNAME,
    CONF_VERIFY_SSL,
)

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(minutes=10)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        # pylint: disable=no-value-for-parameter
        vol.Required(CONF_URL): vol.Url(),
        vol.Inclusive(CONF_USERNAME, "authentication"): cv.string,
        vol.Inclusive(CONF_PASSWORD, "authentication"): cv.string,
        vol.Optional(CONF_VERIFY_SSL, default=True): cv.boolean
    }
)

def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: Optional[DiscoveryInfoType] = None,
) -> None:
    url = config[CONF_URL]
    username = config.get(CONF_USERNAME)
    password = config.get(CONF_PASSWORD)

    client = caldav.DAVClient(
        url, None, username, password, ssl_verify_cert=config[CONF_VERIFY_SSL]
    )

    entities = []
    calendars = client.principal().calendars()
    for calendar in calendars:
        name = calendar.name
        entity_id = generate_entity_id(ENTITY_ID_FORMAT, name, hass=hass)
        entity = CaldavTodoBinarySensor(name, entity_id, calendar)
        entities.append(entity)
    add_entities(entities, True)


class CaldavTodoBinarySensor(BinarySensorEntity):
    def __init__(self, name: str, entity_id: str, calendar: Calendar):
        self._name = name
        self._state = None
        self.entity_id = entity_id
        self._calendar = calendar
        self._tasks = []

    @property
    def name(self) -> str:
        return self._name

    @property
    def is_on(self) -> bool:
        return self._state

    @property
    def extra_state_attributes(self):
        return {
            "all_tasks": self._tasks
        }

    def update(self):
        todos = self._calendar.todos()
        self._tasks = [
            t.vobject_instance.vtodo.summary.value for t in todos
        ]
        self._state: bool = bool(len(todos))
