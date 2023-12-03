FROM ubuntu:20.04

LABEL maintainer="zali29@my.bcit.ca"

RUN apt-get update -y && \
    apt-get install -y python3 python3-pip

COPY ./requirements.txt /app/requirements.txt

WORKDIR /app

RUN pip3 install -r requirements.txt

COPY . /app

# Use a single ENTRYPOINT and CMD instruction
ENTRYPOINT ["python3"]
CMD ["app.py"]
