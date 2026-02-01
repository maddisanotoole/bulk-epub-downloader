```bash
python -m pip install -r requirements.txt
```

## Running the Application

### Start the API Server

```bash
uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```

### Start the Queue Worker (in a separate terminal)

```bash
python worker.py
```

The worker continuously monitors the queue table and processes pending downloads. It will:

- Poll for pending items every 5 seconds
- Download books one at a time
- Update status (IN_PROGRESS → COMPLETED or FAILED)
- Retry failed downloads up to 3 times
- Mark books as downloaded in the database
