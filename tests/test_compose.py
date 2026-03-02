"""Tests for docker-compose.yml and related Docker files."""

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent


class TestDockerComposeFile:
    def test_compose_file_exists(self):
        assert (ROOT / "docker-compose.yml").is_file()

    def test_compose_file_is_valid_yaml(self):
        content = (ROOT / "docker-compose.yml").read_text()
        data = yaml.safe_load(content)
        assert isinstance(data, dict)

    def test_compose_has_all_six_services(self):
        content = (ROOT / "docker-compose.yml").read_text()
        data = yaml.safe_load(content)
        expected = {"api", "redis", "worker", "dashboard", "prometheus", "grafana"}
        assert expected == set(data["services"].keys())


class TestDockerfile:
    def test_dockerfile_exists(self):
        assert (ROOT / "Dockerfile").is_file()


class TestWorkerEntrypoint:
    def test_worker_run_module_exists(self):
        assert (ROOT / "worker" / "run.py").is_file()
