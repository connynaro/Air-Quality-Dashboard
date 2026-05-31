# Proyek Analisis Data: Kualitas Udara Beijing

Dashboard interaktif untuk menganalisis kualitas udara (PM2.5) di 12 stasiun pemantauan di Beijing periode 2013–2017, dibuat menggunakan Streamlit.

## Setup Environment - Anaconda

conda create --name main-ds python=3.9
conda activate main-ds
pip install -r requirements.txt

## Setup Environment - Shell/Terminal

mkdir proyek_analisis_data
cd proyek_analisis_data
pipenv install
pipenv shell
pip install -r requirements.txt

## Menjalankan Dashboard

Setelah dijalankan, dashboard akan otomatis terbuka di browser pada alamat `http://localhost:8501`.