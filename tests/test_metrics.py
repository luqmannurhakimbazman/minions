"""Tests for Prometheus metrics and config files."""

import json
import pathlib

import yaml
from prometheus_client import Counter, Histogram


MONITORING_DIR = pathlib.Path(__file__).resolve().parent.parent / "monitoring"


# ---- Task 7.1: Metric definitions ----

class TestMetricDefinitions:
    def test_counters_exist(self):
        from monitoring.metrics import (
            TASKS_SUBMITTED,
            TASKS_COMPLETED,
            TASKS_FAILED,
            RETRIES_TOTAL,
        )
        assert isinstance(TASKS_SUBMITTED, Counter)
        assert isinstance(TASKS_COMPLETED, Counter)
        assert isinstance(TASKS_FAILED, Counter)
        assert isinstance(RETRIES_TOTAL, Counter)

    def test_histograms_exist(self):
        from monitoring.metrics import TASK_DURATION_SECONDS, CONTAINER_SPAWN_SECONDS
        assert isinstance(TASK_DURATION_SECONDS, Histogram)
        assert isinstance(CONTAINER_SPAWN_SECONDS, Histogram)

    def test_counter_can_increment(self):
        from monitoring.metrics import TASKS_SUBMITTED
        # Should not raise
        TASKS_SUBMITTED.inc()


# ---- Task 7.2: Config files ----

class TestPrometheusConfig:
    def test_prometheus_yml_exists(self):
        path = MONITORING_DIR / "prometheus.yml"
        assert path.exists()

    def test_prometheus_yml_valid_yaml(self):
        path = MONITORING_DIR / "prometheus.yml"
        data = yaml.safe_load(path.read_text())
        assert "scrape_configs" in data

    def test_prometheus_yml_has_jobs(self):
        path = MONITORING_DIR / "prometheus.yml"
        data = yaml.safe_load(path.read_text())
        job_names = [j["job_name"] for j in data["scrape_configs"]]
        assert "minions-api" in job_names
        assert "minions-worker" in job_names


class TestGrafanaDashboard:
    def test_grafana_dashboard_exists(self):
        path = MONITORING_DIR / "grafana" / "dashboard.json"
        assert path.exists()

    def test_grafana_dashboard_valid_json(self):
        path = MONITORING_DIR / "grafana" / "dashboard.json"
        data = json.loads(path.read_text())
        assert "panels" in data
        assert "title" in data

    def test_grafana_dashboard_has_panels(self):
        path = MONITORING_DIR / "grafana" / "dashboard.json"
        data = json.loads(path.read_text())
        assert len(data["panels"]) >= 5
