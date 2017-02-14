from __future__ import print_function
from builtins import str
from builtins import range

def generate_plots(args, figs):
    """ Actually generates the plot figures """
    import matplotlib.pyplot as mp
    # General plotting options
    try:
        mp.style.use(args.style)
    except AttributeError:
        print("Info: Style feature requires matplotlib 1.5")

    i = 0
    for f in figs:
        # Create figure
        fig = mp.figure(i)

        # Plot based on type
        if f['type'] == 'default':
            plot_default(args, f)
        elif f['type'] == 'hist' or f['type'] == 'kde':
            plot_stat(args, f)
        elif f['type'] == 'scatter':
            plot_scatter(args, f)
        else:
            plot_default(args, f)

        # Add descriptors
        mp.title(f['figure'])
        mp.xlabel(f['xlabel'])
        mp.ylabel(f['ylabel'])
        if 'xrange' in f:
            mp.xlim(f['xrange'][0], f['xrange'][-1])
        if 'yrange' in f:
            mp.ylim(f['yrange'])
        if args.legend and len(args.runs) < 10:  # Arbitrary supression at 10 runs
            if 'legend' in f:
                mp.legend(f['legend'], loc='best')
            else:
                mp.legend(loc='best')
        # Set options
        mp.tight_layout()
        fig.canvas.mpl_connect('pick_event', onpick)
        i = i + 1

    mp.show()


def onpick(event):
    thisline = event.artist
    label = thisline.get_label()
    print(label)


def plot_default(args, f):
    """ Default matplotlib line plotting """
    import matplotlib.pyplot as mp
    import numpy as np
    # Finally we are plotting something
    x = f['x']['data']
    for yy in f['y']:
        y = yy['data']
        for r in args.runs:
            # Need to handle if a single expression was evaluated as multiple
            # y-values to plot
            l = 1
            if all(isinstance(i, type(np.array([]))) for i in y[r]):
                l = len(y[r])
            for i in range(l):
                if l == 1 and not isinstance(y[r][i], type(np.array([]))):
                    y_i = y[r]
                else:
                    y_i = y[r][i]
                try:
                    mp.plot(x[r], y_i, label=get_label(
                        r, yy['exp'], len(args.runs)), picker=5)
                except:
                    print("\nWarning: x or y could not be plotted:\n" + f['x']['exp'] + " or " + yy['exp'] + " for " + r)
                    if args.verbose:
                        print("x length: " + str(len(x[r])))
                        print("y length: " + str(len(y[r])))
                    continue


def plot_stat(args, f):
    """ Plots a histogram of the data, aggregating all dependent variables
        and runs, the independent variable (if specified) is completely ignored """
    import matplotlib.pyplot as mp
    import numpy as np
    import seaborn as sb
    for yy in f['y']:
        y = yy['data']
        hist_data = []
        for r in args.runs:
            hist_data.append(y[r])
        try:
            if f['type'] == 'hist':
                mp.hist(hist_data)
            if f['type'] == 'kde':
                # sb.kdeplot(np.array(hist_data))
                sb.distplot(np.array(hist_data))
            # Extras
            print("\nFigure: " + f['figure'])
            print("Average: " + str(np.average(hist_data)))
            print("Std Dev.: " + str(np.std(hist_data)))
        except:
            if args.verbose:
                print("\nWarning: histogram could not be plotted for:\n" + yy['exp'])
            continue


def plot_scatter(args, f):
    """ Plots a seaborn jointplot scatter plot of data """
    import matplotlib.pyplot as mp
    import numpy as np
    import seaborn as sb
    x_data = []
    for r in args.runs:
        x_data.append(f['x']['data'][r])
    for yy in f['y']:
        y = yy['data']
        y_data = []
        for r in args.runs:
            y_data.append(y[r])
        try:
            #sb.jointplot(np.array(x_data), np.array(y_data), kind='scatter')
            mp.scatter(np.array(x_data), np.array(y_data))
        except:
            if args.verbose:
                print("\nWarning: scatter could not be plotted for:\n" + yy['exp'])
            continue


def get_label(r, y, num):  # TODO: this needs to get better
    """ Determines a label to attach to the line on the plot """
    if num > 1:
        lbl = r
    else:
        lbl = y.split('.')[-1]
    return lbl
