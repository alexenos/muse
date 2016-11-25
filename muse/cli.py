#! /usr/bin/env python
# PYTHON_ARGCOMPLETE_OK

"""
Visualizing simulation data should be beautiful, efficient, quick and easy

Muse provides an easy interface for quickly understanding new development
but has extensive features to produce presentation-ready figures

* Command-line plotting
* Format-file figure definitions
* Simple math operations
* Variable array/vector plotting
* Monte-carlo plotting
* Tab-complete, TODO

Let muse be yours
"""
from __future__ import print_function
from __future__ import absolute_import
from __future__ import division
from builtins import str
from builtins import range
from past.utils import old_div

import sys
import os
import re
import argparse as ap
from . import pputils as pp
from .plot import generate_plots

from timeit import default_timer as timer


def main():
    """ Top-level function for executing script """
    # Parse user arguments and options
    args = parse_user_args()
    # Timing to identify slow parts
    args.time = timer()
    # Sanity check user arguments and options
    sanity_check(args)
    # If a monte-carlo run was specified, get all sub-runs
    args.runs = pp.check_monte(args.sim, args.runs)
    # Get a list of all logged variables and what log they are in
    logs, lvars = get_logged_vars(args)
    # Get figure/plot specification information
    figs = get_figures(args)
    # Get list of variable to plot in figures
    pvars = get_plot_vars(args, figs, lvars)
    # Find smallest number of logs to get all variables
    loglist = get_logs(args, logs, pvars)
    # Extract data for plotting
    rdata, time = extract_data(args, pvars, loglist)
    # Process data and apply any simple-math operations
    figs = process_data(args, figs, rdata, time)
    # Generate plots!
    generate_plots(args, figs)
    if args.verbose:
        print("\nTiming: generate_plots at " + str(timer() - args.time))
        args.time = timer()
    return 0


def sanity_check(args):
    """ Sanity checks arguments prior to executing functionality """
    # Sim directory existence
    sdir = os.path.join(args.sim, args.sim)
    if not os.path.isdir(sdir):
        print("\nDoes not exist: " + sdir)
        pp.end_script(-1)
    # Run director(ies) existence
    for r in args.runs:
        rdir = os.path.join(args.sim, r)
        if not os.path.isdir(rdir):
            print("\nDoes not exist: " + rdir)
            pp.end_script(-1)
    # Format file(s) existence
    for y in args.yml:
        yfile = os.path.join(args.ploc, y)
        if not os.path.isfile(yfile):
            print("\nDoes not exist: " + yfile)
            pp.end_script(-1)
    # Check log file(s) existence
    for r in args.runs:
        for l in args.log:
            lfile = os.path.join(args.sim, r, l)
            if not os.path.isfile(lfile):
                print("\nDoes not exist: " + lfile)
                pp.end_script(-1)
    if args.verbose:
        print("\nTiming: sanity_check at " + str(timer() - args.time))
        args.time = timer()


def get_figures(args):
    """ Gets all the data necessary to generate the figures """
    import yaml as yml
    figs = []
    # Parse yaml format files
    for yf in args.yml:  # for each format file
        with open(os.path.join(args.ploc, yf), 'r') as yh:
            try:
                yfh = yml.load(yh)
            except:
                print("Error: Unable to load yaml plot defintion file " + yf)
        for fg in range(0, len(yfh)):
            figs.append(yfh[fg])
    # Command line
    if len(args.var) > 0:
        figs.append(get_fig_info_cl(args.var))
    if args.verbose:
        print("\nTiming: get_figures at " + str(timer() - args.time))
        args.time = timer()
    return figs


def get_fig_info_cl(var):
    """ Simple extract of figure information from command-line """
    fig = {}
    if len(var) < 2:  # Only 1 variable
        fig['x'] = 'sys.exec.out.time'
        fig['y'] = var
    else:
        fig['x'] = var[0]
        fig['y'] = var[1:]
    fig['figure'] = fig['y'][0]
    fig['xlabel'] = fig['x']
    fig['ylabel'] = fig['y'][0]
    return fig


