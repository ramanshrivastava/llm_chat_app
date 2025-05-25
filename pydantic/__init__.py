from dataclasses import dataclass, field as dataclass_field, MISSING

# Minimal Field implementation

def Field(default=MISSING, default_factory=MISSING, **kwargs):
    return dataclass_field(default=default, default_factory=default_factory, metadata=kwargs)

class BaseModel:
    """Very small subset of pydantic BaseModel using dataclasses."""

    def __init_subclass__(cls, **kwargs):
        dataclass(cls)
        super().__init_subclass__(**kwargs)
