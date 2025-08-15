from fastapi.templating import Jinja2Templates
# from jinja2 import StrictUndefined

templates = Jinja2Templates(
    directory="aanvraagapp/templates",
    # undefined=StrictUndefined
)
