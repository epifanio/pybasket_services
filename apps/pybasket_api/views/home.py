import fastapi
from starlette.requests import Request
from starlette.templating import Jinja2Templates


templates = Jinja2Templates('/app/templates')
router = fastapi.APIRouter()


@router.get('/', include_in_schema=False)
async def index(request: Request):
    # events = await report_service.get_reports()
    location = {'city': 'city', 'country': 'country'}
    events = {'location': location, 'description': 'description'}
    data = {'request': request, 'events': events}

    return templates.TemplateResponse('home/index.html', data)


@router.get('/favicon.ico', include_in_schema=False)
def favicon():
    return fastapi.responses.RedirectResponse(url='/static/img/met-logo.ico')