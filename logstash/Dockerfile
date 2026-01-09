FROM logstash:9.1.4

ARG USER
ARG UID

ARG GID
ARG GROUP

USER root

RUN groupadd -r -g ${GID} ${GROUP} && \
    useradd -m -u ${UID} -g ${GROUP} -G logstash -s /bin/bash ${USER}

RUN chown -R ${USER}:${GROUP} /usr/share/logstash

RUN mkdir -p /db/sincedb /db/completed && \
    chown -R ${USER}:${GROUP} /db && \
    chmod 770 /db

USER ${USER}