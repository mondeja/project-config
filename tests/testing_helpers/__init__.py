import os
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

parametrize_color = pytest.mark.parametrize(
    "color",
    (True, False),
    ids=("color=True", "color=False"),
)


def build_testing_server():
    # do not show Flask server banner
    flask.cli.show_server_banner = lambda *args: None

    # create server
    test_server = flask.Flask("http-request-codegen_tests")

    @test_server.route("/ping", methods=["GET"])
    def ping():
        response = flask.make_response("pong", 200)
        response.mimetype = "text/plain"
        return response

    @test_server.route("/download/<filename>", methods=["GET"])
    def download_file(filename):
        response = None
        if flask.request.method == "GET":
            response = flask.make_response(
                flask.request.args.get("content"),
                200,
            )
            response.mimetype = "text/plain"
        else:
            raise NotImplementedError(
                f"Method {flask.request.method} not"
                " implemented in Flask testing server",
            )
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
