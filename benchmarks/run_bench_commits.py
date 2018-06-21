import codecs
import json
import os
import shutil
import subprocess
import sys

try:
    from urllib.request import Request, urlopen
except ImportError:
    from urllib2 import Request, urlopen

BASE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
WORKTREE = 'benchmarking_worktree'


def get_commit_list(commit_range):
    commits = subprocess.check_output(['git', 'log', "--pretty=%h", commit_range]).decode('utf8')
    commits = commits.split('\n')[:-1]
    commits.reverse()
    return commits


def run_benchmark(commit_hash):
    # clean up from former runs
    if os.path.exists('.benchmarks'):
        shutil.rmtree('.benchmarks')
    if os.path.exists('benchmarks'):
        shutil.rmtree('benchmarks')
    subprocess.check_output(['git', 'checkout', 'elasticapm/base.py'])
    subprocess.check_output(['git', 'checkout', commit_hash])
    # copy newest benchmarks into work tree
    shutil.copytree(
        os.path.join(BASE_PATH, 'benchmarks'),
        'benchmarks'
    )
    # set the timer thread to deamon, this fixes an issue with the timer thread
    # not exiting in old commits
    subprocess.check_output("sed -i '' -e 's/self\._send_timer\.start/self\._send_timer\.daemon=True; self\._send_timer\.start/g' elasticapm/base.py", shell=True)
    output_files = []
    for bench_type, flag in (('time', None), ('tracemalloc', '--tracemalloc')):
        output_file = 'result.%s.%s.json' % (bench_type, commit_hash)
        test_cmd = ['python', 'benchmarks/run_bench.py', '-o', output_file]
        if flag:
            test_cmd.append(flag)
        print(' '.join(test_cmd))
        subprocess.check_output(
            test_cmd,
            stderr=subprocess.STDOUT,
        )
        output_files.append(output_file)
    shutil.rmtree(os.path.join('benchmarks'))
    subprocess.check_output(['git', 'checkout', 'elasticapm/base.py'])
    return output_files


if __name__ == '__main__':
    base_branch, commit_range, es_host = sys.argv[1:]
    os.chdir(BASE_PATH)
    if not os.path.exists(WORKTREE):
        subprocess.check_output(['git', 'worktree', 'add', WORKTREE])
    os.chdir(WORKTREE)
    subprocess.check_output(['git', 'checkout', 'elasticapm/base.py'])
    subprocess.check_output(['git', 'checkout', base_branch])
    commits = get_commit_list(commit_range)
    for commit in commits:
        json_files = run_benchmark(commit)
