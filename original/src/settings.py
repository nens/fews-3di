"""Comments by Reinout

- Horrible bare try/excepts that can hide any manner of errors.

- I think an ini file would be a better/clearer/easier choice. Part of the
  elaborateness of this file is due to using xml, I fear.

- Don't return a list of values, but a much clearer dict or so.

"""
from datetime import datetime

import xml.etree.ElementTree as ET


def settings(settingsfile):

    # # read settings file
    # global user, password, model_rev, sim_name, state_file, tstart, duration
    tstart, tend = "", ""
    (
        user,
        password,
        organisation,
        model_rev,
        sim_name,
        state_file,
        save_state,
        save_state_expirytime,
    ) = ("", "", "", "", "", "", False, "")
    # ^^^ defaults

    # tree = ET.parse(r"..\run_info.xml")
    tree = ET.parse(settingsfile)
    root = tree.getroot()
    children = root.getchildren()
    for child in children:
        # ET.dump(child)
        tstart = (
            child.attrib["date"] + "T" + child.attrib["time"] + "Z"
            if child.tag[-13:] == "startDateTime"
            else tstart
        )
        tend = (
            child.attrib["date"] + "T" + child.attrib["time"] + "Z"
            if child.tag[-11:] == "endDateTime"
            else tend
        )
        if child.tag[-10:] == "properties":
            for i in range(len(child)):
                # TODO: remove bare try/except
                user = (
                    child[i].attrib["value"]
                    if child[i].attrib["key"] == "username"
                    else user
                )
                password = (
                    child[i].attrib["value"]
                    if child[i].attrib["key"] == "password"
                    else password
                )
                organisation = (
                    child[i].attrib["value"]
                    if child[i].attrib["key"] == "organisation"
                    else organisation
                )
                model_rev = (
                    child[i].attrib["value"]
                    if child[i].attrib["key"] == "modelrevision"
                    else model_rev
                )
                sim_name = (
                    child[i].attrib["value"]
                    if child[i].attrib["key"] == "simulationname"
                    else sim_name
                )
                state_file = (
                    child[i].attrib["value"].replace("\\", "/")
                    if child[i].attrib["key"] == "use_state"
                    else state_file
                )
                save_state = (
                    child[i].attrib["value"]
                    if child[i].attrib["key"] == "save_state"
                    else save_state
                )
                save_state_expirytime = (
                    child[i].attrib["value"]
                    if child[i].attrib["key"] == "save_state_expiry_days"
                    else save_state
                )

    # calcute duration of simulation
    t0 = datetime.strptime(tstart, "%Y-%m-%dT%H:%M:%SZ")
    t1 = datetime.strptime(tend, "%Y-%m-%dT%H:%M:%SZ")
    duration = int((t1 - t0).total_seconds())

    return (
        user,
        password,
        organisation,
        model_rev,
        sim_name,
        state_file,
        save_state,
        save_state_expirytime,
        t0,
        duration,
    )
