import fastapi
from models.datasource import Datasource
from fastapi.responses import HTMLResponse
from services import bokeh_service
from worker import fake_compress
import re
import uuid
import base64
from infrastructure.api_cache import set_data
router = fastapi.APIRouter()


@router.post('/api/post_datasource',
             name='post_datasource',
             status_code=201,
             response_model=Datasource,
             response_class=HTMLResponse)
async def post_datasource(data: Datasource):
    # generate a post request ID
    return HTMLResponse(content=bokeh_service.get_dashboard_script(data.json()), status_code=200)


@router.post('/api/compress')
async def enqueue_compress(dl: Datasource):
    # We use celery delay method in order to enqueue the task with the given parameters
    rv = base64.b64encode(uuid.uuid4().bytes).decode('utf-8')
    transaction_id = re.sub(r'[\=\+\/]', lambda m: {'+': '-', '/': '_', '=': ''}[m.group(0)], rv)
    print("#################################   ", transaction_id, dl.data)
    # TODO: set NOW the status of the transaction to 'in-progress' by adding a new data key 'status'
    status = {"status": False}
    set_data(transaction_id, status)
    fake_compress.delay(dl.data, dl.email, transaction_id)
    return {"transaction_id": transaction_id}


# TODO: add a api method covered by log-in which can be used to clean-up the download forlder from expired downloads