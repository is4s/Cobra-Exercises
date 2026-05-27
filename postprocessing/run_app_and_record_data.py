#!/usr/bin/env python3

import argparse
import sys
from pathlib import Path

from plot_results import plot_results
from pntos.cobra.utils.lcm_utils import (
    run_pntos_with_log_transport,
    run_pntos_with_network_transport,
)
from pntos_python_datasets_lcm import EXAMPLE_LCM_LOG

OUTPUT_LOG_PREFIX = 'pntos_output'
OUTPUT_LOG = Path(f'{OUTPUT_LOG_PREFIX}.log')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Run app, record data, and plot results.'
    )
    parser.add_argument('app_to_run', help='Path to app.', type=Path)
    args = parser.parse_args()

    app_to_run: Path = args.app_to_run
    returncode = -1
    if 'lcm_relay' in app_to_run.as_posix():
        returncode = run_pntos_with_network_transport(
            app_to_run, Path(EXAMPLE_LCM_LOG), OUTPUT_LOG, validate=True
        )
    else:
        returncode = run_pntos_with_log_transport(app_to_run, [OUTPUT_LOG.as_posix()])

    if returncode != 0:
        print('App terminated unsuccessfully, will not plot results.')
        sys.exit(1)

    # Tutorial apps include UI plugin which automatically plots upon shutdown, so no need to plot again
    if 'tutorial' not in app_to_run.as_posix():
        if OUTPUT_LOG.exists():
            plot_results(OUTPUT_LOG, '/solution/pntos/pva', '/sensor/ins-d/pva')
        else:
            print(
                f'Cannot plot results. pntOS failed to generate output log "{OUTPUT_LOG}"'
            )
