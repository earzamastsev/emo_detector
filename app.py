from PIL import Image
from flask import Flask
from flask import render_template, request, jsonify, session
from uuid import uuid1
from datetime import datetime
from visualizer import Visualizer
from emo_detector import EmoDetector
from flask_sqlalchemy import SQLAlchemy
from timer import Timer

visualizer = Visualizer()
emo_detector = EmoDetector()

app = Flask(__name__)
app.secret_key = 'my_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db/database.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Users(db.Model):
    __tablename__ = 'active-users'
    __table_args__ = { 'extend_existing': True }
    id = db.Column(db.Integer, primary_key=True)
    userid = db.Column(db.String(80), unique=False, nullable=False)
    emo = db.Column(db.String(25), unique=False, nullable=False)
    timestamp = db.Column(db.String(25), unique=False, nullable=False)


@app.route('/')
def index():
    if 'uuid' in session:
        first_time = False
    else:
        first_time = True
        session['uuid'] = uuid1().hex
    return render_template('index.html', first_time=first_time)

@app.route('/check/', methods=["POST"])
def check():
    data = request.json
    if data['reset'] == "yes":
        Users.query.filter_by(userid=session['uuid']).delete()
        db.session.commit()
        return jsonify({"status": "reset", 'uuid': session['uuid']})
    if data['reset'] == "no":
        return jsonify({"status": "continue", 'uuid': session['uuid']})

@app.route('/plot/')
def plot():
    rows = Users.query.filter_by(userid=session['uuid']).all()
    if rows:
        res_dict = {'timestamp':[], 'emotion':[] }
        for row in rows:
            res_dict['timestamp'].append(row.timestamp)
            res_dict['emotion'].append(row.emo)
        fig = visualizer.plot(res_dict)
        fig.write_html('templates/plot.html')
        return render_template('plot.html')
    else:
        return "<h5 class=\"text-center\"> No data available yet. </h5>"


@app.route('/detect/', methods=['POST'])
def detect():
    data = request.files['file']
    img = Image.open(data)
    with Timer() as t:
        result = emo_detector.predict(img)
    if result['status'] == 'error':
        return jsonify({"status": "error"})
    res = Users(userid=session['uuid'], emo=result['emotion'], timestamp=datetime.now())
    db.session.add(res)
    db.session.commit()
    return jsonify({"status": "ok",
                    "timer": f"{t.interval:.3f}",
                    "emo": result['emotion'],
                    "x": result['bbox'][0],
                    "y": result['bbox'][1],
                    "w": result['bbox'][2] - result['bbox'][0],
                    "h": result['bbox'][3] - result['bbox'][1]})

if __name__ == '__main__':
    db.create_all()
    app.run(debug=True, port="8080")
