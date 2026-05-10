from fastapi import FastAPI
from authority.api import teams, nodes, deployments, bootstrap

app = FastAPI(title="HyperSwarm Authority")

app.include_router(teams.router, prefix="/teams", tags=["teams"])
app.include_router(nodes.router, prefix="/nodes", tags=["nodes"])
app.include_router(deployments.router, prefix="/deployments", tags=["deployments"])
app.include_router(bootstrap.router, prefix="/bootstrap", tags=["bootstrap"])


@app.get("/")
def root():
    return {
        "service": "hyperswarm-authority",
        "status": "ok"
    }
