FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN pip list

COPY . .

CMD ["gunicorn", "foodgram.wsgi:application", "-b", "0.0.0.0:8000"]