def get_logged_vars(args):
    """ Composes a list of all variables logged in the run(s) """
    lvars = set(['sys.exec.out.time'])  # List of all unique variables logged
    logs = {}  # Dictionary of log files and the variable logged within

    # Major assumption is that all comparable runs log all the same variables
    run = args.runs[0]

    # Identity log files
    find_all = False
    root = os.path.join(args.sim, run)
    files = []
    if args.log:  # Only variables in specific log files
        files = args.log
        find_all = False
    else:  # Find all logged variables
        files = os.listdir(root)
        find_all = True

    # Get variabls in log files
    for f in files:
        fpath = os.path.join(root, f)
        name, ext = os.path.splitext(fpath)
        name = os.path.basename(name)
        log_var_list = []
        if ext == ".header" and find_all:
            log_var_list, ext = pp.get_vars_header(fpath)
        elif ext == ".h5" and not find_all:
            log_var_list = pp.get_vars_h5(fpath)
        elif ext == ".csv" and not find_all:
            log_var_list = pp.get_vars_csv(fpath)
        else:
            continue
        lfile = name + ext
        if not log_var_list:
            if args.verbose:
                print("\nWarning: log file is empty or unsupported: " + lfile)
        log_var_list.append('sys.exec.out.time')  # Everyone has time
        logs[lfile] = log_var_list
        lvars = lvars.union(logs[lfile])

    if not list(logs.keys()) or not list(lvars):
        print("\nError: No data logged: " + run)
        pp.end_script(-1)

    if args.verbose:
        print("\nTiming: get_logged_vars at " + str(timer() - args.time))
        args.time = timer()

    return logs, list(lvars)


def get_plot_vars(args, figs, lvars):
    """ Composes a list of unique variables to extract from the logs """
    varset = set([])
    found_time = False
    for fg in figs:
        if 'x' in fg:
            varset = varset.union(var_parse(fg['x'], lvars))
        else:  # Defaults to time
            fg['x'] = 'sys.exec.out.time'
            if not found_time:
                found_time = True
                varset = varset.union(var_parse(fg['x'], lvars))
        if 'y' in fg:
            if type(fg['y']) == type([]):
                for y in fg['y']:
                    varset = varset.union(var_parse(y, lvars))
            else:
                varset = varset.union(var_parse(fg['y'], lvars))
        else:
            print("\nError: No dependent variables specified: " + fg['figure'])
            pp.end_script(-1)

    if args.verbose:
        print("\nInfo: Variables to plot:")
        print(list(varset))
    if args.verbose:
        print("\nTiming: get_plot_vars at " + str(timer() - args.time))
        args.time = timer()

    return list(varset)


def var_parse(exp, lvars):
    """ Parses variable expressions and checks that variables are logged """
    # Checks for non-string expressions
    if type(exp) != type(str('')):  # No need to parse numeric values
        return list([])  # return null list
    # Get rid of all whitespace in expression
    exp = exp.replace(" ", "")
    # Split on:
    # * basic operators: + * - / ( )
    # * numbers, if they are not preceeded with a "word"-style character set
    #   and are not followed by a ] character or a number and ]
    # * period, if preceeded by a number and followed by a number
    evars = re.split(
        r'[+*\-/()]+|(?<!\w)(\d+|(\.\d+))(?!\d|])|(?<=\d)[.](?=\d)', exp)
    # Filter out null strings
    evars = [_f for _f in evars if _f]
    # Gets rid of strings that are not logged variables, such as simple operators
    # but keeps variables if they just have indicies at the end
    evarset = set(evars)
    evarset1 = set([v for v in lvars if evarset.intersection(
        [_f for _f in re.split(r'\[\d+\]| \{.*\}', v) if _f])])
    evarset2 = evarset.intersection(lvars)
    evarset = evarset1.union(evarset2)
    if evars and not evarset:
        print("\nWarning: variables not logged:")
        print(evars)
    return list(evarset)


