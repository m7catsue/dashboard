# -*- coding: utf-8 -*-
import math
from bokeh.layouts import column, row, layout, gridplot, WidgetBox
from bokeh.models import CustomJS, DatetimeTickFormatter, FixedTicker, Legend, \
    HoverTool, PanTool, WheelZoomTool, BoxZoomTool, ResetTool
from bokeh.models.widgets import CheckboxButtonGroup, Select
from bokeh.plotting import Figure
from bokeh.io import curdoc


def make_line_plot(data_source, mode='web'):
    """
    作带有widgets的线图;
    [IMP] 在CustomJS的Javascript代码中:
          (1)对于不显示的直线,使用 null 或 者undefined 或者 NaN; 使用null会导致数值为0,undefined和NaN则不完全显示;
          (2)比较array: JSON.stringify(a1) === JSON.stringify(a2);
          (3)判断array中是否包含某个元素: array.includes(element)返回ture/false;
    [INFO] line_alpha(直线透明度): floating point between 0 (transparent) and 1 (opaque)
    """
    if mode not in ['web', 'local']:
        raise ValueError("Error: 'mode' parameter must be 'web' or 'local'!")

    # [IMP] 使用cur_xxx_val作为tooltips的显示:
    # 应为当隐藏部分直线时,CustomJS回掉函数对DataSource中的plt_xxx_val列全部值设为undefined,对于undefined值tooltips会显示'???'.
    hover = HoverTool(tooltips=[("日期 ", "@date_str"),
                                ("最大值 ", "@cur_max_val"),
                                ("平均值 ", "@cur_mean_val"),
                                ("最小值 ", "@cur_min_val")],
                      point_policy='follow_mouse')

    fig = Figure(plot_width=950, plot_height=300, x_axis_type="datetime",                # 时间序列需设置x_axis_type
                 tools=[ResetTool(), PanTool(), WheelZoomTool(), BoxZoomTool(), hover],  # 设置toolbar_location=None不显示toolbar
                 toolbar_location='above', logo=None)                                    # 设置logo=None不显示bokeh logo
    fig.line(x='date', y='plt_max_val', source=data_source, line_width=2, line_alpha=0.5, line_color='#cb181d',
             legend='日最大值')
    fig.line(x='date', y='plt_mean_val', source=data_source, line_width=2, line_alpha=0.9, line_color='#2171b5',
             legend='日平均值')
    fig.circle(x='date', y='plt_mean_val', source=data_source, size=3, color="#2171b5", alpha=0.9,
               legend='日平均值')
    fig.line(x='date', y='plt_min_val', source=data_source, line_width=2, line_alpha=0.5, line_color='#238b45',
             legend='日最小值')

    # [IMP] 设置线图的属性
    fig.title.text = '北京市PM2.5日均浓度变化趋势(ug/m3)'                                   # 初始显示'北京市'数据;title由CustomJS回调函数动态更新
    fig.xaxis.axis_label = 'Date'
    fig.xaxis[0].ticker.desired_num_ticks = 12                                           # 坐标轴ticker的频率(desired_num_ticks) [IMP]
    fig.xaxis.formatter = DatetimeTickFormatter(hours=["%Y-%m-%d"], days=["%Y-%m-%d"],   # 坐标轴datetime的显示格式 [IMP]
                                                months=["%Y-%m-%d"], years=["%Y-%m-%d"])
    fig.xaxis.major_label_orientation = math.pi / 12
    fig.yaxis.axis_label = 'PM2.5 Concentration (ug/m3)'
    fig.yaxis[0].ticker.desired_num_ticks = 12

    # 设置legend属性(legend在figure内)
    fig.legend.location = 'top_right'                              # default: 'top_right'
    fig.legend.margin = 8                                         # legend距离figure边缘的距离(default: 10)
    fig.legend.padding = 3                                        # legend内的pading(default: 10)
    fig.legend.spacing = 1                                        # legend内的行间隔(default: 3)
    fig.legend.glyph_height, fig.legend.glyph_width = 10, 10      # legend内的图例图像的高度/宽度(default: 20)
    fig.legend.label_height, fig.legend.label_width = 10, 10      # legend内的文字标签的高度/宽度(default: 20)
    fig.legend.label_text_font_size = '4pt'                       # 文字大小(default 10)

    # 定义legend(在figure范围外显示legend: 需定义line_max/line_mean/patch_mean/line_min=fig.line()/fig.circle)
    #legend = Legend(items=[('日最大值', [line_max, ]),
                           #('日平均值', [line_mean, patch_mean]),
                           #('日最小值', [line_min, ])],
                    #location=(0, 0),
                    #spacing=1, label_text_font_size='2pt',
                    #glyph_height=15, glyph_width=20,
                    #label_height=15, label_width=20)
    #fig.add_layout(legend, 'right')

    select_metrics = CheckboxButtonGroup(labels=['最小值', '最大值'], active=[0, 1], height=50, width=130)
    select_city = Select(title='选择城市：', value='beijing', height=50, width=130,
                         options=[('beijing', '北京'), ('chengdu', '成都'),
                                  ('guangzhou', '广州'), ('shanghai', '上海'), ('shenyang', '沈阳')])

    # 为实现多个widgets之间选择的联动,为所有widgets设置一个通用的回调函数 [IMP]
    generic_callback = CustomJS(args=dict(source=data_source,
                                          select_city_obj=select_city,
                                          select_metrics_obj=select_metrics,
                                          target_obj=fig),
                                code="""
                                    // [IMP] 多个wigets共用的callback函数: 需先判断变量是否为undefined;
                                    // 当某个widget第一次被使用之后,其对应的变量才会存在,否则为undefined;
                                    // e.g. 在第一次操作wigets时,如果用户使用select_metrics,则变量metrics存在,但变量city为undefined,
                                    //      直到select_city被第一次试用之后,变量city才存在
                                    var data = source.data;                        // object
                                    var city = select_city_obj.value;              // 当前选择的城市: string
                                    var metrics = select_metrics_obj.active;       // 当前选择的指标: arrary/list
                                    var mapping = {
                                        beijing: ['bj_min_val', 'bj_mean_val', 'bj_max_val', '北京市'],
                                        chengdu: ['cd_min_val', 'cd_mean_val', 'cd_max_val', '成都市'],
                                        guangzhou: ['gz_min_val', 'gz_mean_val', 'gz_max_val', '广州市'],
                                        shanghai: ['sh_min_val', 'sh_mean_val', 'sh_max_val', '上海市'],
                                        shenyang: ['sy_min_val', 'sy_mean_val', 'sy_max_val', '沈阳市']
                                    };

                                    // 初始plt_xxx_val是beijing的值:这里不如下设置话,若用户一直未操作select_city,
                                    // 先使用select_metrics取消显示'最小(大)值',再想使用select_metrics恢复显示'最小(大)值',则无法恢复显示,
                                    // 因为取消显示时已设置data['plt_min_val'][i] = undefined,回调函数再运行时须复原plt_xxx_val各列的值;
                                    data['plt_min_val'] = data['bj_min_val'].slice();
                                    data['plt_mean_val'] = data['bj_mean_val'].slice();
                                    data['plt_max_val'] = data['bj_max_val'].slice();

                                    // 根据city对所有metrics(min/mean/max)的array进行赋值(若select_city有赋值,则覆盖上面定义的plt_xxx_val各列);
                                    // cur_xx_val用于tooltips的显示;plt_xx_vat用于作图;
                                    if (city != undefined) {
                                        data['cur_min_val'] = data[mapping[city][0]].slice();
                                        data['cur_mean_val'] = data[mapping[city][1]].slice();
                                        data['cur_max_val'] = data[mapping[city][2]].slice();
                                        data['plt_min_val'] = data[mapping[city][0]].slice();
                                        data['plt_mean_val'] = data[mapping[city][1]].slice();
                                        data['plt_max_val'] = data[mapping[city][2]].slice();
                                    }
                                    // 若不包含某个metric,将其对应的array全部赋值为undefined;
                                    if (metrics != undefined) {
                                        if (metrics.includes(0) === false) {
                                            for (let i=0; i<data['date'].length; i++) {
                                                data['plt_min_val'][i] = undefined;
                                            }
                                        }
                                        if (metrics.includes(1) === false) {
                                            for (let i=0; i<data['date'].length; i++) {
                                                data['plt_max_val'][i] = undefined;
                                            }
                                        }
                                    }
                                    // 更新title [IMP]
                                    target_obj.title.text = mapping[city][3] + 'PM2.5日均浓度变化趋势(ug/m3)';

                                    source.trigger('change');
                                    target_obj.trigger('change');
                                """)

    select_metrics.callback = generic_callback
    select_city.callback = generic_callback

    if mode == 'web':
        fig_layout = row(children=[column(children=[select_city, select_metrics], sizing_mode='fixed'), fig],
                         sizing_mode='fixed')
        return fig_layout
    if mode == 'local':
        document = curdoc()
        document.add_root(row(children=[column(children=[select_city, select_metrics], sizing_mode='fixed'), fig],
                              sizing_mode='fixed'))
        return document


