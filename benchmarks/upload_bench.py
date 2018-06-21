import os
import sys
import json

import perf
import elasticsearch
from perf._formatter import format_datetime

try:
    from urllib import parse as urlparse
except ImportError:
    import urlparse


if __name__ == '__main__':
    files = sys.argv[1:]
    result = []
    for file in files:
        suite = perf.BenchmarkSuite.load(file)
        for bench in suite:
            ncalibration_runs = sum(run._is_calibration() for run in bench._runs)
            nrun = bench.get_nrun()
            loops = bench.get_loops()
            inner_loops = bench.get_inner_loops()
            total_loops = loops * inner_loops
            meta = bench.get_metadata()
            meta['start_date'] = format_datetime(bench.get_dates()[0])
            output = {
                '_index': 'benchmark-agent-python-' + meta['timestamp'].split('T')[0],
                '@timestamp': meta.pop('timestamp'),
                'benchmark': meta.pop('name'),
                'meta': meta,
                'runs': {
                    'calibration': ncalibration_runs,
                    'with_values': nrun - ncalibration_runs,
                    'total': nrun,
                },
                'warmups_per_run': bench._get_nwarmup(),
                'values_per_run': bench._get_nvalue_per_run(),
                'median': bench.median(),
                'median_abs_dev': bench.median_abs_dev(),
                'mean': bench.mean(),
                'mean_std_dev': bench.stdev(),
                'primaryMetric': {
                    'score': bench.mean(),
                    'stdev': bench.stdev(),
                    'scorePercentiles': {},
                },
            }
            for p in (0, 5, 25, 50, 75, 95, 100):
                output['primaryMetric']['scorePercentiles']['%.1f' % p] = bench.percentile(p)
            result.append(output)
    host_url = os.environ['ES_HOST']
    if '@' not in host_url and 'ES_USER' in os.environ:
        parts = urlparse.urlparse(host_url)
        host_url = '%s://%s:%s@%s%s' % (
            parts.scheme,
            os.environ['ES_USER'],
            os.environ['ES_PASSWORD'],
            parts.netloc,
            parts.path,
        )
    es = elasticsearch.Elasticsearch([host_url])
    for b in result:
        es.index(doc_type='doc', body=b, index=b.pop('_index'))

