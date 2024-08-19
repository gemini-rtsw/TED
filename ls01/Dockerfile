FROM logstash:8.15

ARG USER
ARG UID

ARG GID
ARG GROUP

USER root

RUN groupadd -r -g ${GID} ${GROUP}
RUN useradd -g ${GROUP} -u ${GID} ${GROUP}
RUN useradd -m -g ${GROUP} -G logstash -s /bin/bash -u ${UID} ${USER}

RUN chown -R ${USER}:${GROUP} /usr/share/logstash

USER ${USER}
