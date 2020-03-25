"""Comments by Reinout

One big file, most everything on the main level. So it looks like the main script :-)

- Split it up in separate functions.

- Fix settings handling. Turn it into a dict. Or read an ini file with
  defaults. Or accept more command line parameters.

- Mark constants (3di api url, for instance) as such.

- Fix path handling (raw strings with backslashes and even with double
  backslashes). Especially those last ones won't work if ``convert_path()`` is
  used :-)

- Several things happen here. Starting a sim; downloading results; doing some
  processing; etcetera. Turn everything into separate properly-named
  functions, that should make the flow clearer. And it would show which
  variables are needed.

"""
from datetime import datetime
from datetime import timedelta
from lateral_csv_parser import get_lateral_timeseries
from netcdf_utils import create_file_from_source
from netcdf_utils import get_datetimes_from_source
from openapi_client import ApiClient
from openapi_client import AuthApi
from openapi_client import Configuration
from openapi_client import SimulationsApi
from openapi_client import ThreedimodelsApi
from openapi_client.models import Authenticate
from settings import settings
from threedigrid.admin.gridresultadmin import GridH5ResultAdmin
from time import sleep

import logging
import netCDF4
import numpy as np
import os
import pandas as pd
import requests


is_linux = False


def convert_path(path):
    if is_linux:
        return path.replace("\\", "/")
    return path


# TODO: standardize logging setup. And move the actual config into the main
# script runner.
logger = logging.getLogger("simple")
logger.setLevel(logging.INFO)
ch = logging.FileHandler("../logs/3Di_log.txt")
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(levelname)s - %(asctime)s - %(message)s")
ch.setFormatter(formatter)
logger.addHandler(ch)

ch_console = logging.StreamHandler()
ch_console.setLevel(logging.DEBUG)
ch_console.setFormatter(formatter)
logger.addHandler(ch_console)

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
tend = tstart + timedelta(seconds=duration)

# selected state_id
with open(convert_path(state_file), "r") as statefile:
    state_id = statefile.read()
logger.info("Simulation will use initial state: %s", state_id)

# authentication handling
configuration = Configuration()

configuration.host = "https://api.3di.live/v3.0"

api_client = ApiClient(configuration)
auth = AuthApi(api_client)
tokens = auth.auth_token_create(Authenticate(user, password))

configuration.api_key["Authorization"] = tokens.access
configuration.api_key_prefix["Authorization"] = "Bearer"

# new client instance with auth headers
client = ApiClient(configuration)

# Find ThreeDiModel
models = ThreedimodelsApi(api_client)
model = models.threedimodels_list(slug__contains=model_rev)
model_id = model.results[0].id
logger.info("Simulation uses model revision: %s", model_rev)

# Create simulation
data = {}
data["name"] = sim_name
data["threedimodel"] = model_id
data["organisation"] = organisation
data["start_datetime"] = datetime.strftime(tstart, "%Y-%m-%dT%H:%M:%SZ")
data["duration"] = duration
logger.info("Simulation will start at: %s", tstart)
logger.info("Simulation will run for: %s", duration)


sim_api = SimulationsApi(api_client)
sim = sim_api.simulations_create(data)
sim_id = sim.id

logger.info("Simulation has been created with id: %s", str(sim_id))
logger.info("Start processing laterals")

laterals = get_lateral_timeseries(convert_path(r"..\input\lateral.csv"), tstart, tend)

lateral_ids_not_processed = []

for name, timeseries in laterals.items():
    logger.info("Uploading lateral: %s", str(name))

    # Timeseries always should start at 0
    offset = timeseries[0][0]
    if offset > 0:
        timeseries = [[x[0] - offset, x[1]] for x in timeseries]

    if len(timeseries) < 2:
        logger.info("Skipping lateral due to zero timeseries: %s", str(name))
    else:
        lateral = sim_api.simulations_events_lateral_timeseries_create(
            simulation_pk=sim_id,
            data={
                "offset": offset,
                "interpolate": False,
                "values": timeseries,
                "units": "m3/s",
                "connection_node": name,
            },
        )
        lateral_ids_not_processed.append(lateral.id)

# Check whether laterals have been processed
processing = True

logger.info(f"Start waiting for laterals to be processed")

while processing:
    lateral_indexes = [x for x in lateral_ids_not_processed]
    for idx in lateral_indexes:
        lateral = sim_api.simulations_events_lateral_timeseries_read(
            simulation_pk=sim_id, id=idx
        )
        if lateral.state.lower() == "processing":
            continue
        elif lateral.state.lower() == "invalid":
            raise Exception("Invalid lateral %s" % lateral)
        elif lateral.state.lower() == "valid":
            print(f"Lateral {lateral.id} succesfully validated")
            lateral_ids_not_processed.remove(idx)

    if len(lateral_ids_not_processed) == 0:
        processing = False

    sleep(2)
# Set initial state
initial_state_data = {"saved_state": "{}".format(state_id)}

# Set this to True if you want to use the initial state
set_initial_state = True

if set_initial_state:
    sim_api.simulations_initial_saved_state_create(sim_id, data=initial_state_data)


# Save flow state
if save_state == "True":
    # ^^^ TODO: a literal string "True" smells dirty.
    expirytime = datetime.now() + timedelta(days=int(expirydays))
    expirytime = datetime.strftime(expirytime, "%Y-%m-%dT%H:%M:%SZ")
    save_state_data = {
        "name": "Texel operational",
        "time": duration,
        "expiry": expirytime,
    }

    sim_save_state = sim_api.simulations_create_saved_states_timed_create(
        sim_id, data=save_state_data
    )
    logger.info("Saved state created: {}".format(sim_save_state.url))
