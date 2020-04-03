from pathlib import Path

import datetime
import logging
import xml.etree.ElementTree as ET


NAMESPACES = {"pi": "http://www.wldelft.nl/fews/PI"}

logger = logging.getLogger(__name__)


class MissingSettingException(Exception):
    pass


def read_settings(settings_file: Path) -> dict:
    """Return settings from the xml settings file.

    Several settings are mandatory, raise an error when they are missing.

    """
    logger.debug("Reading settings from %s", settings_file)
    result = {}
    root = ET.fromstring(settings_file.read_text())

    required_properties = [
        "username",
        "password",
        "organisation",
        "modelrevision",
        "simulationname",
    ]
    for required_property in required_properties:
        # Extract <properties><string> element with the correct key attribute.
        xpath = f"pi:properties/pi:string[@key='{required_property}']"
        elements = root.findall(xpath, NAMESPACES)
        if not elements:
            raise MissingSettingException(
                f"Required setting '{required_property}' is missing "
                "under <properties> in {settings_file}."
            )
        value = elements[0].attrib["value"]
        logger.debug("Found property %s=%s", required_property, value)
        result[required_property] = value

    for key in ["start", "end"]:
        element_name = f"{key}DateTime"
        # Extract the element with xpath.
        xpath = f"pi:{element_name}"
        elements = root.findall(xpath, NAMESPACES)
        if not elements:
            raise MissingSettingException(
                f"Required setting '{element_name}' is missing " "in {settings_file}."
            )
        date = elements[0].attrib["date"]
        time = elements[0].attrib["time"]
        datetime_string = f"{date}T{time}Z"
        # Note: the available <timeZone> element isn't used yet.
        timestamp = datetime.datetime.strptime(datetime_string, "%Y-%m-%dT%H:%M:%SZ")
        logger.debug("Found timestamp %s=%s", key, timestamp)
        result[key] = timestamp

    return result
