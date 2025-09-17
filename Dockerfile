# syntax=docker/dockerfile:1

FROM python:3.8-slim-bookworm

RUN apt-get update && \
    apt-get install -y locales && \
    sed -i -e 's/# es_ES.UTF-8 UTF-8/es_ES.UTF-8 UTF-8/' /etc/locale.gen && \
    dpkg-reconfigure --frontend=noninteractive locales

ENV LANG es_ES.UTF-8
ENV LC_ALL es_ES.UTF-8
ENV TZ Europe/Madrid

WORKDIR /app

# Copy all project files into the container
COPY . .

# Make the startup script executable
RUN chmod +x ./start.sh

RUN pip3 install -r requirements.txt

RUN mkdir /data
RUN mkdir /logs

CMD [ "./start.sh" ]