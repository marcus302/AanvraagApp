FROM python:3.13.3-bullseye

WORKDIR /app

COPY poetry.lock pyproject.toml README.md  ./
RUN pip install poetry==2.1.3
RUN poetry install --with dev --no-root
COPY aanvraagapp ./aanvraagapp
COPY tests ./tests
RUN poetry install --with dev

CMD ["poetry", "run", "python3", "-Xfrozen_modules=off", "-m", "debugpy", "--listen", "0.0.0.0:5678", "-m", "uvicorn", "aanvraagapp:app", "--reload", "--host", "0.0.0.0", "--port", "80"]
