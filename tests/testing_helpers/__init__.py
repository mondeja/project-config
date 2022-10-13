import os
import sys
import urllib.parse

import flask
import pytest


rootdir = os.path.abspath(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
)

TEST_SERVER_URL = "http://127.0.0.1:9997"
TEST_SERVER_HOST, TEST_SERVER_PORT = urllib.parse.urlsplit(
    TEST_SERVER_URL,
).netloc.split(":")


mark_end2end = pytest.mark.skipif(
    not os.environ.get("PROJECT_CONFIG_TESTS_E2E"),
    reason="The environment variable PROJECT_CONFIG_TESTS_E2E is not set",
)

mark_unix_only = pytest.mark.skipif(
    "win" in sys.platform and sys.platform != "darwin",
    reason="Windows does not support this test",
)

mark_linux_only = pytest.mark.skipif(
    "win" in sys.platform,
    reason="This test is only supported on Linux",
)


def build_testing_server():
    # do not show Flask server banner
    flask.cli.show_server_banner = lambda *args: None  # noqa: U100

    # create server
    test_server = flask.Flask("project-config_tests")

    @test_server.route("/ping", methods=["GET"])
    def ping():
        response = flask.make_response("pong", 200)
        response.mimetype = "text/plain"
        return response

    @test_server.route("/download/<content>/<filename>", methods=["GET"])
    def download_file(filename, content):  # noqa: U100
        response = response = flask.make_response(content, 200)
        response.mimetype = "text/plain"
        return response

    return test_server


def testing_server_process():
    build_testing_server().run(
        host=TEST_SERVER_HOST,
        port=TEST_SERVER_PORT,
        debug=True,
        use_reloader=False,
    )


class FakePlugin:
    def ifFoo(self):  # method not static
        pass

    @staticmethod
    def ifBar():  # static method
        pass

    @staticmethod
    def foo():
        pass

    @classmethod
    def bar(cls):
        pass
