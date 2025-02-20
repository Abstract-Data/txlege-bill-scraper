from typing import Optional, Annotated, Dict, Any
from sqlmodel import SQLModel, Field
from pydantic import ConfigDict

class TexasLegislatureModelBase(SQLModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        validate_assignment=True,
        use_enum_values=True,
    )