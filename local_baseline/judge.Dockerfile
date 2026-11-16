FROM python:3.11-slim-bookworm@sha256:a83ba18aef0f865b1a4a611c2cf460fe446f2795673bbb9fe43be570439e3b39
COPY host-ca.pem /opt/build-host-ca.pem
COPY judge-requirements.lock /opt/judge-requirements.lock
RUN PIP_CERT=/opt/build-host-ca.pem pip install --no-cache-dir -r /opt/judge-requirements.lock
ENV PYTHONDONTWRITEBYTECODE=1
USER 65534:65534
