from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

from routes.dandi import router as router_dandi
from routes.sorting import router as router_sorting
from clients.dandi import DandiClient


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
app.include_router(router_dandi, prefix="/api/dandi", tags=["dandi"])
app.include_router(router_sorting, prefix="/api/sorting", tags=["sorting"])


# Load Dandisets metadata - run only at the startup, and if metadat is not yet present
metadata_path = Path().cwd().joinpath("data/dandisets_metadata.json")
if not metadata_path.exists():
    print("Loading dandisets metadata...")
    dandi_client = DandiClient()
    dandi_client.save_dandisets_metadata_to_json()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)