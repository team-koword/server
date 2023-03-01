FROM python:3.8
RUN pip freeze > requirements.txt
RUN git clone https://github.com/facebookresearch/fastText.git
RUN cd fastText && pip install . && pip install --upgrade pip setuptools wheel && pip install six
WORKDIR /code
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
COPY . /code/app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7778", "--reload"]
