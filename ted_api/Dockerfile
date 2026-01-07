FROM python:3.10
ARG USER
ARG UID

ARG GID
ARG GROUP

WORKDIR /ted_api

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

RUN groupdel -f dialout
RUN groupdel -f staff

RUN groupadd -r -g ${GID} ${GROUP}
RUN useradd -g ${GROUP} -u ${GID} ${GROUP}
RUN useradd -m -g ${GROUP} -s /bin/bash -u ${UID} ${USER}

USER ${USER}
