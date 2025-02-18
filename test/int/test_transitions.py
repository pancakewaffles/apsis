"""
Tests basic transitions by running an Apsis service and interacting with it
via the HTTP client.
"""

from   contextlib import closing
import ora
import pytest
import time

from   instance import ApsisInstance

#-------------------------------------------------------------------------------

@pytest.fixture(scope="module")
def inst():
    with closing(ApsisInstance()) as inst:
        inst.create_db()
        inst.write_cfg()
        inst.start_serve()
        inst.wait_for_serve()
        yield inst


def test_create_adhoc(inst):
    client = inst.client

    # Create and schedule a run.
    res = client.schedule_adhoc("now", {"program": {"type": "no-op"}})
    job_id = res["job_id"]
    run_id = res["run_id"]

    # Check on the adhoc job.
    job = client.get_job(job_id)
    assert job["program"]["type"] == "no-op"

    # Check on the run.
    run = client.get_run(run_id)
    assert run["job_id"] == job_id
    # It should be done.
    assert run["state"] == "success"


def test_skip(inst):
    """
    Schedules a new run for the future and skips it before it runs.
    """
    client = inst.client

    # Create and schedule a run for a minute from now.
    res = client.schedule_adhoc(ora.now() + 60, {"program": {"type": "no-op"}})
    run_id = res["run_id"]

    # It should be scheduled.
    run = client.get_run(run_id)
    assert run["state"] == "scheduled"

    # Skip the run.
    client.skip(run_id)

    # It should be skipped.
    run = client.get_run(run_id)
    assert run["state"] == "skipped"


def test_max_running(inst):
    client = inst.client

    JOB = {
        "program": {
            "type": "no-op",
            "duration": "1",
        },
        "condition": {
            "type": "max_running",
            "count": 1,
        },
    }

    # Create and schedule a run.
    res = client.schedule_adhoc("now", JOB)
    job_id = res["job_id"]
    run_id0 = res["run_id"]

    job = client.get_job(job_id)
    print(job)

    # Schedule a second run with the same (adhoc) job.
    res = client.schedule(job_id, {}, "now")
    run_id1 = res["run_id"]

    # The first job should be running.
    run = client.get_run(run_id0)
    assert run["state"] == "running"

    # The second job should be waiting.
    run = client.get_run(run_id1)
    assert run["state"] == "waiting"

    # Wait and check again.
    time.sleep(1)

    # The first run should have completed and the second started.
    run = client.get_run(run_id0)
    assert run["state"] == "success"
    run = client.get_run(run_id1)
    assert run["state"] == "running"

    # Wait and check again.
    time.sleep(2)

    # The second run should have completed.
    run = client.get_run(run_id1)
    assert run["state"] == "success"


