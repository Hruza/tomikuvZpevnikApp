FROM python:3.12-slim-bookworm AS build
ENV PYTHONUNBUFFERED=1
WORKDIR /tomikuvzpevnik

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt
RUN apt-get update && \
    apt-get install -y locales && \
    sed -i -e 's/# cs_CZ.UTF-8 UTF-8/cs_CZ.UTF-8 UTF-8/' /etc/locale.gen && \
    dpkg-reconfigure --frontend=noninteractive locales

ENV LANG=cs_CZ.UTF-8
ENV LC_NUMERIC=cs_CZ.UTF-8
COPY . .