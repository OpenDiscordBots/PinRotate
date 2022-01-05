from pydantic import BaseModel


class PinRotateConfig(BaseModel):
    channels: list[str]
