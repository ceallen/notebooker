import json
import mock
import time


def test_create_schedule(flask_app, setup_workspace):
    with flask_app.test_client() as client:
        rv = client.post(
            "/scheduler/create/fake/report",
            data={
                "report_title": "test2",
                "report_name": "fake/report",
                "overrides": "",
                "mailto": "",
                "cron_schedule": "* * * * *",
            },
        )
        assert rv.status_code == 201
        data = json.loads(rv.data)
        assert data.pop("next_run_time")
        assert data == {
            "cron_schedule": "* * * * *",
            "delete_url": "/scheduler/fake/report_test2",
            "id": "fake/report_test2",
            "params": {
                "generate_pdf": False,
                "hide_code": False,
                "mailto": "",
                "overrides": "",
                "report_name": "fake/report",
                "report_title": "test2",
                "scheduler_job_id": "fake/report_test2",
            },
            "trigger": {
                "fields": {
                    "day": ["*"],
                    "day_of_week": ["*"],
                    "hour": ["*"],
                    "minute": ["*"],
                    "month": ["*"],
                    "second": ["0"],
                    "week": ["*"],
                    "year": ["*"],
                }
            },
        }


def test_create_schedule_bad_report_name(flask_app, setup_workspace):
    with flask_app.test_client() as client:
        rv = client.post(
            "/scheduler/create/fake2",
            data={
                "report_title": "test2",
                "report_name": "fake2",
                "overrides": "",
                "mailto": "",
                "cron_schedule": "* * * * *",
            },
        )
        assert rv.status_code == 404


def test_list_scheduled_jobs(flask_app, setup_workspace):
    with flask_app.test_client() as client:
        rv = client.post(
            "/scheduler/create/fake/report",
            data={
                "report_title": "test2",
                "report_name": "fake/report",
                "overrides": "",
                "mailto": "",
                "cron_schedule": "* * * * *",
            },
        )
        assert rv.status_code == 201

        rv = client.get("/scheduler/jobs")
        assert rv.status_code == 200
        jobs = json.loads(rv.data)
        assert len(jobs) == 1
        assert jobs[0]["id"] == "fake/report_test2"


def test_delete_scheduled_jobs(flask_app, setup_workspace):
    with flask_app.test_client() as client:
        rv = client.post(
            "/scheduler/create/fake/report",
            data={
                "report_title": "test2",
                "report_name": "fake/report",
                "overrides": "",
                "mailto": "",
                "cron_schedule": "* * * * *",
            },
        )
        assert rv.status_code == 201

        rv = client.get("/scheduler/jobs")
        assert rv.status_code == 200
        assert len(json.loads(rv.data)) == 1

        rv = client.delete("/scheduler/fake/report_test2")
        assert rv.status_code == 200

        rv = client.get("/scheduler/jobs")
        assert rv.status_code == 200
        assert len(json.loads(rv.data)) == 0


def test_scheduler_runs_notebooks(flask_app, setup_workspace):
    with flask_app.test_client() as client:
        def fake_post(url, params):
            path = url.replace("http://", "").split("/", 1)[1]
            client.post(f"/{path}?{params}")
            return mock.MagicMock()
        with mock.patch("notebooker.web.scheduler.requests.post", side_effect=fake_post):
            rv = client.get("/core/get_all_available_results?limit=50")
            assert len(json.loads(rv.data)) == 0

            rv = client.post(
                "/scheduler/create/fake/report",
                data={
                    "report_title": "test2",
                    "report_name": "fake/report",
                    "overrides": "",
                    "mailto": "",
                    "cron_schedule": "* * * * *",
                },
            )
            assert rv.status_code == 201

            time.sleep(60)  # this is the highest resolution for running jobs
            rv = client.get("core/get_all_available_results?limit=50")
            assert len(json.loads(rv.data)) > 0