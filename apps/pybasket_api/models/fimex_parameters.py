from pydantic import BaseModel


class FimexParameters(BaseModel):
    input_data: list = None
    reducetime_start: str = None
    reducetime_end: str = None
    interpolate_proj_string: str = None
    interpolate_method: str = None
    select_variables: list = None
    interpolate_xaxis_min: str = None
    interpolate_xaxis_max: str = None
    interpolate_yaxis_min: str = None
    interpolate_yaxis_max: str = None
    interpolate_xaxis_units: str = None
    interpolate_yaxis_units: str = None
    reducebox_east: str
    reducebox_south: str
    reducebox_west: str
    reducebox_north: str
    interpolate_hor_steps: str = None
    inputtype: str
    outputtype: str
