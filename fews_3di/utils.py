from pathlib import Path

import xml.etree.ElementTree as ET


NAMESPACES = {"pi": "http://www.wldelft.nl/fews/PI"}


class MissingSettingException(Exception):
    pass


def read_settings(settings_file: Path) -> dict:
    """Return settings from the xml settings file.

    Several settings are mandatory, raise an error when they are missing.

    """
    result = {}
    root = ET.fromstring(settings_file.read_text())
    print(root)
    required_properties = [
        "username",
        "password",
        "organisation",
        "modelrevision",
        "simulationname",
    ]
    for required_property in required_properties:
        xpath = f"pi:properties/pi:string[@key='{required_property}']"
        elements = root.findall(xpath, NAMESPACES)
        if len(elements) != 1:
            raise MissingSettingException(
                f"Required property '{required_property}' is missing"
            )
        value = elements[0].attrib["value"]
        result[required_property] = value
    return result
