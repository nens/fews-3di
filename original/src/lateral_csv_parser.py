"""Comments by Reinout

My impression is that it can be done a bit shorter/clearer. Perhaps splitting
it into two or three functions is enough.

"""
from datetime import datetime

import csv


NULL_VALUE = -999


def get_lateral_timeseries(csv_file_path, sim_start, sim_end):

    # start = datetime.strptime("2019-07-24 06:00:00", '%Y-%m-%d %H:%M:%S')
    # end = datetime.strptime("2019-07-24 12:00:00", '%Y-%m-%d %H:%M:%S')

    with open(csv_file_path, "r") as csvfile:
        readCSV = csv.reader(csvfile, delimiter=",")

        # Read all data in llist
        data = [x for x in readCSV]

        # Get headers (first row)
        headers = data[0][1:]

        # Strip headers from data
        data = data[2:]

    # Create dictionary for timeseries
    timeseries = {}

    # Initialize dictionairy with headers
    for header in headers:
        timeseries[header] = []

    # Keep track of the last timeseries read
    last_data = {}

    # loop through all rows
    for row in data:
        # Convert first column to datetime
        date = datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S")
        # Check if in range for simulation
        if sim_start <= date <= sim_end:
            # Loop through all timeseries data
            # Calculate offset in simulation
            offset = (date - sim_start).total_seconds()

            for index, value in enumerate(row[1:]):
                # Convert value to float
                value = float(value)
                name = headers[index]

                # If the last value is the same as the current
                # we can skip it
                if last_data.get(name, None) == value:
                    continue

                if value != NULL_VALUE:
                    # add the value as [offset, value] if it's not a NULL_VALUE
                    timeseries[name].append([offset, value])
                elif (
                    name in last_data
                    and last_data[name] != NULL_VALUE
                    and last_data[name] != 0.0
                ):
                    # Add 0.0 once for first NULL_VALUE after a valid value
                    # and only when the last value was not 0.0
                    timeseries[name].append([offset, 0.0])
                # Set last_data
                last_data[name] = value

    return timeseries
