"""
muse object-oriented API
"""
from builtins import object
import abc
import six
import matplotlib
import yaml
from yaml import YAMLObject


class Figure(YAMLObject):
    """
    A muse figure. This corresponds to both a matplotlib Figure and FigureCanvas.
    """
    yaml_tag = '!figure'

    def __init__(self, axes=None, title=None, *args, **kwargs):
        self.axes = axes
        self.title = title

class Axes(YAMLObject):
    """
    A muse axes. This corresponds to a matplotlib axes created explicitly.
    """
    yaml_tag = '!axes'

    def __init__(self, rect=None, projection=None, *args, **kwargs):
        self.rect = rect
        self.projection = projection


class Subplot(YAMLObject):
    """
    A muse subplot. This is really a matplotlib axes, but it's made using add_subplot.
    """
    yaml_tag = '!subplot'

    def __init__(self, nrows=None, ncols=None, plot_number=None, *args, **kwargs):
        self.nrows = nrows
        self.ncols = ncols
        self.plot_number = plot_number


class Plot(YAMLObject):
    """
    A muse high-level plot object.
    """
    yaml_tag = '!plot'

    def __init__(self, x=None, y=None, xlabel=None, ylabel=None, title=None, *args, **kwargs):
        self.x = x
        self.y = y
        self.xlabel = xlabel
        self.ylabel = ylabel
        self.title = title



class Kde(YAMLObject):
    """
    A muse high-level kernel density estimate plot object
    """
    yaml_tag = '!kde'

    def __init__(self, y=None, xlabel=None, ylabel=None, title=None, *args, **kwargs):
        self.y = y
        self.xlabel = xlabel
        self.ylabel = ylabel
        self.title = title


class Expression(YAMLObject):
    """
    A mathematical expression.
    """
    pass

class yaml_abc(abc.ABCMeta, yaml.YAMLObjectMetaclass):
    """
    Combined metaclass so objects inherited from abc's can also inherit from YAMLObject
    """
    pass


@six.add_metaclass(yaml_abc)
class ContextHandler(object):
    """
    A ContextHandler is responsible for enumerating and returning Contexts.
    """

    @abc.abstractmethod
    def list_contexts(self):
        """
        List the available Contexts
        """
        pass

    @abc.abstractmethod
    def get_context(self, name=None):
        """
        Get a Context object by name.
        """
        pass


@six.add_metaclass(yaml_abc)
class Context(object):
    """
    The context in which to interpret some Expressions. In many cases, a Context will correspond to a
    run of a simulation.
    """

    @abc.abstractmethod
    def list_variables(self):
        """
        List the variables available in the Context.
        """
        pass

    @abc.abstractmethod
    def get_variables(self, names):
        """
        Get the variables requested
        """
        pass
