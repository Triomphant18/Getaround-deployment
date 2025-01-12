FROM continuumio/miniconda3

WORKDIR home/app

COPY ../app.py app.py

RUN apt-get update

RUN pip install --upgrade pip
RUN pip install pandas plotly.express streamlit numpy openpyxl

CMD streamlit run --server.port $PORT app.py