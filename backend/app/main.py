from fastapi import FastAPI

from .api.routes.simulate import router as simulate_router


def create_app() -> FastAPI:
	app = FastAPI(title="Spice Platform API", version="0.1.0")
	app.include_router(simulate_router, prefix="/api")
	return app


app = create_app()
