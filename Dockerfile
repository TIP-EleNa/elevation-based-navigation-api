FROM conda/miniconda2

# Grab requirements.txt.
ADD ./webapp/requirements.txt /tmp/requirements.txt

# Install dependencies
RUN pip install -qr /tmp/requirements.txt

# Add our code
ADD ./webapp /opt/webapp/
WORKDIR /opt/webapp

RUN conda update -n base -c defaults conda

RUN conda create -n elena-api python=3.8 gunicorn flask numpy networkx

RUN conda install -n elena-api -c conda-forge googlemaps osmnx

RUN conda update --all

# Setup CMD to use bash instead of shell
SHELL ["/bin/bash", "-c"]

# Remove corrupt files
CMD source activate elena-api && \ 
  rm /usr/local/envs/elena-api/conda-meta/.wh.ca-certificates-2019.11.27-0.json && \ 
  rm /usr/local/envs/elena-api/conda-meta/.wh.openssl-1.1.1d-h7b6447c_3.json && \ 
  rm /usr/local/envs/elena-api/conda-meta/.wh.python-3.8.0-h0371630_2.json && \ 
  rm /usr/local/envs/elena-api/conda-meta/.wh.tk-8.6.8-hbc83047_0.json && \
  rm /usr/local/envs/elena-api/conda-meta/.wh.readline-7.0-h7b6447c_5.json && \
  conda list && \ 
  gunicorn --bind 0.0.0.0:$PORT wsgi 