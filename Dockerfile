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
RUN pip3 install -e '.[testing]' --break-system-packages
ENTRYPOINT [ "ispl" ]


# # RUN apt install -qq -y build-essential zlib1g-dev \
# #     wget libncurses5-dev libgdbm-dev libnss3-dev \
# #     libssl-dev libreadline-dev libffi-dev libsqlite3-dev wget libbz2-dev
# # RUN wget https://www.python.org/ftp/python/3.10.12/Python-3.10.12.tgz
# # RUN tar -xf Python-3.10.12.tgz
# # RUN cd Python-3.10.12
# # RUN ./configure --enable-optimizations
# # RUN make -j 8
# # RUN sudo make altinstall
# # RUN apt install -qq -y build-essential zlib1g-dev curl 
# RUN apt-get update -qq && apt-get install -qq -y \
#     build-essential \
#     libssl-dev \
#     zlib1g-dev \
#     libbz2-dev \
#     libreadline-dev \
#     libsqlite3-dev \
#     wget \
#     curl \
#     llvm \
#     libncurses5-dev \
#     libncursesw5-dev \
#     xz-utils \
#     tk-dev \
#     libffi-dev \
#     liblzma-dev \
#     python-openssl \
#     git curl
# RUN curl https://pyenv.run | bash
# RUN export PYENV_ROOT="$HOME/.pyenv" \
#     && [[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH" \
#     && eval "$(pyenv init - bash)" \
#     && pyenv install 3.10.12 && pyenv global 3.10.12

# # ENV PATH="/root/.pyenv/bin:$PATH"
# # RUN eval "$(pyenv init -)" && pyenv install 3.10.12
# # RUN pyenv install 3.10.12
# RUN 