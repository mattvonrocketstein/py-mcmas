# WARNING: Compilation fails with newer debian due to conflicting bison version
FROM ghcr.io/mattvonrocketstein/mcmas:v1.3.0 AS mcmas
FROM python:3.11-slim-bookworm
COPY --from=mcmas /usr/local/bin/mcmas /usr/local/bin/mcmas
RUN apt-get -qq update && apt-get install -qq -y make procps curl jq
RUN curl -fsSL https://get.docker.com -o get-docker.sh && bash get-docker.sh
RUN mkdir /opt/py-mcmas
COPY . /opt/py-mcmas
WORKDIR /opt/py-mcmas
RUN pip3 install -e '.[ai]' --break-system-packages
RUN pip3 install -e '.[dev]' --break-system-packages
RUN pip3 install -e '.[docs]' --break-system-packages
RUN pip3 install -e '.[testing]' --break-system-packages
ENTRYPOINT [ "ispl" ]
