FROM condaforge/miniforge3:24.11.3-2
ARG CERTIFICATE_VERSION=1.138IGTFNEW

RUN apt-get update -y && apt-get install gnupg2 netcat-traditional jq -y

RUN conda install --yes \
    -c conda-forge \
    conda-build \
    xrootd==5.6.9 \
    && conda build purge-all && conda clean -ti

RUN apt update && \
    apt upgrade -y && \
    apt install -y sudo

RUN mkdir -p /etc/grid-security/
RUN export X509_CERT_DIR=/etc/grid-security/certificates/
RUN wget https://repo.opensciencegrid.org/cadist/${CERTIFICATE_VERSION}/osg-certificates-${CERTIFICATE_VERSION}.tar.gz
RUN tar -xvf osg-certificates-${CERTIFICATE_VERSION}.tar.gz -C /etc/grid-security/

# Use existing UID 1000 user (typically 'ubuntu') and add to sudo group
RUN usermod -aG sudo $(getent passwd 1000 | cut -d: -f1) || true
RUN mkdir -p /etc/grid-security/certificates /etc/grid-security/vomsdir

ADD gai.conf /etc/gai.conf

# COPY requirements.txt .
# COPY requirements.lock .
# RUN /opt/conda/bin/pip install safety==1.9.0

# RUN safety check -r requirements.lock
# RUN /opt/conda/bin/pip --no-cache-dir install \
#     --upgrade \
#     --no-deps \
#     --require-hashes \
#     --requirement requirements.lock

# WORKDIR /servicex
# COPY proxy-exporter.sh .
# RUN chmod +x proxy-exporter.sh

ENV PYTHONUNBUFFERED=1
ENV X509_USER_PROXY=/tmp/x509up_u1000

RUN chgrp -R 0 /home/ubuntu && chmod -R g+rwX /home/ubuntu || true
WORKDIR /home/ubuntu

# Switch to UID 1000 user
USER 1000