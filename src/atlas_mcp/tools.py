from typing import TypedDict
from pydantic import BaseModel, Field


class Stat(BaseModel):
    mean: float = Field(description="Mean value")
    std: float = Field(description="Standard deviation")


class Echo(TypedDict):
    echoed: str


def compute_stats(data: list[float]) -> Stat:
    import statistics as st

    return Stat(mean=st.fmean(data), std=st.pstdev(data))


def echo(msg: str) -> Echo:
    return {"echoed": msg}
