"""Tests for common.config — Settings with env var overrides."""

from common.config import Settings, get_settings


class TestSettingsDefaults:
    def test_redis_url(self):
        s = Settings()
        assert s.redis_url == "redis://localhost:6379"

    def test_api_host(self):
        s = Settings()
        assert s.api_host == "0.0.0.0"

    def test_api_port(self):
        s = Settings()
        assert s.api_port == 8000

    def test_api_base_url(self):
        s = Settings()
        assert s.api_base_url == "http://localhost:8000"

    def test_max_retries(self):
        s = Settings()
        assert s.max_retries == 3

    def test_worker_concurrency(self):
        s = Settings()
        assert s.worker_concurrency == 2

    def test_log_level(self):
        s = Settings()
        assert s.log_level == "INFO"

    def test_container_image(self):
        s = Settings()
        assert s.container_image == "minions-agent:latest"

    def test_container_network_mode(self):
        s = Settings()
        assert s.container_network_mode == "host"


class TestSettingsEnvOverride:
    def test_redis_url_override(self, monkeypatch):
        monkeypatch.setenv("MINIONS_REDIS_URL", "redis://custom:6380")
        s = Settings()
        assert s.redis_url == "redis://custom:6380"

    def test_api_port_override(self, monkeypatch):
        monkeypatch.setenv("MINIONS_API_PORT", "9000")
        s = Settings()
        assert s.api_port == 9000

    def test_max_retries_override(self, monkeypatch):
        monkeypatch.setenv("MINIONS_MAX_RETRIES", "5")
        s = Settings()
        assert s.max_retries == 5

    def test_log_level_override(self, monkeypatch):
        monkeypatch.setenv("MINIONS_LOG_LEVEL", "DEBUG")
        s = Settings()
        assert s.log_level == "DEBUG"


class TestGetSettings:
    def test_returns_settings_instance(self):
        s = get_settings()
        assert isinstance(s, Settings)
