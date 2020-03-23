# import getpass
# import json
import os
import requests

# import numpy as np
import pandas as pd
import logging

from openapi_client import (
    ApiClient,
    Configuration,
    AuthApi,
    SimulationsApi,
    ThreedimodelsApi,
)
from openapi_client.models import Authenticate

# import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from time import sleep

from settings import settings
from threedigrid.admin.gridresultadmin import GridH5ResultAdmin

is_linux = False


def convert_path(path):
    if is_linux:
        return path.replace("\\", "/")
    return path


# read settings file
setting = settings(convert_path(r"..\run_info.xml"))

# set variables
user = setting[0]
password = setting[1]
organisation = setting[2]
model_rev = setting[3]
sim_name = setting[4]
state_file = setting[5]
save_state = setting[6]
expirydays = setting[7]
tstart = setting[8]
duration = setting[9]


# Read results
results = GridH5ResultAdmin(
    convert_path(r"..\\model\\gridadmin.h5"),
    convert_path(r"..\\output\\results_3di.nc"),
)

times = (
    results.pumps.timestamps[()]
    + datetime.strptime(tstart, "%Y-%m-%dT%H:%M:%SZ").timestamp()
)
times = times.astype("datetime64[s]")
times = pd.Series(times).dt.round("10 min")
endtime = results.pumps.timestamps[-1]
pump_id = results.pumps.display_name.astype("U13")
discharges = results.pumps.timeseries(start_time=0, end_time=endtime).data["q_pump"]
df = pd.DataFrame(discharges, index=times, columns=pump_id)
params = ["Q.sim" for x in range(len(df.columns))]

df.columns = pd.MultiIndex.from_arrays([pump_id, pump_id, params])
df.to_csv(convert_path(r"..\output\discharges.csv"), index=True, header=True, sep=",")
logger.info("Simulated discharges are exported")

# Write FEWS-readable NetCDF file
import netCDF4

dset = netCDF4.Dataset(r"..\\output\\ow.nc", "a")
s1 = results.nodes.subset("2D_OPEN_WATER").timeseries(start_time=0, end_time=endtime).s1
dset["Mesh2D_s1"][:] = s1
dset.close()

# Finish
logger.info("Done")
