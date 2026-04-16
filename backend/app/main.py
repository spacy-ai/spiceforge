from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from  app.api.routes.auth import router as auth_router
from app.api.routes.circuits import router as circuits_router
from app.api.routes.export import router as export_router
from app.api.routes.simulate import router as simulate_router
from app.api.routes.measure import router as measure_router



def create_app() -> FastAPI:
	app = FastAPI(title="Spice Platform API", version="0.1.0")

	app.add_middleware(
		CORSMiddleware,
		allow_origins=["http://localhost:3000"],
		allow_credentials=True,
		allow_methods=["*"],
		allow_headers=["*"],
	)

	@app.get("/")
	def home() -> dict:
		return {
			"message": "Welcome to the Spice Platform API",
			"docs": "/docs",
		}

	app.include_router(simulate_router, prefix="/simulate", tags=["simulation"])
	app.include_router(auth_router, prefix="/auth", tags=["auth"])
	app.include_router(circuits_router, tags=["circuits"])
	app.include_router(measure_router, prefix="/measure", tags=["measurement"])
	app.include_router(export_router, prefix="/export", tags=["export"])
	return app


app = create_app()
