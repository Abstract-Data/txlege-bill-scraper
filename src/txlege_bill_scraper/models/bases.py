import datetime
from typing import Optional, Annotated, Dict, Any
from sqlmodel import SQLModel, Field
from pydantic import ConfigDict
from logfire.integrations.pydantic import PluginSettings
import hashlib

class TexasLegislatureModelBase(SQLModel, plugin_settings=PluginSettings(logfire={'record': 'failure'})):
    __table_args__ = {'extend_existing': True},
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        use_enum_values=True,
        str_strip_whitespace=True,
    )

    @classmethod
    def create_hash(cls, *args, length: int = 16) -> str:
        data_to_encode = []
        for arg in args:
            match arg:
                case str():
                    data_to_encode.append(arg)
                case dict():
                    data_to_encode.append(cls._encode_dict(arg))
                case list():
                    data_to_encode.append(cls._encode_list(arg))
                case datetime.date():
                    data_to_encode.append(arg.strftime('%Y%m%d'))
                case None:
                    pass
                case _:
                    data_to_encode.append(str(arg))

        return hashlib.sha256("".join(data_to_encode).encode()).hexdigest()[:length]
