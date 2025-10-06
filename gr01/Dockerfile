FROM grafana/grafana:12.3.0-17962464148-ubuntu

ARG UID
ARG USER

ARG GID
ARG GROUP

USER root

RUN groupadd -r -g ${GID} ${GROUP}
RUN useradd -g ${GROUP} -u ${GID} ${GROUP}
RUN useradd -m -g ${GROUP} -s /bin/bash -u ${UID} ${USER}

USER ${USER}
