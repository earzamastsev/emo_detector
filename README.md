# emo_detector
# Emotion detector
-----

## Quick start:

* Clone code:

`git clone https://github.com/earzamastsev/emo_detector`

`git checkout master`


* Next, you need to install python packages (recommend to use venv):

`cd emo_detector`

`pip install -r requirements.txt`

* After installing you need to create database:

`mkdir db`

`python create_db.py`

* Now you may run web server (only for testing and develop propousals, for production - use gunicorn insteed).

`python app.py`


