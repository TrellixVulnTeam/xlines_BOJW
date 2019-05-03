"""
Summary.

    Multiprocessing module for line count

Module Functions:


"""
import os
import multiprocessing
from multiprocessing import Queue
from pyaws.utils import stdout_message, export_json_object
from pyaws.colors import Colors
from xlines.common import BUFFER, acct, bwt, text, rst, arrow, div
from xlines.statics import local_config
from xlines.common import locate_fileobjects, remove_illegal, linecount, print_header, print_footer


def longest_path_mp(object_list):
    longest = 0
    for path_dict in object_list:
        if len(path_dict['path']) > longest:
            longest = len(path_dict['path'])
    return longest


def mp_linecount(path, exclusions):
    """Multiprocessing line count"""
    p = path
    try:
        if os.path.isfile(path):
            q.put({
                    'path': os.path.abspath(path),
                    'count': linecount(path)
                }
            )

        elif os.path.isdir(path):
            d = locate_fileobjects(path)
            valid_paths = remove_illegal(d, exclusions)
            for p in valid_paths:
                q.put({'path': p, 'count': linecount(p)})
    except UnicodeDecodeError:
        q.put({'path': p, 'count': None})
        return


def print_results(object_list):

    tcount, tobjects = 0, 0
    io_fail = []
    width = longest_path_mp(object_list)

    print_header(width)
    count_width = local_config['PROJECT']['COUNT_COLUMN_WIDTH']
    hicount_threshold = local_config['PROJECT']['COUNT_THRESHOLD']

    for object_dict in object_list:

        try:
            path = object_dict['path']
            inc = object_dict['count']
            highlight = acct if inc > hicount_threshold else Colors.AQUA
            tcount += inc    # total line count
            tobjects += 1    # increment total number of objects

            # truncation
            lpath = os.path.split(path)[0]
            fname = os.path.split(path)[1]

            if width < (len(lpath) + len(fname)):
                cutoff = (len(lpath) + len(fname)) - width
            else:
                cutoff = 0

            tab = '\t'.expandtabs(width - len(lpath) - len(fname) - count_width + BUFFER)
            tab4 = '\t'.expandtabs(4)

            # with color codes added
            if cutoff == 0:
                lpath = text + lpath + rst
            else:
                lpath = os.path.split(path)[0][:cutoff] + arrow

            fname = highlight + fname + rst

            # incremental count formatting
            ct_format = acct if inc > hicount_threshold else bwt

            output_str = f'{tab4}{lpath}{div}{fname}{tab}{ct_format}{"{:,}".format(inc):>7}{rst}'
            print(output_str)
        except Exception:
            io_fail.append(path)
            continue

    print_footer(tcount, tobjects, width)
    return True


def multiprocessing_main(container, exclusions, debug):
    """Execute Operations using concurrency (multi-process) model"""

    global q
    q = Queue()

    processes = []
    for i in container:
        t = multiprocessing.Process(target=mp_linecount, args=(i, exclusions.types))
        processes.append(t)
        t.start()

    for one_process in processes:
        one_process.join()

    results = []
    while not q.empty():
        results.append(q.get())

    print_results(results)

    if debug:
        export_json_object(results, logging=False)
        stdout_message(message='Num of objects: {}'.format(len(results)))
    return 0
