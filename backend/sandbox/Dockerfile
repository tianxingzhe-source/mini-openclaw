FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    bash curl git procps && \
    rm -rf /var/lib/apt/lists/*

RUN mkdir -p /sandbox/skills /sandbox/workspace /sandbox/memory /sandbox/knowledge

COPY executor.py /opt/executor.py

WORKDIR /sandbox

EXPOSE 9999

CMD ["python", "-u", "/opt/executor.py"]
