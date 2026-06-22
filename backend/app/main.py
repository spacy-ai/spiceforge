from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from  app.api.routes.auth import router as auth_router
from app.api.routes.chat import router as chat_router
from app.api.routes.circuits import router as circuits_router
# from app.api.routes.export import router as export_router
from app.api.routes.simulate import router as simulate_router
from app.api.routes.measure import router as measure_router
from app.api.routes.netlist_gen import router as netlist_gen_router
from app.api.routes.user import router as user_router
from app.api.routes.svg_export import router as svg_export_router
from app.api.routes.chet import router as chet_router




def create_app() -> FastAPI:
	app = FastAPI(title="Spice Platform API", version="0.1.0")

	app.add_middleware(
		CORSMiddleware,
		allow_origins=["http://localhost:3000"],
		allow_credentials=True,
		allow_methods=["*"],
		allow_headers=["*"],
	)

	app.include_router(simulate_router, prefix="/simulate", tags=["simulation"])
	app.include_router(auth_router, prefix="/auth", tags=["auth"])
	app.include_router(chat_router, prefix="/chat", tags=["chat"])
	app.include_router(circuits_router, tags=["circuits"])
	app.include_router(measure_router, prefix="/measure", tags=["measurement"])
	# #app.include_router(export_router, tags=["export"])
	app.include_router(netlist_gen_router, prefix="/netlist", tags=["netlist generation"])
	app.include_router(user_router, prefix="/users", tags=["users"])
	app.include_router(svg_export_router)
	app.include_router(chet_router)

	return app


app = create_app()
