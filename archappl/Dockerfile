FROM tomcat:9.0.80-jdk21-openjdk-slim-bullseye

ARG USER
ARG UID

ARG GID
ARG GROUP
#-----Enviroment stage ---------------------------------------
ENV JAVA_OPTS="-XX:+UseG1GC -Xms4G -Xmx4G -ea"
ENV ARCHAPPL_ALL_APPS_ON_ONE_JVM=true
ENV ARCHAPPL_APPLIANCES=/etc/archappl/appliances.xml
ENV ARCHAPPL_POLICIES=/etc/archappl/policies.py
ENV ARCHAPPL_PROPERTIES_FILENAME=/etc/archappl/archappl.properties
ENV ARCHAPPL_SHORT_TERM_FOLDER=/storage/sts
ENV ARCHAPPL_LONG_TERM_FOLDER=/storage/lts

#----Copy stage-----------------------------------------------
COPY \lib \lib
COPY \bin \bin

#----Run stage-----------------------------------------------
RUN apt update && apt install -y python3
RUN groupdel -f dialout

RUN groupadd -r -g ${GID} ${GROUP}
RUN useradd -g ${GROUP} -u ${GID} ${GROUP}
RUN useradd -m -g ${GROUP} -s /bin/bash -u ${UID} ${USER}

RUN mkdir -p /storage
#linked files for a centralized configuration
RUN rm /usr/local/tomcat/conf/server.xml && ln -s /etc/archappl/server.xml /usr/local/tomcat/conf/server.xml
RUN rmdir /usr/local/tomcat/logs && ln -s /storage/logs /usr/local/tomcat/logs

RUN chown -R ${USER}:${GROUP} /usr/local/tomcat
RUN chown -R ${USER}:${GROUP} /storage

USER ${USER}

EXPOSE 17665