def get_logs(args, logs, pvars):
    """ Finds the minimum global interesection of the variables to plot and the log
        files available """
    logset = set([])
    # Create dictionary of log files for every variable to plot
    vldict = {}
    for v in pvars:
        vldict[v] = [l for l in logs if v in logs[l]]
        if not vldict[v]:
            print("\nError: variable not found in specified logs: " + v)
            pp.end_script(-1)  # Maybe not end it for MC runs? TODO
    if args.verbose:
        print("\nInfo: Variables and their logs:")
        print(vldict)

    # Find lowest common denominator of log files
    for i in range(0, len(vldict)):
        v = list(vldict.keys())[i]
        vl = set(vldict[v])
        for j in range(i + 1, len(vldict)):
            u = list(vldict.keys())[j]
            ul = set(vldict[u])
            if not vl == ul:
                ls = vl.intersection(ul)
                if not ls:
                    if not logset.intersection(vl):
                        logset.update(vl)
                    if not logset.intersection(ul):
                        logset.update(ul)
                else:
                    logset.update(ls)
            else:
                logset.update(ul)
                continue  # next one
    # Prioritize hdf5 files
    loglist = list(logset)
    loglist.sort(key=lambda l: os.path.splitext(l)[1], reverse=True)

    if not loglist:
        print("\nWarning: No logs found to plot desired variables")

    if args.verbose:
        print("\nInfo: Logs to plot from: ")
        print(loglist)
    if args.verbose:
        print("\nTiming: get_logs at " + str(timer() - args.time))
        args.time = timer()

    return loglist


def extract_data(args, pvars, loglist):
    """ Extracts all data for variables to plot """
    data = {}
    time = {}
    for r in args.runs:
        data[r] = {}
        time[r] = {}
        # Extract based on file type
        for l in loglist:
            lfile = os.path.join(args.sim, r, l)
            name, ext = os.path.splitext(lfile)
            if ext == '.h5':
                data[r], time[r][l] = pp.extract_h5(
                    args, pvars, data[r], lfile)
            elif ext == '.csv':
                data[r], time[r][l] = pp.extract_csv(
                    args, pvars, data[r], lfile)
            else:
                print("\nOnly csv and hdf5 is supported, not: " + l)
                pp.end_script(-1)

    if args.verbose:
        print("\nTiming: extract_data at " + str(timer() - args.time))
        args.time = timer()

    return data, time


def process_data(args, figs, rdata, time):
    """ Preps data for generating plots, including evaluating simple math """
    from . import simple_math as sm
    fout = []
    for f in figs:

        # Start constructing the massive, all inclusive fout
        # list of dictionaries of data and stuff for each figure
        fig = {}
        fig['x'] = {'exp': f['x'], 'data': {}}
        fig['y'] = []
        if type(f['y']) == type([]):
            for y in f['y']:
                fig['y'].append({'exp': y, 'data': {}})
        else:
            fig['y'].append({'exp': f['y'], 'data': {}})

        if not f['figure']:
            fig['figure'] = f['y'][-1] if type(f['y']) == type([]) else f['y']
        else:
            fig['figure'] = f['figure']
        if 'xlabel' in f:
            fig['xlabel'] = f['xlabel']
        else:
            fig['xlabel'] = f['x']
        if 'ylabel' in f:
            fig['ylabel'] = f['ylabel']
        else:
            fig['ylabel'] = f['y'][-1] if type(f['y']) == type([]) else f['y']
        if 'xrange' in f:
            fig['xrange'] = f['xrange']
        if 'yrange' in f:
            fig['yrange'] = f['yrange']
        if 'type' in f:
            fig['type'] = f['type']
        else:
            fig['type'] = 'default'
        if 'legend' in f:
            fig['legend'] = f['legend']
            args.legend = True
        # Add new features here

        # Process data
        for r in args.runs:
            # Scale variables for single length: TODO: Maybe not all variables?
            rdata[r], length = variable_meld(args, rdata[r], time[r])
            # Evaluate all figure expressions
            fig['x']['data'][r], data_sets = sm.evaluate(
                fig['x']['exp'], rdata[r], length)
            for y in fig['y']:
                y['data'][r], data_sets = sm.evaluate(
                    y['exp'], rdata[r], length)
                # TODO: need vector expression support here

        # Append figure to fout
        fout.append(fig)

    if args.verbose:
        print("\nTiming: process_data at " + str(timer() - args.time))
        args.time = timer()

    return fout


