FROM mcpstudio-minimal-input:bd320540b91dabf4f7fabe7bef85aefea4745d256895bbd6b2261c562db22049 AS assembler
USER root
COPY build-minimal-root.py /tmp/build-minimal-root.py
RUN python /tmp/build-minimal-root.py
FROM scratch
COPY --from=assembler /candidate-root /
ENV PATH="/usr/local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
ENV LANG="C.UTF-8"
ENV PYTHON_VERSION="3.14.10"
ENV PYTHON_SHA256="de414a57119abef52784d8993e341d53aed635fc2b05c2607d9f98a2c5b72032"
ENV PYTHONDONTWRITEBYTECODE="1"
WORKDIR /fixture
USER 65534:65534
CMD ["python", "/fixture/service_validation.py"]
