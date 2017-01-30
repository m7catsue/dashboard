# -*- coding: utf-8 -*-
from bokeh.plotting import Figure
from bokeh.models import FixedTicker, CustomJS
from bokeh.models.widgets import Div
from bokeh.layouts import column, row, layout, gridplot, WidgetBox
from bokeh.io import curdoc


def make_streaming_plots(ajax_data_source, mode='web'):
    """
    使用AjaxDataSource绘制实时图像;
    在Figure中设置tools=[]以取消图像中默认的'pan'的功能,保证streamming图像不受意外的拖动干扰 [IMP]
    """
    if mode not in ['web', 'local']:
        raise ValueError("Error: 'mode' parameter must be 'web' or 'local'!")

    fig1 = Figure(plot_width=360, plot_height=240, title='Streaming模拟数据: 正弦函数',
                  y_range=(-1.5, 1.5), toolbar_location=None, logo=None, tools=[])
    fig1.line(x='x', y='y_sin', source=ajax_data_source, line_width=2, line_alpha=0.9, color='#2171b5')

    fig2 = Figure(plot_width=360, plot_height=240, title='Streaming模拟数据: 余弦函数',
                  y_range=(-1.5, 1.5), toolbar_location=None, logo=None, tools=[])
    fig2.line(x='x', y='y_cos', source=ajax_data_source, line_width=2, line_alpha=0.9, color='#cb181d')

    fig3 = Figure(plot_width=360, plot_height=240, title='Streaming模拟数据: [-1, 1)均匀分布',
                  y_range=(-2, 2), toolbar_location=None, logo=None, tools=[])
    fig3.circle('x', 'y_random', source=ajax_data_source, size=3, color="#2171b5", alpha=0.9)

    fig1.yaxis[0].ticker = FixedTicker(ticks=[-1.5, -1, -0.5, 0, 0.5, 1, 1.5])  # 设置y轴刻度
    fig2.yaxis[0].ticker = FixedTicker(ticks=[-1.5, -1, -0.5, 0, 0.5, 1, 1.5])
    fig3.yaxis[0].ticker = FixedTicker(ticks=[-2, -1, 0, 1, 2])

    for fig in [fig1, fig2, fig3]:            # 设置streaming图像的x轴属性(x轴刻度随着streaming数据而增大)
        fig.x_range.follow = "end"
        fig.x_range.follow_interval = 20      # follow_interval:整个x轴所显示的范围

    # 设置Streaming Widget
    div = Div(text="""<h4><b>对streaming数据的实时分析：</b></h4>
                      <p>当前图像<b>X轴</b>最右侧坐标点为：0</p>
                      <p>
                          (1)<b>正弦函数</b>最近50期的平均值为： 0;
                          (2)<b>余弦函数</b>最近50期的平均值为： 0;
                          (3)<b>均匀分布</b>最近50期的平均值为： 0.
                      <p/>
                    """,
              width=1200, height=20)
    callback = CustomJS(args=dict(source=ajax_data_source, div=div),
                        code="""
                        var data = source.data;
                        var space = '&nbsp;'           // "&nbsp;"表示"non breaking space"即一个空格 [IMP]
                        function arr_mean(arr) {
                            var sum = 0;
                            for (let i=0; i<arr.length; i++) {
                                sum = sum + arr[i]
                            }
                            return sum/arr.length;
                        }
                        //console.log(data['x'].length); console.log(data['x'].slice(-1)[0]);

                        // 更新Div Widget中的text内容;保留2位小数
                        div.text = "<h4><b>对streaming数据的实时分析：</b></h4>" +
                                   "<p>当前图像<b>X轴</b>最右侧坐标点为：<b>" + data['x'].slice(-1)[0].toFixed(2) + "</b></p>" +
                                   "<p>" +
                                      "(1)<b>正弦函数</b>最近50期的平均值为：<b>" + arr_mean(data['y_sin'].slice(-50)).toFixed(2) + "</b>." +
                                      space.repeat(3) +
                                      "(2)<b>正弦函数</b>最近50期的平均值为：<b>" + arr_mean(data['y_cos'].slice(-50)).toFixed(2) + "</b>." +
                                      space.repeat(3) +
                                      "(3)<b>均匀分布</b>最近50期的平均值为：<b>" + arr_mean(data['y_random'].slice(-50)).toFixed(2) + "</b>." +
                                   "</p>"
                        div.trigger('change');
                        """)

    ajax_data_source.js_on_change('change', callback)  # [IMP] 注意对AjaxDtaSource和Div(Paragraph)插件的设定('change')

    if mode == 'web':
        fig_layout = layout([fig1, fig2, fig3],
                            [div, ])
        return fig_layout
    if mode == 'local':
        document = curdoc()
        document.add_root(layout([fig1, fig2, fig3],
                                 [div, ]))
        return document


if __name__ == '__main__':
    import math
    import random
    import numpy as np
    from flask import Flask, jsonify
    from bokeh.models.sources import AjaxDataSource
    from bokeh.io import output_file, save, show
    from WebDevelopment.dashboard.decorators import crossdomain  # PycharmProjects目录属于sys.path

    x = list(np.arange(0, 2, 0.1))                         # 模拟数据
    y_sin = [math.sin(xi) for xi in x]
    y_cos = [math.cos(xi) for xi in x]
    y_random = [random.uniform(-1, 1) for i in range(20)]  # random.random()返回[0.0, 1.0)之间的浮点数

    ajax_source = AjaxDataSource(data=dict(x=x,
                                           y_sin=y_sin,
                                           y_cos=y_cos,
                                           y_random=y_random),
                                 data_url='http://localhost:5050/data',              # 每隔200ms访问data_url以获取数据
                                 polling_interval=200, mode='append', max_size=500)  # DataSource中每列所保留的最大长度为500

    doc = make_streaming_plots(ajax_source, mode='local')

    output_file('example_streaming.html')
    save(doc)

    app = Flask(__name__)

    @app.route('/data', methods=['GET', 'OPTIONS', 'POST'])
    @crossdomain(origin="*", methods=['GET', 'POST'], headers=None)
    def get_data():
        """生成streaming的模拟数据"""
        x.append(x[-1] + 0.1)
        y_sin.append(math.sin(x[-1]))
        y_cos.append(math.cos(x[-1]))
        y_random.append(random.uniform(-1, 1))
        return jsonify(x=x[-1], y_sin=y_sin[-1], y_cos=y_cos[-1], y_random=y_random[-1])

    app.run(debug=True, port=5050)




