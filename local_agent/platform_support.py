"""Host configuration and locking; no model or candidate execution."""
import contextlib
import json
import os
import platform
import sys
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

REPO = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Settings:
    backend: str
    root: Path
    endpoint: str = 'http://127.0.0.1:11435'
    vendor_override: Path | None = None

    @classmethod
    def load(cls, backend='auto', *, system=None, environ=None):
        system = system or platform.system()
        env = os.environ if environ is None else environ
        selected = ('windows' if system == 'Windows' else 'portable') if backend == 'auto' else backend
        if selected not in ('windows', 'portable'):
            raise ValueError('Unknown host backend')
        if selected == 'windows':
            if system != 'Windows':
                raise ValueError('The frozen Windows backend requires Windows')
            return cls(selected, Path('E:/CSC2108Local'))
        root = Path(env.get('CSC2108_ROOT', str(Path.home() / '.local/share/csc2108'))).expanduser().resolve()
        if root == REPO or root.is_relative_to(REPO):
            raise ValueError('CSC2108_ROOT must be outside the checkout')
        endpoint = env.get('CSC2108_OLLAMA_ENDPOINT', 'http://127.0.0.1:11435').rstrip('/')
        url = urlparse(endpoint)
        if url.scheme != 'http' or url.hostname not in ('127.0.0.1', 'localhost', '::1') or url.username or url.password or url.path or url.query or url.fragment:
            raise ValueError('Use a dedicated loopback HTTP Ollama endpoint')
        if (url.port or 80) == 11434:
            raise ValueError('Keep the project server separate from Desktop port 11434')
        vendor = Path(env['CSC2108_VENDOR']).expanduser().resolve() if env.get('CSC2108_VENDOR') else None
        return cls(selected, root, endpoint, vendor)

    @property
    def vendor(self):
        return self.vendor_override or self.root / 'vendor/LiveCodeBench'

    @property
    def manifest(self):
        return self.root / 'portable-images.json'

    def initialize(self):
        for part in ('config', 'cache', 'tmp', 'logs', 'eval-v2'):
            (self.root / part).mkdir(parents=True, exist_ok=True)
        # Set before importing the frozen modules; leave the user's Windows env alone.
        if self.backend == 'portable':
            os.environ['MSWEA_GLOBAL_CONFIG_DIR'] = str(self.root / 'config')
            os.environ.setdefault('LITELLM_LOCAL_MODEL_COST_MAP', 'True')
            os.environ.setdefault('MSWEA_SILENT_STARTUP', '1')

    def output(self, path, *, create=True):
        path = Path(path).expanduser().resolve()
        if path.is_relative_to(REPO) or path == REPO:
            raise ValueError('Runtime artifacts must be outside the checkout')
        if self.backend == 'windows' and path.drive.upper() != 'E:':
            raise ValueError('Windows runtime artifacts must be on E:')
        if create:
            path.mkdir(parents=True, exist_ok=False)
        return path


@contextlib.contextmanager
def model_lock(settings):
    """Windows shares the historical lock; POSIX holds a stable advisory lock inode."""
    settings.initialize()
    if os.name == 'nt':
        sys.path.insert(0, str(REPO / 'local_eval_v2'))
        from common import Lock
        with Lock(settings.root / 'eval-v2/gpu.lock'):
            yield
        return
    import fcntl
    with (settings.root / 'eval-v2/gpu.lock').open('a+') as stream:
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError('Another local agent owns this data root') from exc
        try:
            stream.seek(0)
            stream.truncate()
            json.dump({'pid': os.getpid(), 'host': platform.node()}, stream)
            stream.flush()
            yield
        finally:
            fcntl.flock(stream, fcntl.LOCK_UN)
        # Do not unlink: replacing the inode would let another process bypass a lock.
