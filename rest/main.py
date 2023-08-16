from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

from core.settings import settings
from routes.user import router as router_user
from routes.dandi import router as router_dandi
from routes.sorting import router as router_sorting
from routes.runs import router as router_runs
from clients.dandi import DandiClient
from db.utils import initialize_db


app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router_user, prefix="/api/user", tags=["user"])
app.include_router(router_dandi, prefix="/api/dandi", tags=["dandi"])
app.include_router(router_sorting, prefix="/api/sorting", tags=["sorting"])
app.include_router(router_runs, prefix="/api/runs", tags=["runs"])


# Create Database, if not yet created
try:
    print("############  Initializing the database - if needed  ############")
    initialize_db(db='postgresql+psycopg2://postgres:postgres@database/si-sorting-db')
except Exception as e:
    print(f"Error initializing the database: {e}")

# Load Dandisets metadata - run only at the startup, and if metadata is not yet present
metadata_path = Path().cwd().joinpath("data/dandisets_metadata.json")
print("Loading dandisets metadata...")
dandi_client = DandiClient(token=settings.DANDI_API_TOKEN)
dandi_client.save_dandisets_metadata_to_json()
print("Done loading dandisets metadata.")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)