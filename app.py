import torch
from PIL import Image
from flask import Flask
from flask import render_template, request, jsonify, session
from torchvision import transforms as T
import numpy as np
from facenet_pytorch import MTCNN, extract_face

from datetime import datetime
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time

class Timer:
    def __enter__(self):
        self.start = time.time()
        return self

    def __exit__(self, *args):
        self.end = time.time()
        self.interval = self.end - self.start

model = torch.load('models/resnet34_ft_albu_imb_4.pth', map_location=torch.device('cpu'))
model = model.module
mtcnn = MTCNN(select_largest=True, margin=10, post_process=False, device='cpu')
results = {"timestamp": [],
           "emotion": []
          }

img = None
app = Flask(__name__)
app.secret_key = 'my_secret_key'


def prepare_data(data, period='10s'):
    df = pd.DataFrame(data)
    df["datetime"] = pd.to_datetime(df.timestamp, unit='s')
    df = df.set_index('datetime')
    df = df.groupby([pd.Grouper(freq=period), 'emotion']).agg({'emotion': 'count'})
    df = df.loc[df.groupby(level=0)['emotion'].idxmax()]
    df.columns = ['cnt']
    df.cnt = 1
    df = df.reset_index()
    return df


def prepare_plot(df):
    graph_dict = {}
    fig = make_subplots(
        rows=1, cols=2,
        column_widths=[0.7, 0.3],
        specs=[[{"type": "bar"}, {"type": "pie"}]])

    emotions = ['happy', 'sad', 'anger', 'uncertain', 'fear', 'disgust', 'neutral', 'contempt', 'surprise']
    plotly_colors = ['#00CC96', '#636EFA', '#EF553B', '#AB63FA', '#FF6692', '#19D3F3', '#FFA15A', '#FF97FF', '#B6E880']
    colors = dict(zip(emotions, plotly_colors))
    for step in ['3s', '10s', '30s', '60s']:
        visible = False
        if step == '3s':
            visible = True
        data = prepare_data(df, period=step)
        pie = data.emotion.value_counts()
        pie_labels = pie.index.tolist()
        pie_colors = [colors[x] for x in pie_labels]
        graph_dict[step] = []
        for emo in data.emotion.unique():
            tmp = data[data['emotion'] == emo]
            graph_dict[step].append('bar')
            fig.add_trace(go.Bar(x=tmp.index, y=tmp.cnt.values, name=emo, marker_color=colors[emo], visible=visible),
                          row=1, col=1)
        graph_dict[step].append('pie')
        fig.add_trace(go.Pie(labels=pie.index, values=pie.values, showlegend=False,
                             marker_colors=pie_colors, hole=.3, visible=visible,
                             hovertemplate="%{label}<extra></extra>"), row=1, col=2)
    steps = []
    idx = 0
    num_traces = sum([len(x) for x in graph_dict.values()])
    for key, value in graph_dict.items():
        step = dict(
            method="update",
            args=[{"visible": [False] * num_traces},
                  {"title": "Slider switched to step: " + key}],
            label=key,
        )
        step["args"][0]["visible"][idx:idx + len(value)] = [True] * len(value)  # Toggle i'th trace to "visible"
        steps.append(step)
        idx += len(value)

    sliders = [dict(
        active=0,
        currentvalue={"prefix": "Frequency: "},
        pad={"t": 50},
        steps=steps)]

    fig.update_layout(
        sliders=sliders,
        hovermode='x',
        bargap=0,  # gap between bars of adjacent location coordinates.
        bargroupgap=0,  # gap between bars of the same location coordinate.
        legend=dict(
            title="Emotions",
            orientation='h',
            yanchor="top",
            y=-0.07,
            xanchor="left",
            x=0
        ),
        yaxis=dict(visible=False)
    )
    return fig


def image_preprocessing(img):
    transform = T.Compose([
        T.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])
    return transform(img / 255)


def predict(img):
    img = image_preprocessing(img)
    class_names = ['anger',
                   'contempt',
                   'disgust',
                   'fear',
                   'happy',
                   'neutral',
                   'sad',
                   'surprise',
                   'uncertain']

    _, preds = model(img.unsqueeze(0)).max(1)
    return class_names[preds]


@app.route('/test/')
def test():
    return render_template('test.html')

@app.route('/')
def index():
    if 'id' in session:
        first_time = False
    else:
        session['id'] = 1
        first_time = True
    return render_template('index.html', first_time=first_time)


@app.route('/check/', methods=["POST"])
def check():
    global results
    data = request.json
    if data['reset'] == "yes":
        session.pop('id')
        results = {"timestamp": [],
           "emotion": []
          }
        return jsonify({"status": "reset"})
    if data['reset'] == "no":
        results = session["results"]
        return jsonify({"status": "continue"})


@app.route('/plot/')
def plot():
    if results['emotion']:
        fig = prepare_plot(results)
        fig.write_html('templates/plot.html')
        return render_template('plot.html')
    else:
        return "<h5 class=\"text-center\"> No data available yet. </h5>"


@app.route('/detect/', methods=['POST'])
def detect():
    data = request.files['file']
    seq = request.form['seq']
    img = Image.open(data)
    with Timer() as t:
        bbox = mtcnn.detect(img)[0]
        if bbox is None:
            return jsonify({"status": "error"})
        bbox = bbox[0].astype(np.int).tolist()
        face = extract_face(img, bbox, image_size=224)
        emo = predict(face)
    results["emotion"].append(emo)
    results["timestamp"].append(datetime.timestamp(datetime.now()))
    session["results"] = results
    return jsonify({"status": "ok",
                    "timer": f"{t.interval:.3f}",
                    "seq": seq,
                    "emo": emo,
                    "x": bbox[0],
                    "y": bbox[1],
                    "w": bbox[2] - bbox[0],
                    "h": bbox[3] - bbox[1]})


if __name__ == '__main__':
    app.run(debug=True, port="8080")
