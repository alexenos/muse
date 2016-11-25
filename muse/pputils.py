#! /usr/bin/env python

"""
Frequently-used simulation post-processing functions
"""
from __future__ import print_function
from builtins import str

import sys
import os
import re


def end_script(status):
    """ Ends the script, most likely due to a failure condition """
    if status is not 0:
        print("Failure occurred: " + str(status))
    sys.exit(status)


def get_vars_h5(lfile):
    import h5py
    """ Gets the variables logged from a hdf5 file """
    try:
        raw = h5py.File(lfile, 'r')
    except:
        print("Error: File could not be read: " + lfile)
        return
    return list(raw.keys())


def get_vars_header(lfile):
    """ Gets the variables logged from a csv/h5 header file """
    # Get variable list
    vlist = []
    with open(lfile) as fh:
        for line in fh:
            vlist.append(line.split()[-1])
    # Get extension
    ext = ".h5"
    if vlist[0] == "ASCII":
        ext = ".csv"
    elif vlist[0] == "HDF5":
        ext = ".h5"
    else:  # Unsupported type
        pass
    return vlist[1:], ext  # First line is a header line of sorts


def get_vars_csv(lfile):
    import pandas as pd
    """ Gets the variables logged from a csv file """
    try:
        raw = pd.read_csv(lfile, header=0, index_col=0)
    except:
        print("Error: File could not be read: " + lfile)
        return
    return list(raw.keys())


def extract_csv(args, var, data, lfile):
    """ Extracts data from csv files """
    import pandas as pd
    import numpy as np
    try:
        raw = pd.read_csv(lfile, header=0, index_col=0, dtype=np.float64)
    except:
        print("Error: File could not be read: " + lfile)
        return
    # Get time
    time = np.array(raw.index.get_values())
    # Get data
    for v in var:
        if v not in data:
            if v == 'sys.exec.out.time':
                data[v] = np.array(raw.index.get_values())
            else:
                regex = re.compile(' \{.*\}')
                if regex.search(v):
                    vv = v.split()[0]
                else:
                    regex = re.compile(re.escape(v) + ' \{.*\}')
                    v = [c for c in raw
                         for m in [regex.search(c)] if m]  # Find the firs
                    if not v:
                        continue
                    v = v[0]
                    vv = v.split()[0]
                data[vv] = np.array(raw[v].get_values())
        else:
            continue  # already extracted
    return data, time


def extract_h5(args, var, data, lfile):
    """ Extracts data from hdf5 files """
    import h5py
    import numpy as np
    try:
        raw = h5py.File(lfile, 'r')
    except:
        print("Error: File could not be read: " + lfile)
        return
    # Get time
    time = np.array(raw['sys.exec.out.time'])
    # Get data
    for v in var:
        if v not in data:  # havent extracted yet
            if v in raw:
                data[v] = np.array(raw[v])
            else:
                # if args.verbose :
                # print "Warning: " + v + " not found in " +
                # os.path.basename(lfile)
                continue
        else:
            continue  # already extracted
    raw.close()
    return data, time


def check_monte(loc, runs):
    """ If a MONTE_*/ directory is provided, it goes and gets all the
        sub-RUN directories """
    new_runs = []
    for r in runs:
        if 'MONTE' in r:
            for root, dirs, files in os.walk(os.path.join(loc, r)):
                for d in dirs:
                    if 'RUN' in d:
                        new_runs.append(os.path.join(r, d))
                break  # only goes 1-level deep
        else:
            new_runs.append(r)
    if not new_runs:
        return runs
    return new_runs
