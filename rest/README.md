# REST API

To run REST API in local environment, from the root directory of the project run:

```bash
uvicorn rest.main:app --host 0.0.0.0 --port 8000 --workers 4 --reload
```