FROM mcpstudio-candidate-input:e970c09287e35e2cf86f0b1c518df50fb14c92427b9111f12f2877f248be739d AS cleaned
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
CMD ["python", "/fixture/service_validation.py"]
