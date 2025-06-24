FROM mysql:8.0.35-debian

ARG UID
ARG USER

ARG GID
ARG GROUP

RUN groupdel -f games

RUN groupadd -r -g ${GID} ${GROUP}
RUN useradd -g ${GROUP} -u ${GID} ${GROUP}
RUN useradd -m -g ${GROUP} -G mysql -s /bin/bash -u ${UID} ${USER}


ENV MYSQL_ROOT_PASSWORD=DmXWr7oduBoo770HLxmaOyt7rt72WyGT3tljs4mUgPKginYYQE
ENV MYSQL_DATABASE=archappl
ENV MYSQL_USER=archappl
ENV MYSQL_PASSWORD=archappl

COPY archappl_mysql.sql /docker-entrypoint-initdb.d

USER ${USER}
