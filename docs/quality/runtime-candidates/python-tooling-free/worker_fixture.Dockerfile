FROM mcpstudio-candidate-input:5cd2e089643a7c47f7c0fe4feaf81b0191834d51e9b9190a128a87a796846af4 AS cleaned
USER root
COPY prune.py /tmp/prune.py
RUN python /tmp/prune.py && rm /tmp/prune.py
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
