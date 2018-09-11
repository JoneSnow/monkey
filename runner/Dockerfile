FROM python:2

RUN apt-get update && \
    apt-get install -y android-tools-adb && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /usr/src/app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . ./runner

CMD [ "python", "./runner/Runner.py" ]