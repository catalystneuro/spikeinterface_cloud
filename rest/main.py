from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.dandi import router as router_dandi
from pathlib import Path

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


# Load Dandisets metadata - run only at the startup, and if metadat is not yet present
metadata_path = Path().cwd().joinpath("data/dandisets_metadata.json")
if not metadata_path.exists():
    print("Loading dandisets metadata...")
    dandi_client = DandiClient()
    dandi_client.save_dandisets_metadata_to_json()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=5000, reload=True)