def variable_meld(args, data, time):
    """ Makes all variables the same length pseudo-intelligently """
    import numpy as np
    # Checks
    if not list(time.keys()):  # Nothing logged...
        return data, 1
    n = len(time[list(time.keys())[0]])
    # Check if everything is already the same length
    if all(len(time[t]) == n for t in time):
        return data, n
    else:  # We get to have fun!
        # Find the maximum, we never want to lose fidelity
        n = max(len(time[t]) for t in time)
        # Meld data
        for v in data:
            m = len(data[v])
            if m <= 1:
                print("Error: Could not meld variable because there is no data")
                pp.end_script(-1)
            if n == m:  # same length?
                continue  # next variable
            else:  # meld this variable to the new, correct length
                mlt = old_div((n - 1), (m - 1))
                mod = (n - 1) % (m - 1) + 1
                # Handle multiple of new length
                if mlt > 1:  # interpolate
                    y = []
                    x = list(range(mlt))
                    xp = [0, mlt - 1]
                    for i in range(1, m):
                        y.extend(
                            np.interp(x, xp, [data[v][i - 1], data[v][i]]))
                    data[v] = y
                elif mlt > 0:
                    print("\nError: Didnt find the max... " + str(m) + " > " + str(n) + " ?")
                    pp.end_script(-1)
                elif mlt <= 0:
                    print("\nError: Cannot meld variable: " + v)
                    print("Meld conditions:\nn = " + str(n) + "\nm = " + str(m))
                    print("mlt = " + str(mlt))
                    print("mod = " + str(mod))
                    pp.end_script(-1)
                else:
                    pass  # mlt == 1, so that isnt the issue here
                # Handle modulus of new length
                if mod > 0:
                    # Putting these extra steps almost at the end...
                    # this makes the variable step get geometrically
                    # smaller between the second to last step and the last step
                    x = 0.5
                    xp = list(range(2))
                    last_index = len(data[v]) - 1
                    index = list(range(last_index, last_index + mod))
                    for i in index:
                        data[v].insert(i, np.interp(
                            x, xp, [data[v][i - 1], data[v][i]]))
                elif mod < 0:
                    print("\nError: Cannot meld variable: " + v)
                    pp.end_script(-1)
                else:
                    pass  # do nothing!
                # Check
                if len(data[v]) != n:
                    print("\nError: Melding did not work! " + str(len(data[v])) + " != " + str(n))
                    print("Meld conditions:\nn = " + str(n) + "\nm = " + str(m))
                    print("mlt = " + str(mlt))
                    print("mod = " + str(mod))
                    pp.end_script(-1)
    return data, n


def complete_variable(prefix, parsed_args, **kwargs):
    logs, lvars = get_logged_vars(parsed_args)
    last = prefix.split(" ")[-1]
    return [var for var in lvars if var.startswith(last)]


def parse_user_args():
    """ Parses the user arguments and options for the script """
    try:
        import argcomplete
        has_ac = True
    except ImportError:
        has_ac = False

    parser = ap.ArgumentParser(description="muse: plotting made beautifully easy",
                               formatter_class=ap.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-r', '--runs', help="List of RUN/MONTE directory(ies) of data",
                        nargs='+', type=str, default=['RUN_airdrop'])
    parser.add_argument('-y', '--yml', help="List of YAML plot format files",
                        nargs='+', type=str, default=[])
    parser.add_argument('-v', '--var', help="List of variables to plot from command line. First variable is x if more than one variable is listed, otherwise variables are y.",
                        nargs='+', type=str,  default=[]).completer = complete_variable
    parser.add_argument('-l', '--log', help="Restricted list of log files, otherwise script finds all available",
                        nargs='+', type=str,  default=[])
    parser.add_argument('--legend', help="Adds a legend to the plot",
                        default=False, action='store_true')
    parser.add_argument('--style', help="Sets the style for the plots",
                        default='classic')
    parser.add_argument('-s', '--sim', type=str, help="Location of RUN/MONTE directory(ies) of interest",
                        default=os.path.join(os.getenv('SISU'), 'sims/SIM_alpha'))
    parser.add_argument('-p', '--ploc', type=str,  help="Location of yaml plot file(s) of interest",
                        default=os.path.join(os.getenv('SISU'), 'sims/SIM_alpha/muse_plots'))
    parser.add_argument('--verbose', help="Verbose command-line output for diagnostics",
                        default=False, action='store_true')
    if has_ac:
        argcomplete.autocomplete(parser)
    return parser.parse_args()

if __name__ == '__main__':
    sys.exit(main())
