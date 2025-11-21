FROM grafana/grafana:12.0.0

ARG UID
ARG USER

ARG GID
ARG GROUP

USER root

RUN apk add --no-cache shadow
RUN apk add sqlite

COPY grafana.sql /var/lib/grafana/grafana.sql
RUN sqlite3 /var/lib/grafana/grafana.db < /var/lib/grafana/grafana.sql

RUN groupadd -r -g ${GID} ${GROUP}
RUN useradd -g ${GROUP} -u ${GID} ${GROUP}
RUN useradd -m -g ${GROUP} -s /bin/bash -u ${UID} ${USER}

RUN groupadd grafana
RUN usermod -aG grafana ${USER}
RUN usermod -aG grafana grafana

RUN chown -R :grafana /var/lib/grafana
RUN chown -R :grafana /usr/share/grafana

RUN chmod -R 770 /var/lib/grafana
RUN chmod -R 770 /usr/share/grafana

USER ${USER}

