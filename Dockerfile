FROM python:alpine

WORKDIR /app

EXPOSE 5000

COPY requirements.txt ./

RUN pip install -r requirements.txt

COPY templates/* templates/
COPY *.py ./

CMD flask run --host '0.0.0.0'