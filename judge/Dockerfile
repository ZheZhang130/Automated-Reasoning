# csc2108-judge: the judge black box (see timeline/judge_1114.md).
# Build from the judge/ directory:  docker build -t csc2108-judge:0.2.1 .
# Start it with judgekit (python -m judgekit up), which sets the required flags.
FROM python:3.12-slim@sha256:5e2bdb1b0d542d5039cffb8181c65930093949194a65c365dfb1b0fe13a4fa5b

# One unprivileged user per worker slot: runner-0 .. runner-15 (uid/gid 2000..2015).
RUN for k in $(seq 0 15); do \
        groupadd --gid $((2000 + k)) runner-$k && \
        useradd --uid $((2000 + k)) --gid $((2000 + k)) --no-create-home \
                --home-dir /nonexistent --shell /usr/sbin/nologin runner-$k; \
    done

COPY container/judge.py /opt/judge/judge.py
RUN printf '#!/bin/sh\nexec python3 -I /opt/judge/judge.py "$@"\n' > /usr/local/bin/judge \
    && chmod 755 /usr/local/bin/judge /opt/judge && chmod 644 /opt/judge/judge.py

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
LABEL org.csc2108.judge.version="0.2.1"
USER root
WORKDIR /
CMD ["sleep", "infinity"]
