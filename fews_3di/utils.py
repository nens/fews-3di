from pathlib import Path
from typing import Dict
from typing import List

import csv
import datetime
import logging
import xml.etree.ElementTree as ET


NAMESPACES = {"pi": "http://www.wldelft.nl/fews/PI"}
NULL_VALUE = -999

logger = logging.getLogger(__name__)


class MissingSettingException(Exception):
    pass


class MissingFileException(Exception):
    pass


class Settings:
    # Instance variables with their types
    username: str
    password: str
    organisation: str
    modelrevision: str
    simulationname: str
    start: datetime.datetime
    end: datetime.datetime

    def __init__(self, settings_file: Path):
        """Read settings from the xml settings file."""
        self._settings_file = settings_file
        logger.info("Reading settings from %s...", self._settings_file)
        try:
            self._root = ET.fromstring(self._settings_file.read_text())
        except FileNotFoundError as e:
            msg = f"Settings file '{settings_file}' not found"
            raise MissingFileException(msg) from e
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
                f"under <properties> in {self._settings_file}."
            )
        value = elements[0].attrib["value"]
        setattr(self, property_name, value)
        if property_name == "password":
            value = "*" * len(value)
        logger.debug("Found property %s=%s", property_name, value)

    def _read_datetime(self, datetime_variable):
        element_name = f"{datetime_variable}DateTime"
        # Extract the element with xpath.
        xpath = f"pi:{element_name}"
        elements = self._root.findall(xpath, NAMESPACES)
        if not elements:
            raise MissingSettingException(
                f"Required setting '{element_name}' is missing in "
                f"{self._settings_file}."
            )
        date = elements[0].attrib["date"]
        time = elements[0].attrib["time"]
        datetime_string = f"{date}T{time}Z"
        # Note: the available <timeZone> element isn't used yet.
        timestamp = datetime.datetime.strptime(datetime_string, "%Y-%m-%dT%H:%M:%SZ")
        logger.debug("Found timestamp %s=%s", datetime_variable, timestamp)
        setattr(self, datetime_variable, timestamp)

    @property
    def duration(self) -> int:
        """Return duration in seconds."""
        return int((self.end - self.start).total_seconds())

    @property
    def base_dir(self) -> Path:
        return self._settings_file.parent


def lateral_timeseries(laterals_csv: Path, settings: Settings) -> dict:
    if not laterals_csv.exists():
        raise MissingFileException("Lateral csv file %s not found", laterals_csv)

    logger.info("Extracting lateral timeseries from %s", laterals_csv)
    with laterals_csv.open() as csv_file:
        rows = list(csv.reader(csv_file, delimiter=","))

    # Get headers (first row, but omit the first column).
    headers = rows[0][1:]
    # Strip header rows from rows.
    rows = rows[2:]

    timeseries: Dict[str, List] = {}
    previous_values: Dict[
        str, float
    ] = {}  # Values can be omitted if they stay the same.
    for header in headers:
        timeseries[header] = []

    for row in rows:
        # Convert first column to datetime
        timestamp = datetime.datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S")
        offset = (timestamp - settings.start).total_seconds()
        # Check if in range for simulation
        if (timestamp < settings.start) or (timestamp > settings.end):
            continue

        for index, value_str in enumerate(row[1:]):
            key = headers[index]
            value = float(value_str)
            previous_value = previous_values.get(key, None)

            if previous_value == value:
                # If the last value is the same as the current we can skip it.
                continue
            if value != NULL_VALUE:
                # add the value as [offset, value] if it's not a NULL_VALUE
                timeseries[key].append([offset, value])
            elif previous_value != NULL_VALUE and previous_value != 0.0:
                # Add 0.0 once for first NULL_VALUE after a valid value
                # and only when the last value was not 0.0
                timeseries[key].append([offset, 0.0])
            # Set previous_values
            previous_values[key] = value

    return timeseries
