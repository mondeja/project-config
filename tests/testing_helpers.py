import os
import urllib.parse

import flask


rootdir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

TEST_SERVER_URL = "http://127.0.0.1:9997"
TEST_SERVER_HOST, TEST_SERVER_PORT = urllib.parse.urlsplit(
    TEST_SERVER_URL,
).netloc.split(":")


def build_testing_server():
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
