FROM python:3.8-slim-buster

WORKDIR /geaservice

FROM python:3.8-slim-buster

ARG USER
ARG UID

ARG GID
ARG GROUP

WORKDIR /geaservice

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
RUN apt-get update
RUN apt-get install -y psmisc


COPY . .

RUN groupadd -r -g ${GID} ${GROUP}
RUN useradd -g ${GROUP} -u ${GID} ${GROUP}
RUN useradd -m -g ${GROUP} -s /bin/bash -u ${UID} ${USER}

USER ${USER}