if __name__ == '__main__':
    import os
    import sqlite3
    import pandas as pd
    from bokeh.models import ColumnDataSource
    from bokeh.io import output_file, save

    basedir = os.path.abspath(os.path.dirname(__file__))             # 本文件所在文件夹的绝对路径
    db_dir = os.path.dirname(basedir)                                # sqlite所在的路径(base_dir的上一级路径)

    with sqlite3.connect(os.path.join(db_dir, 'db_tmp.db')) as conn:
        df = pd.read_sql("SELECT * FROM aqi_data", con=conn)         # dataframe columns: 'city', 'date', 'mean_val', 'min_val', 'max_val', 'year'

    df['date'] = pd.to_datetime(df['date'])                          # 转为日期类型

    ######################################################################################
    # 选择year的功能由网页表单提供
    df = df[df['year'] == '2015']
    ######################################################################################

    # ColumnDataSource所有列必须长度相同 [IMP];
    # date_str用于在hover工具中正确显示日期(关注bokeh更新此功能)
    data = dict(date=df[df['city'] == 'Beijing']['date'],
                date_str=df[df['city'] == 'Beijing']['date'].apply(lambda x: x.strftime('%Y-%m-%d')),

                bj_min_val=df[df['city'] == 'Beijing']['min_val'],
                bj_mean_val=df[df['city'] == 'Beijing']['mean_val'],
                bj_max_val=df[df['city'] == 'Beijing']['max_val'],
                cd_min_val=df[df['city'] == 'Chengdu']['min_val'],
                cd_mean_val=df[df['city'] == 'Chengdu']['mean_val'],
                cd_max_val=df[df['city'] == 'Chengdu']['max_val'],
                gz_min_val=df[df['city'] == 'Guangzhou']['min_val'],
                gz_mean_val=df[df['city'] == 'Guangzhou']['mean_val'],
                gz_max_val=df[df['city'] == 'Guangzhou']['max_val'],
                sh_min_val=df[df['city'] == 'Shanghai']['min_val'],
                sh_mean_val=df[df['city'] == 'Shanghai']['mean_val'],
                sh_max_val=df[df['city'] == 'Shanghai']['max_val'],
                sy_min_val=df[df['city'] == 'Shenyang']['min_val'],
                sy_mean_val=df[df['city'] == 'Shenyang']['mean_val'],
                sy_max_val=df[df['city'] == 'Shenyang']['max_val'],

                cur_min_val=df[df['city'] == 'Beijing']['min_val'],
                cur_mean_val=df[df['city'] == 'Beijing']['mean_val'],
                cur_max_val=df[df['city'] == 'Beijing']['max_val'],
                plt_min_val=df[df['city'] == 'Beijing']['min_val'],
                plt_mean_val=df[df['city'] == 'Beijing']['mean_val'],
                plt_max_val=df[df['city'] == 'Beijing']['max_val'])
    source = ColumnDataSource(data=data)

    # 绘制线图,生成bokeh document
    doc = make_line_plot(source, mode='local')

    output_file('example_line_chart.html')
    save(doc)

