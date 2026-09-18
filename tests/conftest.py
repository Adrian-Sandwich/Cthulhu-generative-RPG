"""Shared test plumbing.

Every persistence path (saves, playtest archives, feedback) resolves through
core.generative_save.data_root(). Tests pin it to a throwaway directory so no
run can write fixture games into the real repo again (MAGI #42: 126 saves and
6 playtest archives named Tester/Alice/Bob/... were being read as players).
"""

import os

import pytest


@pytest.fixture(scope="session", autouse=True)
def _isolated_data_dir(tmp_path_factory):
    """Point DATA_DIR at a session-wide temp dir for anything that reads env."""
    previous = os.environ.get("DATA_DIR")
    os.environ["DATA_DIR"] = str(tmp_path_factory.mktemp("data"))
    yield
    if previous is None:
        os.environ.pop("DATA_DIR", None)
    else:
        os.environ["DATA_DIR"] = previous

