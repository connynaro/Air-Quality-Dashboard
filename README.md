## Setup Environment - Anaconda

```
conda create --name main-ds python=3.10
conda activate main-ds
pip install -r requirements.txt
```

## Setup Environment - Shell/Terminal

```
mkdir proyek_analisis_data
cd proyek_analisis_data
pipenv install --python 3.10
pipenv shell
pip install -r requirements.txt
```

## Menjalankan Dashboard

```
cd Dashboard
streamlit run dashboard.py
```
