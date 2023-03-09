import fastapi
from models.datasource import Datasource
from fastapi.responses import HTMLResponse
from services import bokeh_service
from worker import fake_compress, generate_spec, generate_spec2, fake_compress2
import re
import uuid
import base64
from infrastructure.api_cache import set_data

router = fastapi.APIRouter()
import os

from itsdangerous import TimestampSigner
from itsdangerous import BadSignature, SignatureExpired


@router.post(
    "/api/post_datasource",
    name="post_datasource",
    status_code=201,
    response_model=Datasource,
    response_class=HTMLResponse,
)
async def post_datasource(data: Datasource):
    # generate a post request ID
    return HTMLResponse(
        content=bokeh_service.get_dashboard_script(data.json()), status_code=200
    )


@router.post("/api/compress")
async def enqueue_compress(dl: Datasource):
    # We use celery delay method in order to enqueue the task with the given parameters
    rv = base64.b64encode(uuid.uuid4().bytes).decode("utf-8")
    transaction_id = re.sub(
        r"[\=\+\/]", lambda m: {"+": "-", "/": "_", "=": ""}[m.group(0)], rv
    )
    print("#################################   ", transaction_id, dl.data)
    # TODO: set NOW the status of the transaction to 'in-progress' by adding a new data key 'status'
    status = {"status": False}
    set_data(
        transaction_id=transaction_id,
        data=status,
        redishost=os.environ["REDIS_HOST"],
        password=os.environ["REDIS_PASSWORD"],
    )
    fake_compress.delay(dl.data, dl.email, transaction_id)
    return {"transaction_id": transaction_id}


@router.post("/api/compress_spec")
async def enqueue_compress2(dl: Datasource):
    # We use celery delay method in order to enqueue the task with the given parameters
    rv = base64.b64encode(uuid.uuid4().bytes).decode("utf-8")
    transaction_id = re.sub(
        r"[\=\+\/]", lambda m: {"+": "-", "/": "_", "=": ""}[m.group(0)], rv
    )
    print("#################################   ", transaction_id, dl.data)
    # TODO: set NOW the status of the transaction to 'in-progress' by adding a new data key 'status'
    status = {"status": False}
    set_data(
        transaction_id=transaction_id,
        data=status,
        redishost=os.environ["REDIS_HOST"],
        password=os.environ["REDIS_PASSWORD"],
    )
    fake_compress2.delay(dl.data, dl.notebooks, transaction_id)
    return {"transaction_id": transaction_id}


@router.post("/api/getspec")
async def enqueue_getspec(dl: Datasource):
    # We use celery delay method in order to enqueue the task with the given parameters
    rv = base64.b64encode(uuid.uuid4().bytes).decode("utf-8")
    transaction_id = re.sub(
        r"[\=\+\/]", lambda m: {"+": "-", "/": "_", "=": ""}[m.group(0)], rv
    )
    print("#################################   ", transaction_id, dl.data)
    # TODO: set NOW the status of the transaction to 'in-progress' by adding a new data key 'status'
    status = {"status": False}
    set_data(
        transaction_id=transaction_id,
        data=status,
        redishost=os.environ["REDIS_HOST"],
        password=os.environ["REDIS_PASSWORD"],
    )
    print("this is what we get", dl)
    generate_spec.delay(dl.data, dl.notebooks, transaction_id)
    return {"transaction_id": transaction_id}


@router.post("/api/getspec2")
async def enqueue_getspec2(dl: Datasource):
    # We use celery delay method in order to enqueue the task with the given parameters
    rv = base64.b64encode(uuid.uuid4().bytes).decode("utf-8")
    transaction_id = re.sub(
        r"[\=\+\/]", lambda m: {"+": "-", "/": "_", "=": ""}[m.group(0)], rv
    )
    print("#################################   ", transaction_id, dl.data)
    # TODO: set NOW the status of the transaction to 'in-progress' by adding a new data key 'status'
    status = {"status": False}
    set_data(
        transaction_id=transaction_id,
        data=status,
        redishost=os.environ["REDIS_HOST"],
        password=os.environ["REDIS_PASSWORD"],
    )
    s = TimestampSigner("secret-key")
    download_token_string = transaction_id + ".yaml"
    download_token = s.sign(download_token_string).decode()
    generate_spec2.delay(dl.data, transaction_id, download_token)
    return {"transaction_id": transaction_id, "download_token": download_token}


# TODO: add a api method covered by log-in which can be used to clean-up the download forlder from expired downloads
