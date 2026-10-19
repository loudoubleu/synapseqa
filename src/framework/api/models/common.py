from pydantic import BaseModel, ConfigDict, Field


class InvalidParameterDetail(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    invalid_param_keys: list[str] = Field(alias="invalidParamKeys")


class ApiError(BaseModel):
    status: str
    message: str
    data: InvalidParameterDetail | None = None


class ErrorResponse(BaseModel):
    error: ApiError
