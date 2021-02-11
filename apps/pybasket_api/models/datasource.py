from typing import Optional

import pydantic
from pydantic import BaseModel


class Datasource(BaseModel):
    data: dict = pydantic.Field(default={"": ""},
                                example={
                                    "id1": {
                                        "title": "osisaf sh icearea seasonal",
                                        "feature_type": "timeSeries",
                                        "resources": {
                                            "opendap": [
                                                "http://hyrax.epinux.com/opendap/hyrax/local_data/osisaf_sh_icearea_seasonal.nc"]
                                        }
                                    },
                                    "id2": {
                                        "title": "osisaf nh iceextent daily",
                                        "feature_type": "timeSeries",
                                        "resources": {
                                            "opendap": [
                                                "http://hyrax.epinux.com/opendap/hyrax/local_data/osisaf_nh_iceextent_daily.nc"]
                                        }
                                    },
                                    "id3": {
                                        "title": "ctdiaoos gi2007 2009",
                                        "feature_type": "timeSeriesProfile",
                                        "resources": {
                                            "opendap": [
                                                "http://hyrax.epinux.com/opendap/hyrax/local_data/ctdiaoos_gi2007_2009.nc"]
                                        }
                                    }
                                })
    email: str = pydantic.Field(default='me@you.web', example='epiesasha@me.com')
    project: Optional[str] = pydantic.Field(default='METSIS', example='METSIS')
