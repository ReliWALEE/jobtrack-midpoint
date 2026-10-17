FROM python:3.13-slim
WORKDIR /app
COPY server.py .
COPY web ./web
RUN useradd --uid 10001 --create-home jobtrack && mkdir /data && chown jobtrack /data
USER jobtrack
ENV JOBTRACK_DB=/data/jobtrack.sqlite3
VOLUME ["/data"]
EXPOSE 8000
HEALTHCHECK --interval=30s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health')"
CMD ["python", "server.py", "--host", "0.0.0.0"]
