from pathlib import Path
from pntos.cobra.utils import run_pntos_with_log_transport


def test_zupt_stub() -> None:
    # just make sure the app can run to completion
    run_pntos_with_log_transport(Path('exercises/zupt_exercise/zupt_app.py'))


def test_zupt_sol() -> None:
    # just make sure the app can run to completion
    run_pntos_with_log_transport(Path('.details/zupt_exc_ans/zupt_app.py'))
