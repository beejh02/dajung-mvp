from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    service: str
    app_name: str
    version: str
    environment: str
