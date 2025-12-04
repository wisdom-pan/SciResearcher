FROM m.daocloud.io/docker.io/library/python:3.10-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1



COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://mirrors.cloud.tencent.com/pypi/simple

COPY . .

RUN mkdir -p data logs

EXPOSE 7860

CMD ["python", "gradio_app.py"]
