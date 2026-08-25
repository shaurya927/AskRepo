from pydantic import BaseModel, ConfigDict
import uuid

class CodeSymbolResponse(BaseModel):
    id: uuid.UUID
    repository_id: uuid.UUID
    file_path: str
    name: str
    symbol_type: str
    language: str
    start_line: int
    end_line: int
    class_name: str | None
    signature: str | None
    docstring: str | None
    decorators: list[str]
    complexity: int
    model_config = ConfigDict(from_attributes=True)

class CodeImportResponse(BaseModel):
    id: uuid.UUID
    repository_id: uuid.UUID
    file_path: str
    source: str
    names: list[str]
    is_relative: bool
    resolved_path: str | None
    is_internal: bool
    line: int
    model_config = ConfigDict(from_attributes=True)

class RepositoryMetricsResponse(BaseModel):
    total_functions: int
    total_classes: int
    total_methods: int
    avg_complexity: float
    max_complexity: int
    complexity_distribution: dict
    internal_dependencies: int
    external_dependencies: int
    model_config = ConfigDict(from_attributes=True)
