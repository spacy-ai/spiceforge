from fastapi import FastAPI
from  app.api.routes.auth import router as auth_router
from app.api.routes.simulate import router as simulate_router
from app.api.routes.measure import router as measure_router



def create_app() -> FastAPI:
	app = FastAPI(title="Spice Platform API", version="0.1.0")

	@app.get("/")
	def home() -> dict:
		return {
			"message": "Welcome to the Spice Platform API",
			"docs": "/docs",
		}

	app.include_router(simulate_router, prefix="/simulate", tags=["simulation"])
	app.include_router(auth_router, prefix="/auth", tags=["auth"])
	app.include_router(measure_router, prefix="/measure", tags=["measurement"])
	return app


app = create_app()
