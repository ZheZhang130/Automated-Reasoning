"""Verify the real LiteLLM transformation without calling any inference server."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import httpx
import litellm
from common import ENDPOINT, ROOT, read
from runtime import RawCapture


class Wire(unittest.TestCase):
    def test_explicit_ollama_sampler_survives_adapter(self):
        profile = read(ROOT / 'profiles.json')['heredoc-v6-16k-common']
        options = profile['sampler'] | {'num_ctx': 16384, 'num_predict': 4096, 'temperature': .2, 'seed': 2108}
        response = {'model': 'qwen3.5:9b', 'created_at': '2026-11-16T00:00:00Z',
                    'message': {'role': 'assistant', 'content': 'READY'}, 'done': True, 'done_reason': 'stop',
                    'prompt_eval_count': 2, 'eval_count': 1, 'total_duration': 1000}
        captured = []
        def fake_post(handler, url, **kwargs):
            payload = json.loads(kwargs['data']) if 'data' in kwargs else kwargs['json']
            self.assertTrue(str(url).startswith(ENDPOINT))
            if str(url).endswith('/api/chat'):
                captured.append(payload)
            return httpx.Response(200, json=response, request=httpx.Request('POST', url))
        with tempfile.TemporaryDirectory() as folder:
            capture = RawCapture(Path(folder) / 'responses.json')
            previous = litellm.callbacks
            litellm.callbacks = [capture]
            try:
                with patch('litellm.llms.custom_httpx.http_handler.HTTPHandler.post', new=fake_post):
                    litellm.completion(model='ollama_chat/qwen3.5:9b', api_base=ENDPOINT,
                        messages=[{'role': 'user', 'content': 'READY'}], think=False,
                        num_ctx=16384, num_predict=4096, temperature=.2, seed=2108,
                        extra_body={'options': options}, num_retries=0)
                self.assertEqual(len(captured), 1)
                self.assertEqual(captured[0]['options'], options)
                self.assertIs(captured[0]['think'], False)
                self.assertEqual(len(capture.requests), 1)
                self.assertEqual(capture.requests[0]['options'], options)
            finally:
                litellm.callbacks = previous


if __name__ == '__main__':
    unittest.main(verbosity=2)
