from app.api.datasources import router as datasources_router
from app.api.backup import router as backup_router
from app.api.migration import router as migration_router
from app.api.ws import router as ws_router

routers = [datasources_router, backup_router, migration_router, ws_router]
