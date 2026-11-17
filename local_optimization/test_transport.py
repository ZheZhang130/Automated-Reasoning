"""Exercise the real pinned provider serializer; no inference or benchmark solutions."""
import copy
import json
import unittest
from unittest.mock import patch

from optlib import ENDPOINT
import httpx
import litellm
from transport import native_messages, is_timeout


class Transport(unittest.TestCase):
    def transmit(self, fixed):
        messages = [{'role': 'user', 'content': 'Inspect workspace'},
            {'role': 'assistant', 'content': '', 'reasoning_content': 'Need the current path.', 'tool_calls': [
                {'id': 'call_1', 'type': 'function', 'function': {'name': 'bash', 'arguments': json.dumps({'command': 'pwd'})}}]},
            {'role': 'tool', 'tool_call_id': 'call_1', 'content': '/workspace'}]
        expected = copy.deepcopy(messages)
        options = {'num_ctx': 131072, 'num_predict': 32768, 'seed': 2108, 'temperature': .2, 'presence_penalty': 0.0}
        body = {'options': options}
        if fixed:
            body['messages'] = native_messages(messages)
        captured = []
        def post(handler, url, **kwargs):
            self.assertTrue(str(url).startswith(ENDPOINT + '/'))
            if str(url).endswith('/api/chat'):
                captured.append(json.loads(kwargs['data']))
            return httpx.Response(200, json={'model': 'qwen3.5:9b', 'message': {'role': 'assistant', 'content': 'ok'}, 'done': True, 'done_reason': 'stop'}, request=httpx.Request('POST', url))
        with patch('litellm.llms.custom_httpx.http_handler.HTTPHandler.post', new=post):
            litellm.completion(model='ollama_chat/qwen3.5:9b', api_base=ENDPOINT, messages=copy.deepcopy(messages),
                extra_body=body, think=True, num_retries=0)
        self.assertEqual(messages, expected)
        self.assertEqual(len(captured), 1)
        self.assertEqual(captured[0]['options'], options)
        self.assertIs(captured[0]['think'], True)
        return captured[0]

    def test_stock_adapter_drops_history(self):
        payload = self.transmit(False)
        self.assertNotIn('tool_calls', payload['messages'][1])
        self.assertNotIn('tool_name', payload['messages'][2])

    def test_override_preserves_history_and_sampler(self):
        payload = self.transmit(True)
        self.assertEqual(payload['messages'][1]['tool_calls'][0]['function'], {'name': 'bash', 'arguments': {'command': 'pwd'}})
        self.assertEqual(payload['messages'][1]['thinking'], 'Need the current path.')
        self.assertEqual(payload['messages'][2]['tool_name'], 'bash')

    def test_unknown_tool_result_is_rejected(self):
        with self.assertRaises(KeyError):
            native_messages([{'role': 'tool', 'content': 'x', 'tool_call_id': 'missing'}])

    def test_wrapped_timeout_is_distinct_from_connection_refusal(self):
        for error_type, expected in [(httpx.ReadTimeout, True), (httpx.ConnectError, False)]:
            def post(handler, url, **kwargs):
                self.assertTrue(str(url).startswith(ENDPOINT + '/'))
                if str(url).endswith('/api/chat'):
                    raise error_type('Deliberate transport fixture', request=httpx.Request('POST', url))
                return httpx.Response(200, json={}, request=httpx.Request('POST', url))
            with patch('litellm.llms.custom_httpx.http_handler.HTTPHandler.post', new=post):
                try:
                    litellm.completion(model='ollama_chat/qwen3.5:9b', api_base=ENDPOINT,
                        messages=[{'role':'user','content':'Test'}], num_retries=0)
                except Exception as exc:
                    self.assertEqual(is_timeout(exc), expected)
                else:
                    self.fail('Expected deliberate transport failure')


if __name__ == '__main__':
    unittest.main(verbosity=2)
