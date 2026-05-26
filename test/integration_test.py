from pathlib import Path
from pntos.cobra.utils import run_pntos_with_log_transport


def test_zupt_stub() -> None:
    # just make sure the app can run to completion
    run_pntos_with_log_transport(
        Path('exercises/zupt_exercise/zupt_app.py'), validate=True
    )


def test_zupt_sol() -> None:
    # just make sure the app can run to completion
    run_pntos_with_log_transport(
        Path('.details/zupt_exc_ans/zupt_app.py'), validate=True
    )


def test_pos_baro_stub() -> None:
    # just make sure the app can run to completion
    run_pntos_with_log_transport(
        Path('exercises/new_app_exercise/pos_baro_app.py'), validate=True
    )


def test_pos_baro_sol() -> None:
    # just make sure the app can run to completion
    run_pntos_with_log_transport(
        Path('.details/new_app_exc_ans/pos_baro_app.py'), validate=True
    )


def test_direction_sol() -> None:
    run_pntos_with_log_transport(
        Path('.details/direction_exc_ans/direction_app.py'), validate=True
    )
