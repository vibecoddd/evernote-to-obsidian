from pathlib import Path
import socket
import threading

import macos_app


def test_resource_root_uses_project_directory_when_not_frozen(monkeypatch):
    monkeypatch.delattr(macos_app.sys, "_MEIPASS", raising=False)

    assert macos_app.get_resource_root() == Path(macos_app.__file__).resolve().parent


def test_resource_root_uses_pyinstaller_directory_when_frozen(monkeypatch, tmp_path):
    monkeypatch.setattr(macos_app.sys, "_MEIPASS", str(tmp_path), raising=False)

    assert macos_app.get_resource_root() == tmp_path


def test_find_free_port_returns_loopback_port():
    port = macos_app.find_free_port()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", port))
        assert probe.getsockname()[1] == port


class FakeResponse:
    def __init__(self, status=200):
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


def test_wait_for_server_retries_until_http_200():
    responses = [OSError("not ready"), FakeResponse(200)]
    sleeps = []

    def opener(_url, timeout):
        value = responses.pop(0)
        if isinstance(value, Exception):
            raise value
        return value

    macos_app.wait_for_server(
        "http://127.0.0.1:43123/",
        timeout=1,
        interval=0.01,
        opener=opener,
        sleep=sleeps.append,
        clock=iter([0.0, 0.1, 0.2]).__next__,
    )

    assert sleeps == [0.01]


def test_wait_for_server_raises_startup_error_after_deadline():
    def opener(_url, timeout):
        raise OSError("connection refused")

    times = iter([0.0, 0.5, 1.1])

    try:
        macos_app.wait_for_server(
            "http://127.0.0.1:43123/",
            timeout=1,
            interval=0.01,
            opener=opener,
            sleep=lambda _seconds: None,
            clock=times.__next__,
        )
    except macos_app.StartupError as error:
        assert "127.0.0.1:43123" in str(error)
    else:
        raise AssertionError("wait_for_server should time out")


class FakeMigrator:
    def __init__(self):
        self.run_calls = []
        self.started = threading.Event()

    def run(self, **kwargs):
        self.run_calls.append(kwargs)
        self.started.set()


class FakeWebView:
    def __init__(self):
        self.window_calls = []
        self.start_calls = 0

    def create_window(self, title, url, **kwargs):
        self.window_calls.append((title, url, kwargs))
        return object()

    def start(self):
        self.start_calls += 1


def test_run_desktop_app_uses_dynamic_loopback_url(monkeypatch):
    migrator = FakeMigrator()
    webview = FakeWebView()
    readiness_urls = []

    monkeypatch.setattr(macos_app.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(macos_app, "find_free_port", lambda _host: 43123)

    def readiness(url):
        assert migrator.started.wait(1)
        readiness_urls.append(url)

    macos_app.run_desktop_app(
        migrator_factory=lambda: migrator,
        webview_module=webview,
        readiness=readiness,
    )

    assert migrator.run_calls == [
        {
            "host": "127.0.0.1",
            "port": 43123,
            "debug": False,
            "allow_unsafe_werkzeug": True,
        }
    ]
    assert readiness_urls == ["http://127.0.0.1:43123/"]
    assert webview.window_calls[0][1] == "http://127.0.0.1:43123/"
    assert webview.start_calls == 1


def test_web_migrator_forwards_desktop_server_option(monkeypatch):
    from web_app import WebMigrator

    migrator = WebMigrator()
    run_calls = []
    monkeypatch.setattr(
        migrator.socketio,
        "run",
        lambda app, **kwargs: run_calls.append(kwargs),
    )

    migrator.run(
        host="127.0.0.1",
        port=43123,
        debug=False,
        allow_unsafe_werkzeug=True,
    )

    assert run_calls == [
        {
            "host": "127.0.0.1",
            "port": 43123,
            "debug": False,
            "allow_unsafe_werkzeug": True,
        }
    ]
