from pathlib import Path

import datetime
import logging
import xml.etree.ElementTree as ET


NAMESPACES = {"pi": "http://www.wldelft.nl/fews/PI"}

logger = logging.getLogger(__name__)


class MissingSettingException(Exception):
    pass


class Settings:
    # Instance variables with their types
    username: str
    password: str
    organisation: str
    modelrevision: str
    simulation_name: str
    start: datetime.datetime
    end: datetime.datetime

    def __init__(self, settings_file: Path):
        """Read settings from the xml settings file."""
        self._settings_file = settings_file
        self._root = ET.fromstring(settings_file.read_text())
        required_properties = [
            "username",
            "password",
            "organisation",
            "modelrevision",
            "simulationname",
        ]
        for property_name in required_properties:
            self._read_property(property_name)
        datetime_variables = ["start", "end"]
        for datetime_variable in datetime_variables:
            self._read_datetime(datetime_variable)

    def _read_property(self, property_name):
        """Extract <properties><string> element with the correct key attribute."""
        xpath = f"pi:properties/pi:string[@key='{property_name}']"
        elements = self._root.findall(xpath, NAMESPACES)
        if not elements:
            raise MissingSettingException(
                f"Required setting '{property_name}' is missing "
                "under <properties> in {settings_file}."
            )
        value = elements[0].attrib["value"]
        logger.debug("Found property %s=%s", property_name, value)
        setattr(self, property_name, value)

    def _read_datetime(self, datetime_variable):
        element_name = f"{datetime_variable}DateTime"
        # Extract the element with xpath.
        xpath = f"pi:{element_name}"
        elements = self._root.findall(xpath, NAMESPACES)
        if not elements:
            raise MissingSettingException(
                f"Required setting '{element_name}' is missing in "
                "{self._settings_file}."
            )
        date = elements[0].attrib["date"]
        time = elements[0].attrib["time"]
        datetime_string = f"{date}T{time}Z"
        # Note: the available <timeZone> element isn't used yet.
        timestamp = datetime.datetime.strptime(datetime_string, "%Y-%m-%dT%H:%M:%SZ")
        logger.debug("Found timestamp %s=%s", datetime_variable, timestamp)
        setattr(self, datetime_variable, timestamp)
