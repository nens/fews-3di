import os
import xml.etree.ElementTree as ET
from datetime import datetime


def settings(settingsfile):

    ## read settings file
    #global user, password, model_rev, sim_name, state_file, tstart, duration
    tstart, tend = '',''
    user, password, organisation, model_rev, sim_name, state_file \
          , save_state, save_state_expirytime = '','','','','','',False,''
    #tree = ET.parse(r"..\run_info.xml")
    tree = ET.parse(settingsfile)
    root = tree.getroot()
    children = root.getchildren()
    for child in children:
        #ET.dump(child)
        tstart = child.attrib['date']+'T'+child.attrib['time']+'Z' \
                if child.tag[-13:] == 'startDateTime' else tstart
        tend = child.attrib['date']+'T'+child.attrib['time']+'Z' \
                if child.tag[-11:] == 'endDateTime' else tend
        if child.tag[-10:] == 'properties':
            for i in range(len(child)):
                try:
                    user = child[i].attrib['value'] if child[i].attrib['key'] == 'username' else user
                except:
                    continue
                try:
                    password = child[i].attrib['value'] if child[i].attrib['key'] == 'password' else password
                except:
                    continue
                try:
                    organisation = child[i].attrib['value'] if child[i].attrib['key'] == 'organisation' else organisation
                except:
                    continue
                try:
                    model_rev = child[i].attrib['value'] if child[i].attrib['key'] == 'modelrevision' else model_rev
                except:
                    continue
                try:
                    sim_name = child[i].attrib['value'] if child[i].attrib['key'] == 'simulationname' else sim_name
                except:
                    continue
                try:
                    state_file = child[i].attrib['value'] if child[i].attrib['key'] == 'use_state' else state_file
                except:
                    continue
                try:
                    save_state = child[i].attrib['value'] if child[i].attrib['key'] == 'save_state' else save_state
                except:
                    continue
                try:
                   save_state_expirytime = child[i].attrib['value'] if child[i].attrib['key'] == 'save_state_expiry_days' else save_state
                except:
                    continue


    # calcute duration of simulation
    t0 = datetime.strptime(tstart, '%Y-%m-%dT%H:%M:%SZ')
    t1 = datetime.strptime(tend, '%Y-%m-%dT%H:%M:%SZ')
    duration = int((t1-t0).total_seconds())

    return user, password, organisation, model_rev, sim_name, state_file, save_state \
           , save_state_expirytime, t0, duration
