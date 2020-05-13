FROM ubuntu:20.04
RUN apt update && \
    apt install -y python3 python3-pip python3-dev && \
    mkdir /opt/app
WORKDIR /opt/app
EXPOSE 9121
COPY . /opt/app
RUN cd /opt/app/ && pip3 install -r requirements.txt 
CMD cd /opt/app/ && sh run.sh