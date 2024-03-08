from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes.auth_router import router as auth_router
from api.routes.user_routes import router as user_router
from api.routes.sample_routes import router as sample_router
from core.database import DB_POOL

from utils.api_utils import add_scopes_to_docs


app = FastAPI()


# app = FastAPI(lifespan=add_scopes_to_docs)
# ml_models = {}
# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     # Load the ML model
#     ml_models["answer_to_everything"] = fake_answer_to_everything_ml_model
#     yield
#     # Clean up the ML models and release the resources
#     ml_models.clear()


# Ensure connections are returned to the pool after use
@app.middleware("http")
async def release_db_connection(request, call_next):
    response = await call_next(request)
    if getattr(response, "connection", None) is not None:
        DB_POOL.putconn(response.connection)
    return response


app.include_router(user_router)
app.include_router(auth_router)
app.include_router(sample_router)

add_scopes_to_docs(app)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    max_age=600,
    allow_headers=["*"],
    # allow_origin_regex="",
)
