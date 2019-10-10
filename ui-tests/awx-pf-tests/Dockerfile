FROM cypress/included:3.3.2
RUN apt-get update && \
    apt-get install -y make build-essential libssl-dev zlib1g-dev && \
    apt-get install -y libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm && \
    apt-get install -y libncurses5-dev libncursesw5-dev xz-utils tk-dev
RUN wget https://www.python.org/ftp/python/3.6.4/Python-3.6.4.tgz && \
    tar xvf Python-3.6.4.tgz && \
    cd Python-3.6.4 && \
    ./configure --enable-optimizations && \
    make -j8 && \
    make altinstall
RUN apt-get install -y python3-pip python-virtualenv
RUN virtualenv -p python3.6 /venv-awxkit
RUN /venv-awxkit/bin/pip3.6 install nodeenv
RUN git clone https://github.com/ansible/awx
RUN venv-awxkit/bin/pip3.6 install -r awx/awxkit/requirements.txt
RUN cd awx/awxkit && /venv-awxkit/bin/python3.6 setup.py install
ENTRYPOINT ["/bin/bash", "-c", "source /venv-awxkit/bin/activate && cypress run"]
