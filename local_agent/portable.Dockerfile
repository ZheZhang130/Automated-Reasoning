FROM python:3.11-slim-bookworm@sha256:a83ba18aef0f865b1a4a611c2cf460fe446f2795673bbb9fe43be570439e3b39
COPY local_baseline/judge-requirements.lock /opt/judge-requirements.lock
RUN --mount=type=secret,id=ca \
    if [ -f /run/secrets/ca ]; then \
      PIP_CERT=/run/secrets/ca pip install --no-cache-dir -r /opt/judge-requirements.lock; \
    else pip install --no-cache-dir -r /opt/judge-requirements.lock; fi
ENV PYTHONDONTWRITEBYTECODE=1
USER 65534:65534
ENTRYPOINT ["timeout", "-k", "2", "175"]
