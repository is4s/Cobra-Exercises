from pathlib import Path
from pntos.cobra.utils import run_pntos_with_log_transport


def test_zupt_stub() -> None:
    # just make sure the app can run to completion
    run_pntos_with_log_transport(Path('exercises/zupt_exercise/zupt_app.py'))


def test_zupt_sol() -> None:
    # just make sure the app can run to completion
    run_pntos_with_log_transport(Path('.details/zupt_exc_ans/zupt_app.py'))


def test_pos_baro_stub() -> None:
    # just make sure the app can run to completion
    run_pntos_with_log_transport(Path('exercises/new_app_exercise/pos_baro_app.py'))


def test_pos_baro_sol() -> None:
    # just make sure the app can run to completion
    run_pntos_with_log_transport(Path('.details/new_app_exc_ans/pos_baro_app.py'))


def test_direction_stub() -> None:
    # TODO I don't think this does what we want. This exercise raises exceptions but 'passes'.
    run_pntos_with_log_transport(
        Path('exercises/direction_processor_exercise/direction_app.py')
    )
