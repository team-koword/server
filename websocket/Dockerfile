FROM python:3.8

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

#COPY . /code/
COPY . .

#ENV NEW_RELIC_CONFIG_FILE=newrelic.ini

#CMD ["sh", "-c", "NEW_RELIC_CONFIG_FILE=newrelic.ini", "newrelic-admin", "run-program", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
#CMD ["gunicorn", "main:app", "--worker-class", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000"]
#CMD ["newrelic-admin", "run-program", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
