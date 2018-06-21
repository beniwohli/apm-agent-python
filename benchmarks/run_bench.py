import sys
import os
import operator
import importlib
import pkgutil
import subprocess

import perf

import bm

if __name__ == '__main__':
    sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))
    git_timestamp, git_sha, git_message = subprocess.check_output(
        ['git', 'log', '-1' ,'--pretty=%aI\t%H\t%B']
    ).decode('utf8').split('\t', 2)
    if '--tracemalloc' in sys.argv:
        bench_type = 'malloc'
        bench_unit = 'bytes'
    elif '--track-memory' in sys.argv:
        bench_type = 'mem'
        bench_unit = 'bytes'
    else:
        bench_type = 'time'
        bench_unit = 'seconds'
    runner = perf.Runner(metadata={
        'timestamp': git_timestamp,
        'revision': git_sha,
        'commit_message': git_message.split('\n')[0],
        'unit': bench_unit,
    })
    for importer, modname, is_pkg in sorted(pkgutil.iter_modules(bm.__path__), key=operator.itemgetter(1)):
        if modname.startswith('bm_'):
            bench_module = importlib.import_module('bm.' + modname)
            for func_name in sorted(dir(bench_module)):
                if func_name.startswith('bench_'):
                    runner.bench_func('%s.%s.%s' % (modname, func_name, bench_type), getattr(bench_module, func_name))
