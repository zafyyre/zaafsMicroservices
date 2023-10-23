FROM ubuntu:20.04

LABEL maintainer="zali29@my.bcit.ca"

# Install required packages
RUN apt-get update -y && \
    apt-get install -y python3 python3-pip

# Copy the Python application files
COPY ./requirements.txt /app/requirements.txt
COPY . /app

# Set the working directory
WORKDIR /app

# Install Python dependencies
RUN pip3 install -r requirements.txt

# Use a single ENTRYPOINT and CMD instruction
ENTRYPOINT ["python3"]
CMD ["app.py"]
