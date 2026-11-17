"""Preserve Ollama native-tool history around the pinned LiteLLM transformer."""
import copy
import json


def is_timeout(exception):
    """Pinned LiteLLM wraps httpx ReadTimeout as APIConnectionError (500)."""
    import httpx
    import litellm
    import requests
    seen = set()
    while exception is not None and id(exception) not in seen:
        seen.add(id(exception))
        if isinstance(exception, (httpx.TimeoutException, requests.exceptions.Timeout, litellm.exceptions.Timeout)):
            return True
        exception = exception.__cause__ or exception.__context__
    return False


def native_messages(messages, *, retain_thinking=True):
    """Translate the actual agent history, without synthesizing observations or code."""
    result, names = [], {}
    for original in messages:
        msg = {'role': original['role'], 'content': original.get('content') or ''}
        if not isinstance(msg['content'], str):
            raise ValueError('Only text history is supported in this experiment')
        thinking = original.get('reasoning_content') or original.get('thinking')
        if thinking and retain_thinking:
            msg['thinking'] = thinking
        if original.get('tool_calls'):
            calls = []
            for call in original['tool_calls']:
                fn = copy.deepcopy(call['function'])
                args = fn.get('arguments', {})
                fn['arguments'] = json.loads(args) if isinstance(args, str) else args
                if not isinstance(fn['arguments'], dict):
                    raise ValueError('Tool arguments must be an object')
                calls.append({'function': fn})
                names[call['id']] = fn['name']
            msg['tool_calls'] = calls
        if msg['role'] == 'tool':
            msg['tool_name'] = names[original['tool_call_id']]
        result.append(msg)
    return result


class NativeHistory:
    def _query(self, messages, **kwargs):
        # LiteLLM merges extra_body after its provider transformation. Build this
        # BEFORE super(): the pinned adapter mutates the incoming tool-call args.
        body = copy.deepcopy(self.config.model_kwargs.get('extra_body', {}))
        body['messages'] = native_messages(messages, retain_thinking=getattr(self, 'retain_thinking', True))
        return super()._query(copy.deepcopy(messages), **(kwargs | {'extra_body': body}))
