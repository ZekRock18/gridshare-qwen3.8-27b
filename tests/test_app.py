import unittest
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient
import app


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app.app)
        app.MODEL_PROCESS = None
        app.set_state("ready")

    def tearDown(self):
        app.MODEL_PROCESS = None
        app.set_state("starting")
        self.client.close()

    def test_health_waits_for_model(self):
        app.set_state("loading")
        self.assertEqual(self.client.get("/health").status_code, 503)
        self.assertEqual(self.client.post("/run", json={"input": {"prompt": "Hi"}}).status_code, 503)
        app.set_state("ready")
        self.assertEqual(self.client.get("/health").status_code, 200)

    def test_crashed_model_is_unhealthy(self):
        app.MODEL_PROCESS = Mock(returncode=1)
        app.MODEL_PROCESS.poll.return_value = 1
        self.assertEqual(self.client.get("/health").status_code, 503)

    @patch("app.requests.post")
    def test_gridshare_envelope_and_response(self, post):
        expected = {"choices": [{"message": {"role": "assistant", "content": "Hello"}}]}
        post.return_value = Mock(status_code=200)
        post.return_value.json.return_value = expected
        response = self.client.post("/run", json={"input": {"prompt": "Hi", "max_tokens": 96, "enable_thinking": False}})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected)
        body = post.call_args.kwargs["json"]
        self.assertEqual(body["messages"], [{"role": "user", "content": "Hi"}])
        self.assertEqual(body["chat_template_kwargs"], {"enable_thinking": False})
        self.assertFalse(body["stream"])

    def test_invalid_inputs_return_client_errors(self):
        for inner in ([], {}, {"messages": []}, {"prompt": "Hi", "max_tokens": "oops"}, {"prompt": "Hi", "temperature": "nan"}):
            with self.subTest(inner=inner):
                self.assertEqual(self.client.post("/run", json={"input": inner}).status_code, 400)

    @patch("app.requests.post", side_effect=app.requests.Timeout("timeout"))
    def test_upstream_timeout_returns_gateway_error(self, post):
        self.assertEqual(self.client.post("/run", json={"input": {"prompt": "Hi"}}).status_code, 502)


if __name__ == "__main__":
    unittest.main()
