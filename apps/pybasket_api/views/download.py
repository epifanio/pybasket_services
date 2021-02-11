import os
from pathlib import Path

import fastapi
from fastapi import Request
from itsdangerous import TimestampSigner, SignatureExpired, BadSignature
from starlette.templating import Jinja2Templates
import datetime as dt
from datetime import timezone
from datetime import timedelta

router = fastapi.APIRouter()
templates = Jinja2Templates(directory='app/templates')


@router.get("/api/download/{id}")
async def read_item(request: Request, id: str):
    # TODO: check that the file  exist, if yes ..
    s = TimestampSigner('secret-key')
    try:
        token = s.unsign(id, max_age=600, return_timestamp=True)
        filename = token[0].decode()
        expire_utc_time = token[1]
        #time_delta = dt.datetime.now(timezone.utc).replace(tzinfo=None) - expire_utc_time
        # formatting in time left
        #time_left = dt.timedelta(seconds=600) - time_delta
        #days, hours, minutes = time_left.days, time_left.seconds // 3600, time_left.seconds % 3600 // 60
        #seconds = time_left.seconds - hours * 3600 - minutes * 60
        #expire_in = f"{days}D {hours}h:{minutes}':{seconds}''"
        #print(expire_utc_time.year,
        #      expire_utc_time.month,
        #      expire_utc_time.day,
        #      expire_utc_time.hour,
        #      expire_utc_time.minute,
        #      expire_utc_time.second)
        #print(int(time_left.total_seconds() * 1000), expire_utc_time)
        return templates.TemplateResponse("download/download.html", {"request": request,
                                                                     "id": filename,
                                                                     # "expire_in": expire_in,
                                                                     "year": expire_utc_time.year,
                                                                     "month": expire_utc_time.month-1,
                                                                     "day": expire_utc_time.day,
                                                                     "hour": expire_utc_time.hour,
                                                                     "minute": expire_utc_time.minute,
                                                                     "second": expire_utc_time.second})
    except SignatureExpired:
        try:
            # check if is a file
            # Path(os.environ['DOWNLOAD_DIR'], str(id.rsplit('.', 2)[0])
            os.remove(Path(os.environ['DOWNLOAD_DIR'],
                           str(id.rsplit('.', 2)[0])))
        except OSError:
            pass
        except KeyError:
            return templates.TemplateResponse("download/expired.html", {"request": request, "id": id})
    except BadSignature:
        return templates.TemplateResponse("download/error.html", {"request": request, "id": id})
