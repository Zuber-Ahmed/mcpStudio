FROM mcpstudio-os-input:ea6891d3e54f5d50597f2f27ede69385033f33afe20dcb5651e82675d4d6f762 AS cleaned
USER root
RUN mkdir -p /opt/os-review && dpkg-query -W > /opt/os-review/os-before.tsv && apt-get update && apt-get -y upgrade && dpkg-query -W > /opt/os-review/os-after.tsv && rm -rf /var/lib/apt/lists/*
FROM scratch
COPY --from=cleaned / /
ENV PATH="/usr/local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
ENV LANG="C.UTF-8"
ENV PYTHON_VERSION="3.14.10"
ENV PYTHON_SHA256="de414a57119abef52784d8993e341d53aed635fc2b05c2607d9f98a2c5b72032"
ENV PYTHONDONTWRITEBYTECODE="1"
WORKDIR /fixture
USER 65534:65534
CMD ["python", "/fixture/worker-readiness.py"]
