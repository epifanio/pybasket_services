from typing import Optional

import pydantic
from pydantic import BaseModel


class Datasource(BaseModel):
    data: dict = pydantic.Field(
        default={"": ""},
        example={
            "id1": {
                "title": "osisaf sh icearea seasonal",
                "feature_type": "timeSeries",
                "resources": {
                    "opendap": [
                        "http://hyrax.epinux.com/opendap/osisaf_sh_icearea_seasonal.nc"
                    ]
                },
            },
            "id2": {
                "title": "osisaf nh iceextent daily",
                "feature_type": "timeSeries",
                "resources": {
                    "opendap": [
                        "http://hyrax.epinux.com/opendap//osisaf_nh_iceextent_daily.nc"
                    ]
                },
            },
            "id3": {
                "title": "itp01_itp1grd2042",
                "feature_type": "profile",
                "resources": {
                    "opendap": [
                        "http://hyrax.epinux.com/opendap/itp01_itp1grd2042.nc"
                    ]
                },
            },
            "id4": {
                "title": "itp01_itp1grd2042",
                "feature_type": "NA",
                "resources": {
                    "opendap": [
                        "http://hyrax.epinux.com/opendap/itp01_itp1grd2042.nc"
                    ]
                },
            },
            "id5": {
                "title": "ctdiaoos gi2007 2009",
                "feature_type": "timeSeriesProfile",
                "resources": {
                    "opendap": [
                        "http://hyrax.epinux.com/opendap/ctdiaoos_gi2007_2009.nc"
                    ]
                },
            },
            "id6": {
                "title": "High resolution sea ice concentration",
                "feature_type": "NA",
                "resources": {
                    "OGC:WMS": [
                        "https://thredds.met.no/thredds/wms/cmems/si-tac/cmems_obs-si_arc_phy-siconc_nrt_L4-auto_P1D_aggregated?service=WMS&version=1.3.0&request=GetCapabilities"
                    ]
                },
            },
            "id7": {
                "title": "S1A EW GRDM",
                "feature_type": "NA",
                "resources": {
                    "OGC:WMS": [
                        "http://nbswms.met.no/thredds/wms_ql/NBS/S1A/2021/05/18/EW/S1A_EW_GRDM_1SDH_20210518T070428_20210518T070534_037939_047A42_65CD.nc?SERVICE=WMS&REQUEST=GetCapabilities"
                    ]
                },
            },
        },
    )
    email: str = pydantic.Field(default="me@you.web", example="epiesasha@me.com")
    project: Optional[str] = pydantic.Field(default="METSIS", example="METSIS")
    notebook: Optional[bool] = pydantic.Field(default=False, example=False)
    notebooks: Optional[dict] = pydantic.Field(
        default={"": ""},
        example={
            "UseCase2": {
                "name": "UseCase",
                "purpose": "cool science",
                "resource": "https://raw.githubusercontent.com/UseCase.ipynb",
            }
        },
    )
