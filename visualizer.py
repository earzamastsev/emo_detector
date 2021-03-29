import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots



class Visualizer:
    def __init__(self):
        self.data = None
        self.emotions = ['happy', 'sad', 'anger', 'uncertain', 'fear', 'disgust', 'neutral', 'contempt', 'surprise']
        self.plotly_colors = ['#00CC96', '#636EFA', '#EF553B', '#AB63FA', '#FF6692', '#19D3F3', '#FFA15A', '#FF97FF', '#B6E880']
        self.colors = dict(zip(self.emotions, self.plotly_colors))
        self.intervals = ['3s', '10s', '30s', '60s']

    def _prepare_data(self, data, period='10s'):
        df = pd.DataFrame(data)
        df["datetime"] = pd.to_datetime(df.timestamp)
        df = df.set_index('datetime')
        df = df.groupby([pd.Grouper(freq=period), 'emotion']).agg({'emotion': 'count'})
        df = df.loc[df.groupby(level=0)['emotion'].idxmax()]
        df.columns = ['cnt']
        df.cnt = 1
        df = df.reset_index()
        return df


    def plot(self, row_data):
        graph_dict = {}
        fig = make_subplots(
            rows=1, cols=2,
            column_widths=[0.7, 0.3],
            specs=[[{"type": "bar"}, {"type": "pie"}]])

        for step in self.intervals:
            visible = False
            if step == '3s':
                visible = True
            df = self._prepare_data(row_data, period=step)
            pie = df.emotion.value_counts()
            pie_labels = pie.index.tolist()
            pie_colors = [self.colors[x] for x in pie_labels]
            graph_dict[step] = []
            for emo in df.emotion.unique():
                tmp = df[df['emotion'] == emo]
                graph_dict[step].append('bar')
                fig.add_trace(go.Bar(x=tmp.index, y=tmp.cnt.values, name=emo, marker_color=self.colors[emo], visible=visible),
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
            step["args"][0]["visible"][idx:idx + len(value)] = [True] * len(value)
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
            bargap=0,
            bargroupgap=0,
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
