from fastapi.templating import Jinja2Templates
# from jinja2 import StrictUndefined

prompts = Jinja2Templates(
    directory="aanvraagapp/parsing/prompts",
    # undefined=StrictUndefined
)