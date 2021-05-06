FROM python:3
ENV PYTHONUNBUFFERED 1
RUN mkdir /code
WORKDIR /code
COPY requirements.txt /code/
RUN pip install -r requirements.txt
COPY . /code

# copy entrypoint.sh
COPY ./entrypoint.sh /code/entrypoint.sh

# run entrypoint.sh
ENTRYPOINT ["/code/entrypoint.sh"]
