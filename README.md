# JobTrack

Incremental midpoint upload, batch 1: Python API, SQLite persistence, and backend tests.

Requires Python 3.11+. No package installation is needed.

```sh
python3 server.py
python3 -m unittest discover -s tests -v
```

The API runs at `http://127.0.0.1:8000/api/applications`. SQLite data initializes under `data/` and survives restarts. The dashboard, Chrome extension, deployment configuration, and presentation will arrive in later commits. No live AWS deployment is claimed.
