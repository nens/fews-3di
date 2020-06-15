from collections import namedtuple
from pathlib import Path
from typing import Dict
from typing import List

import cftime
import csv
import datetime
import logging
import netCDF4 as nc
import numpy as np
import tempfile
import xml.etree.ElementTree as ET


NAMESPACES = {"pi": "http://www.wldelft.nl/fews/PI"}
NULL_VALUE = -999

logger = logging.getLogger(__name__)


OffsetAndValue = namedtuple("OffsetAndValue", ["offset", "value"])


class MissingSettingException(Exception):
    pass


class MissingFileException(Exception):
    pass


class Settings:
    # Instance variables with their types
    end: datetime.datetime
    modelrevision: str
    organisation: str
    password: str
    save_state: bool
    saved_state_expiry_days: int
    settings_file: Path
    simulationname: str
    start: datetime.datetime
    username: str
    lizard_results_scenario_name: str

    def __init__(self, settings_file: Path):
        """Read settings from the xml settings file."""
        self.settings_file = settings_file
        setattr(self, "lizard_results_scenario_name", "")
        setattr(self, "lizard_results_scenario_uuid", "")
        logger.info("Reading settings from %s...", self.settings_file)
        try:
            self._root = ET.fromstring(self.settings_file.read_text())
        except FileNotFoundError as e:
            msg = f"Settings file '{settings_file}' not found"
            raise MissingFileException(msg) from e
        required_properties = [
            "modelrevision",
            "organisation",
            "password",
            "save_state",
            "saved_state_expiry_days",
            "simulationname",
            "username",
        ]
        optional_properties = [
            "lizard_results_scenario_name",
            "lizard_results_scenario_uuid",
        ]
        for property_name in required_properties:
            self._read_property(property_name)

        for property_name in optional_properties:
            self._read_property(property_name, True)

        datetime_variables = ["start", "end"]
        for datetime_variable in datetime_variables:
            self._read_datetime(datetime_variable)

    def _read_property(self, property_name, optional=False):
        """Extract <properties><string> element with the correct key attribute."""
        xpath = f"pi:properties/pi:string[@key='{property_name}']"
        elements = self._root.findall(xpath, NAMESPACES)
        if not elements and not optional:
            raise MissingSettingException(
                f"Required setting '{property_name}' is missing "
                f"under <properties> in {self.settings_file}."
            )
        if not elements and optional:
            return

        string_value = elements[0].attrib["value"]
        if property_name == "save_state":
            value = string_value.lower() == "true"
        elif property_name == "saved_state_expiry_days":
            value = int(string_value)
        else:
            # Normal situation.
            value = string_value
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
                f"{self.settings_file}."
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
        return self.settings_file.parent


def lateral_timeseries(
    laterals_csv: Path, settings: Settings
) -> Dict[str, List[OffsetAndValue]]:
    if not laterals_csv.exists():
        raise MissingFileException("Lateral csv file %s not found", laterals_csv)

    logger.info("Extracting lateral timeseries from %s", laterals_csv)
    with laterals_csv.open() as csv_file:
        rows = list(csv.reader(csv_file, delimiter=","))

    # Get headers (first row, but omit the first column).
    headers = rows[0][1:]
    # Strip header rows from rows.
    rows = rows[2:]

    timeseries: Dict[str, List[OffsetAndValue]] = {}
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
            logger.debug("Omitting timestamp %s", timestamp)
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
                timeseries[key].append(OffsetAndValue(offset, value))
            elif previous_value != NULL_VALUE and previous_value != 0.0:
                # Add 0.0 once for first NULL_VALUE after a valid value
                # and only when the last value was not 0.0
                timeseries[key].append(OffsetAndValue(offset, 0.0))
            # Set previous_values
            previous_values[key] = value

    # Extra checks/cleanup.
    to_remove: List[str] = []
    for name, timeserie in timeseries.items():
        if len(timeserie) < 2:
            to_remove.append(name)
            continue
        first_offset = timeserie[0].offset
        if first_offset != 0:
            # Timeseries always should start at 0.
            shift_back_by = first_offset
            logger.warning(
                "lateral timeserie '%s' does not start at 0; shifting "
                "*all* times back by %s seconds.",
                name,
                shift_back_by,
            )
            shifted_timeserie = [
                OffsetAndValue(offset - shift_back_by, value)
                for offset, value in timeserie
            ]
            timeseries[name] = shifted_timeserie
    for name in to_remove:
        logger.warn(
            "Removing lateral timeserie '%s' because there are less than two values",
            name,
        )
        del timeseries[name]

    return timeseries


def timestamps_from_netcdf(source_file: Path) -> List[cftime.DatetimeGregorian]:
    source = nc.Dataset(source_file)
    timestamps = nc.num2date(source["time"][:], source["time"].units)
    source.close()
    return timestamps


def write_new_netcdf(source_file: Path, target_file: Path, time_indexes: List):
    source = nc.Dataset(source_file)
    target = nc.Dataset(target_file, mode="w")

    # Create the dimensions of the file.
    for name, dim in source.dimensions.items():
        dim_length = len(dim)
        if name == "time":
            dim_length = len(time_indexes)
        target.createDimension(name, dim_length if not dim.isunlimited() else None)

    # Copy the global attributes.
    target.setncatts({a: source.getncattr(a) for a in source.ncattrs()})

    # Create the variables in the file.
    for name, var in source.variables.items():
        target.createVariable(name, var.dtype, var.dimensions)
        # Copy the variable attributes.
        target.variables[name].setncatts({a: var.getncattr(a) for a in var.ncattrs()})
        # Copy the variables values (as 'f4' eventually).
        data = source.variables[name][:]
        if name in ("time", "values", "Mesh2D_s1"):
            data = data[time_indexes]
        target.variables[name][:] = data

    # Save the file.
    target.close()
    source.close()


def write_netcdf_with_time_indexes(source_file: Path, settings: Settings):
    """Return netcdf file with only time indexes"""
    if not source_file.exists():
        raise MissingFileException("Source netcdf file %s not found", source_file)

    logger.info("Converting %s to a file with only time indexes", source_file)
    relevant_timestamps = timestamps_from_netcdf(source_file)
    # Figure out which timestamps are valid for the given simulation period.
    time_indexes: List = (
        np.argwhere(  # type: ignore
            (relevant_timestamps >= settings.start)  # type: ignore
            & (relevant_timestamps <= settings.end)  # type: ignore
        )
        .flatten()
        .tolist()
    )

    # Create new file with only time indexes
    temp_dir = Path(tempfile.mkdtemp(prefix="fews-3di"))
    target_file = temp_dir / source_file.name
    write_new_netcdf(source_file, target_file, time_indexes)
    logger.debug("Wrote new time-index-only netcdf to %s", target_file)
    return target_file
