"""
Defaults handling
"""

import os
import yaml
import six
import muse.trick

DEFAULTS_FILENAME = '.muse'

def path_split_recursive(path):
    """
    >>> path_split_recursive('/home/alphagnc/sisu/sims/SIM_alpha')
    ('/', 'home', 'alphagnc', 'sisu', 'sims', 'SIM_alpha')
    """
    if isinstance(path, six.string_types):
        new_path = os.path.split(path)
        if not new_path[1]:
            return new_path
        else:
            return path_split_recursive(new_path)
    else:
        new_path = os.path.split(path[0])
        if not new_path[1]:
            # TODO: this is a bit ugly
            return tuple(tuple(new_path[0]) + path[1:])
        else:
            return path_split_recursive(tuple(new_path[:] + path[1:]))

def find_defaults_files(start_dir='.'):
    """
    Find defaults files, starting from the root and ending in the current directory.
    """
    abs_path = os.path.abspath(start_dir)
    current_dir = ''
    path_chunks = path_split_recursive(abs_path)
    for dirname in path_chunks:
        current_dir = os.path.join(current_dir, dirname)
        current_fn = os.path.join(current_dir, DEFAULTS_FILENAME)
        if os.path.isfile(current_fn):
            yield current_fn


def load_defaults(start_dir='.'):
    """
    Load all defaults files found, starting from the root and ending in the current directory.
    Places their values in a dictionary, with the later values replacing the earlier.
    """
    defaults_dict = {}
    for defaults_filename in find_defaults_files(start_dir):
        with open(defaults_filename, mode='rb') as defaults_file:
            file_dict = yaml.load(defaults_file)
            if 'defaults' in file_dict:
                for key in file_dict['defaults']:
                    defaults_dict[key] = file_dict['defaults'][key]

    return defaults_dict


if __name__ == "__main__":
    import doctest
    doctest.testmod()