else:
    sim_save_state = None


# Post rain events
rainfilename = "precipitation.nc"
filepath = r"..\input"


full_path = convert_path(os.path.join(filepath, rainfilename))
new_path = full_path.replace(".nc", "_{}.nc".format(sim_id))

# Get all precipitation datetimes in the file
precipitation_datetimes = get_datetimes_from_source(full_path)

# Figure out which are valid for the given simulation period
# precipation_datetimes
time_indexes = (
    np.argwhere((precipitation_datetimes >= tstart) & (precipitation_datetimes <= tend))
    .flatten()
    .tolist()
)

# Create new file with only time_indexes
create_file_from_source(full_path, new_path, time_indexes)

# Declare rainfile upload and upload to put_url using requests
sim_upload_rain = sim_api.simulations_events_rain_rasters_netcdf_create(
    sim_id, data={"filename": rainfilename.replace(".nc", "_{}.nc".format(sim_id))}
)
with open(new_path, "rb") as f:
    requests.put(sim_upload_rain.put_url, data=f)


# Check whether rain upload has been processed
processing = True
sleep(2)

while processing:
    # TODO: move the sleep up here.
    upload_status = sim_api.simulations_events_rain_rasters_netcdf_list(sim_id)
    if upload_status.results[0].file.state == "processed":
        processing = False
    else:
        sleep(2)

# Post evaporation events
evapfilename = "evaporation.nc"
filepath = r"..\input"

full_path = convert_path(os.path.join(filepath, evapfilename))
new_path = full_path.replace(".nc", "_{}.nc".format(sim_id))

# Get all evaporation datetimes in the file
evap_datetimes = get_datetimes_from_source(full_path)

# Figure out which are valid for the given simulation period
# precipation_datetimes
time_indexes = (
    np.argwhere((evap_datetimes >= tstart) & (evap_datetimes <= tend))
    .flatten()
    .tolist()
)

# Create new file with only time_indexes
create_file_from_source(full_path, new_path, time_indexes)

# Declare evaporation upload and upload to put_url using requests
sim_upload_evap = sim_api.simulations_events_sources_sinks_rasters_netcdf_create(
    sim_id, data={"filename": evapfilename.replace(".nc", "_{}.nc".format(sim_id))}
)

with open(new_path, "rb") as f:
    requests.put(sim_upload_evap.put_url, data=f)

sleep(2)

# Check whether rain upload has been processed
processing = True

while processing:
    upload_status = sim_api.simulations_events_sources_sinks_rasters_netcdf_list(sim_id)
    if upload_status.results[0].file.state == "processed":
        processing = False
    else:
        sleep(2)


# Start simulation
start_data = {"name": "start"}
sim_start = sim_api.simulations_actions_create(sim_id, data=start_data)

logger.info("Simulation has been started %s", sim_start)

# Wait for simulation to finish
pending = True

while pending:
    latest_sim_status = sim_api.simulations_status_list(sim_id)
    if latest_sim_status.name in [
        "finished",
    ]:
        pending = False
    sleep(5)
logger.info("Simulation has finished")

# Download results
sim_results = sim_api.simulations_results_files_list(sim_id)


def download_file(results, file_name, path):
    results = [x for x in results if x.filename.lower() == file_name.lower()]
    if results:
        # Request 'Download' resource
        download = sim_api.simulations_results_files_download(results[0].id, sim_id)

        with open(path, "wb") as f:
            file_data = requests.get(download.get_url)
            f.write(file_data.content)
        logger.info("Downloaded: %s", file_name)
    else:
        logger.info("Could not download file %s", file_name)


logger.info("Downloading results files")

download_file(
    sim_results.results, "simulation.log", convert_path(r"..\output\simulation.log")
)

# New zipfile with all logs (combined)
download_file(
    sim_results.results,
    f"log_files_sim_{sim_id}.zip",
    convert_path(r"..\output\simulation.zip"),
)

download_file(
    sim_results.results, "flow_summary.log", convert_path(r"..\output\flow_summary.log")
)

download_file(
    sim_results.results, "results_3di.nc", convert_path(r"..\output\results_3di.nc")
)


logger.info("Download of resultfile is succeeded")

# Store saved_state.id
if sim_save_state:
    with open(convert_path(r"..\states\states_3Di.out"), "w") as f:
        f.write("%d" % sim_save_state.id)
        logger.info("Saved state exported: {}".format(sim_save_state.url))


# Read results
results = GridH5ResultAdmin(
    convert_path(r"..\\model\\gridadmin.h5"),
    convert_path(r"..\\output\\results_3di.nc"),
)

times = results.pumps.timestamps[()] + tstart.timestamp()
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
ow_path = r"..\\input\\ow.nc"

# Get all own datetimes in the file
ow_datetimes = get_datetimes_from_source(convert_path(ow_path))

# Figure out which are valid for the given simulation period
# precipation_datetimes
time_indexes = (
    np.argwhere((ow_datetimes >= tstart) & (ow_datetimes <= tend)).flatten().tolist()
)

# Create new file with only time_indexes
create_file_from_source(
    convert_path(ow_path), convert_path(r"..\\output\\ow.nc"), time_indexes
)

dset = netCDF4.Dataset(convert_path(r"..\\output\\ow.nc"), "a")
s1 = results.nodes.subset("2D_OPEN_WATER").timeseries(start_time=0, end_time=endtime).s1
dset["Mesh2D_s1"][:, :] = s1
dset.close()

# Finish
logger.info("Done")
