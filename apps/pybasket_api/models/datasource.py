from typing import Optional

import pydantic
from pydantic import BaseModel


class Datasource(BaseModel):
    data: dict = pydantic.Field(
        default={"": ""},
        example={
            "8bd8cde8-1d8c-4d85-9260-121292acf74c": {
                "title": "osisaf sh icearea seasonal",
                "feature_type": "timeSeries",
                "resources": {
                    "opendap": [
                        "https://hyrax.epinux.com/opendap/hyrax/local_data/osisaf_sh_icearea_seasonal.nc"
                    ]
                },
            },
            "55669b7e-6911-4c16-b3a4-927320d7e0c5": {
                "title": "osisaf nh iceextent daily",
                "feature_type": "timeSeries",
                "resources": {
                    "opendap": [
                        "https://hyrax.epinux.com/opendap/hyrax/local_data/osisaf_nh_iceextent_daily.nc"
                    ]
                },
            },
            "85271d8c-fcb6-4e8d-9a2b-a408f79d728b": {
                "title": "itp01_itp1grd2042",
                "feature_type": "profile",
                "resources": {
                    "opendap": [
                        "https://hyrax.epinux.com/opendap/hyrax/local_data/itp01_itp1grd2042.nc"
                    ]
                },
            },
            "6373edcd-1aef-452f-8e75-dbb96cc72328": {
                "title": "itp01_itp1grd2042",
                "feature_type": "NA",
                "resources": {
                    "opendap": [
                        "https://hyrax.epinux.com/opendap/hyrax/local_data/itp01_itp1grd2042.nc"
                    ]
                },
            },
            "614372dc-da52-4651-8505-1957c19a0cdf": {
                "title": "ctdiaoos gi2007 2009",
                "feature_type": "timeSeriesProfile",
                "resources": {
                    "opendap": [
                        "https://hyrax.epinux.com/opendap/hyrax/local_data/ctdiaoos_gi2007_2009.nc"
                    ]
                },
            },
            "4534a82c-3564-4da4-af41-bd5d5d44294e": {
                "title": "High resolution sea ice concentration",
                "feature_type": "NA",
                "resources": {
                    "OGC:WMS": [
                        "https://thredds.met.no/thredds/wms/cmems/si-tac/cmems_obs-si_arc_phy-siconc_nrt_L4-auto_P1D_aggregated?service=WMS&version=1.3.0&request=GetCapabilities"
                    ]
                },
            },
            "ae997427-ad27-4c08-9a8c-416de7c8ad32": {
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
    notebook: Optional[bool] = pydantic.Field(default=False, example=True)
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
