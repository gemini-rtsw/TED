FROM elasticsearch:8.11.1

ARG USER
ARG UID

ARG GID
ARG GROUP

RUN groupadd -r -g ${GID} ${GROUP}
RUN useradd -g ${GROUP} -u ${GID} ${GROUP}
RUN useradd -m -g ${GROUP} -G elasticsearch -s /bin/bash -u ${UID} ${USER}

RUN chown -R ${USER}:${GROUP} /usr/share/elasticsearch

USER ${USER}
