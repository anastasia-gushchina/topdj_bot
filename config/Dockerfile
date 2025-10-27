FROM python:3.13

RUN mkdir /app

RUN apt update && python -m pip install --upgrade pip

WORKDIR /app

# Installing dependencies into venv
COPY /requirements /requirements

RUN pip install virtualenv
RUN virtualenv -p python venv
RUN /bin/bash -c "source venv/bin/activate" && \
    pip install --upgrade setuptools && pip install -r /requirements/base.txt

# Copy source code
COPY . .

# Run entrypoint
ENTRYPOINT ["/app/config/docker-entrypoint.sh"]
