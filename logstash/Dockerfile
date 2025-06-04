FROM logstash:8.15.0

ARG USER
ARG U_ID

ARG G_ID
ARG GROUP

USER root

RUN groupadd -r -g ${G_ID} ${GROUP}
RUN useradd -g ${GROUP} -u ${G_ID} ${GROUP}
RUN useradd -m -g ${GROUP} -G logstash -s /bin/bash -u ${U_ID} ${USER}

RUN chown -R ${USER}:${GROUP} /usr/share/logstash

RUN mkdir -p /db/sincedb /db/completed
RUN chown -R ${USER}:${GROUP} /db
RUN chmod 770 /db

USER ${USER}
