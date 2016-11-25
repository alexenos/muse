"""
Utilities for working with output of sims built in NASA's Trick simulation framework.
"""
from builtins import next
from builtins import range
from builtins import object
import os
import collections
from yaml import YAMLObject

import muse
LOG_PREFIX = 'log_'
HEADER_EXT = '.header'
INDEX_VAR = 'sys.exec.out.time'

LoggedVar = collections.namedtuple('TrickVar', 'log ctype unit name')

class LogFile(object):
    pass

class HdfLogFile(LogFile):
    """
    A Trick-style HDF5 log file. Frustratingly, Trick's style is incompatible with pytables,
    so it is necessary to do a lot by hand.
    """
    def __init__(self, filename):
        self.filename = filename
        self.cache = {}

    def get_var(self, name):
        import h5py
        import pandas as pd
        if not name in self.cache:
            with h5py.File(self.filename, 'r') as hdf_file:
                self.cache[name] = hdf_file[name][:]
        return self.cache[name]

    def get_series(self, name, index=INDEX_VAR):
        import pandas as pd
        return pd.Series(self.get_var(name), index=pd.Index(self.get_var(index), name=index), name=name)

class CsvLogFile(LogFile):
    def __init__(self, filename):
        import pandas as pd
        self.filename = filename
        self.cache    = pd.read_csv(self.filename, index_col=None)
        self.cache.columns = [(name.split('{')[0]).strip() for name in self.cache.columns]

    def get_arr(self, name):
        return self.cache[name].as_matrix()

    def get_series(self, name, index=INDEX_VAR):
        tmp = self.cache.set_index(index)
        return tmp[name]


def map_format(fmt):
    if fmt == 'ASCII':
        return '.csv'
    elif fmt == 'HDF5':
        return '.h5'
    else:
        raise NotImplementedError('Unsupported format: {}'.format(fmt))

def parse_header(fn):
    with open(fn) as fl:
        lines = fl.readlines()

    header = lines[0].split()
    fmt = header[3]

    bn, ext = os.path.splitext(fn)
    try:
        log_fn = bn + map_format(fmt)
    except NotImplementedError:
        return None
    logged_vars = [LoggedVar(*(line.split())) for line in lines[1:]]

    return log_fn, logged_vars

class TrickSim(muse.ContextHandler, YAMLObject):
    """
    A Trick simulation. Contexts within the simulation correspond to runs (single or Monte Carlo) of the simulation.
    """
    yaml_tag = '!trick_sim'

    def __init__(self, sim_dir):
        import os.path
        self.sim_dir = os.path.abspath(sim_dir)

    @classmethod
    def from_yaml(cls, loader, node):
        data = loader.construct_mapping(node)
        # Try to get the file from which this was read
        filename = loader.name
        if not filename in ['<unicode string>', '<string>', '<file>']:
            data['sim_dir'] = os.path.join(os.path.dirname(filename), data['sim_dir'])

        return cls(**data)


    def list_contexts(self):
        all_runs = []
        for (dirpath, dirnames, filenames) in os.walk(self.sim_dir):
            runs = [d for d in dirnames if d.startswith('RUN_')]
            monte_runs = [d for d in dirnames if d.startswith('MONTE_')]
            all_runs.extend([os.path.relpath(os.path.join(dirpath, d), self.sim_dir) for d in runs + monte_runs])
            dirnames = monte_runs
        return all_runs

    def get_context(self, name=None):
        import os
        last_dir = os.path.split(name)[-1]
        if last_dir.startswith('RUN'):
            return SingleRun(self.sim_dir, name)
        else:
            return NotImplementedError

    def __repr__(self):
        return "{}({!r})".format(self.__class__.__name__, self.sim_dir)


class Context(muse.Context):
    """
    A context in which some variables are evaluated. Can be one or more runs.
    """

    def __init__(self):
        self.logs = {}

    def load_log(self, name):
        if name.endswith('h5'):
            self.logs[name] = HdfLogFile(name)
        elif name.endswith('csv'):
            self.logs[name] = CsvLogFile(name)

    def get_log(self, name):
        if name not in self.logs:
            self.load_log(name)
        return self.logs[name]

    def get_var(self, name, index=INDEX_VAR):
        log_fn = next(self.get_var_log(name))
        log = self.get_log(log_fn)
        return log.get_series(name, index)


    def get_variables(self, names, index=INDEX_VAR):
        import pandas as pd
        return pd.concat([self.get_var(n, index) for n in names], axis=1)




class SingleRun(Context, YAMLObject):
    """
    A single run of a Trick simulation
    """
    yaml_tag = '!trick_single_run'

    def __init__(self, sim_dir, run_dir):
        self.logs = {}
        self.sim_dir = os.path.abspath(sim_dir)
        self.run_dir = os.path.abspath(run_dir)

    @classmethod
    def from_yaml(cls, loader, node):
        data = loader.construct_mapping(node)
        # Try to get the file from which this was read
        filename = loader.name
        if not filename in ['<unicode string>', '<string>', '<file>']:
            data['sim_dir'] = os.path.join(os.path.dirname(filename), data['sim_dir'])
            data['run_dir'] = os.path.join(os.path.dirname(filename), data['run_dir'])

        return cls(**data)

    def get_header_fns(self):
        import glob
        search_dir = os.path.join(self.sim_dir, self.run_dir)
        for fn in glob.glob(os.path.join(search_dir, LOG_PREFIX + '*' + HEADER_EXT)):
            yield os.path.join(search_dir, fn)

    def iter_headers(self):
        for fn in self.get_header_fns():
            p = parse_header(fn)
            if p:
                yield p

    def list_variables(self):
       return  [lv.name for log_fn, logged_vars in self.iter_headers() for lv in logged_vars]

    def get_var_log(self, name):
        for log_fn, logged_vars in self.iter_headers():
            if name in [lv.name for lv in logged_vars]:
                yield log_fn


    def __repr__(self):
        return "{}({!r}, {!r})".format(self.__class__.__name__, self.sim_dir, self.run_dir)


class TrickVar(object):

    def __init__(self, name, context, index=INDEX_VAR):
        self.name    = name
        self.context = context
        self.log_fns = self.context.get_var_log(self.name)
        self.log     = self.context.get_log(next(self.log_fns))
        self.index   = index

    def get_arr(self):
        return self.log.get_arr(self.name)

    def get_series(self):
        return self.log.get_series(self.name, self.index)

class TrickVector3Var(TrickVar):

    def __init__(self, name, context, index=INDEX_VAR):
        self.name    = name
        self.context = context
        self.log_fns = self.context.get_var_log(self.name + '[0]')
        self.log     = self.context.get_log(next(self.log_fns))
        self.index   = index
        self._vars   = [TrickVar(self.name + '[{}]'.format(i), self.context) for i in range(3)]

    #def get_arr(self):
    #    import numpy as np
    #    inds = [self.log.get_arr(self.name + '[{}]'.format(i)) for i in range(3)]
    #    return np.vstack(inds)

    def get_values(self):
        import pandas as pd
        df = pd.concat([v.get_series() for v in self._vars], axis=1)
        df.columns = pd.MultiIndex.from_product([[self.name], list(range(3))])
        return df
