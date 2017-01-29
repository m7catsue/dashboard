# -*- coding: utf-8 -*-
import math
from bokeh.layouts import column, row, layout, gridplot, WidgetBox
from bokeh.models import FactorRange,  FixedTicker, CustomJS, LabelSet
from bokeh.models.widgets import RadioButtonGroup, Toggle
from bokeh.plotting import Figure
from bokeh.io import curdoc


def get_aqi_level(value):
    """
    返回相应的空气质量等级;排除部分日期有缺失值PM2.5浓度为1的情况
    """
    if 1 <= value <= 12:
        return '好'
    elif 13 <= value <= 35:
        return '中等'
    elif 36 <= value <= 55:
        return '对敏感人群不健康'
    elif 56 <= value <= 150:
        return '不健康'
    elif 151 <= value <= 250:
        return '非常不健康'
    else:
        return '有毒害'


def make_bar_matrix(data_source, mode='web'):
    """
    按月份作(2*3)散点图(linked panning & brushing)和(2*3)线图;
    图形排列(2*3):北京,成都,广州,上海,沈阳,所有城市;
    widgets可选选择:空气质量等级(好,中等,对敏感人群不健康,不健康,非常不健康,有毒害)/是否显示线图;

    在Figure中设置tools=[]以取消图像中默认的'pan'的功能,保证图像不受意外的拖动干扰 [IMP];
    初始显示每月AQI达到“中等”的天数;title由CustomJS回调函数动态更新
    """
    if mode not in ['web', 'local']:
        raise ValueError("Error: 'mode' parameter must be 'web' or 'local'!")

    month_labels = ['1月', '2月', '3月', '4月', '5月', '6月',
                    '7月', '8月', '9月', '10月', '11月', '12月']

    fig1 = Figure(plot_width=360, plot_height=240, title='AQI等级到达"中等"的天数:北京', toolbar_location=None, logo=None,
                  x_range=FactorRange(factors=month_labels), y_range=(0, 30), tools=[])
    fig1.vbar(x='months', top='fig_1_data', source=data_source, width=0.5)

    fig2 = Figure(plot_width=360, plot_height=240, title='AQI等级到达"中等"的天数:成都', toolbar_location=None, logo=None,
                  x_range=FactorRange(factors=month_labels), y_range=(0, 30), tools=[])
    fig2.vbar(x='months', top='fig_2_data', source=data_source, width=0.5)

    fig3 = Figure(plot_width=360, plot_height=240, title='AQI等级到达"中等"的天数:广州', toolbar_location=None, logo=None,
                  x_range=FactorRange(factors=month_labels), y_range=(0, 30), tools=[])
    fig3.vbar(x='months', top='fig_3_data', source=data_source, width=0.5)

    fig4 = Figure(plot_width=360, plot_height=240, title='AQI等级到达"中等"的天数:上海', toolbar_location=None, logo=None,
                  x_range=FactorRange(factors=month_labels), y_range=(0, 30), tools=[])
    fig4.vbar(x='months', top='fig_4_data', source=data_source, width=0.5)

    fig5 = Figure(plot_width=360, plot_height=240, title='AQI等级到达"中等"的天数:沈阳', toolbar_location=None, logo=None,
                  x_range=FactorRange(factors=month_labels), y_range=(0, 30), tools=[])
    fig5.vbar(x='months', top='fig_5_data', source=data_source, width=0.5)

    fig6 = Figure(plot_width=360, plot_height=240, title='AQI等级到达"中等"的天数:所有城市', toolbar_location=None, logo=None,
                  x_range=FactorRange(factors=month_labels), y_range=(0, 100), tools=[])  # 所有城市加总
    fig6.vbar(x='months', top='fig_6_data', source=data_source, width=0.5, color='#41ae76')

    # [IMP] 调整每个图形的属性:
    figs = [fig1, fig2, fig3, fig4, fig5, fig6]
    for fig in figs:
        if figs.index(fig) != 5:                                                # 设定y轴刻度值(单个城市)
            fig.yaxis[0].ticker = FixedTicker(ticks=list(range(0, 31, 5)))
        else:                                                                   # 设定y轴刻度值(所有城市加总)
            fig.yaxis[0].ticker = FixedTicker(ticks=list(range(0, 101, 20)))
        fig.xaxis.major_label_orientation = math.pi/8                           # 旋转x轴上的刻度标签 (π=180°)

    # [IMP] 为每个图形添加标签
    dict_figs = dict(fig1=['fig_1_data', 'fig_1_lab', fig1], fig2=['fig_2_data', 'fig_2_lab', fig2],
                     fig3=['fig_3_data', 'fig_3_lab', fig3], fig4=['fig_4_data', 'fig_4_lab', fig4],
                     fig5=['fig_5_data', 'fig_5_lab', fig5], fig6=['fig_6_data', 'fig_6_lab', fig6])
    for key in dict_figs:
        label_set = LabelSet(x='months', y=dict_figs[key][0], text=dict_figs[key][1],
                             y_offset=3, text_font_size='5pt', angle=math.pi/15,
                             source=data_source)
        dict_figs[key][2].add_layout(label_set)

    # 设置widgets和共用的回调函数(generic_callback)
    select_level = RadioButtonGroup(labels=['好', '中等', '对敏感人群不健康', '不健康', '非常不健康', '有毒害'], active=1,
                                    height=50, width=450)
    toggle_label = Toggle(label='显示数值/隐藏数值', button_type='default', active=False,
                          height=50, width=200)

    generic_callback = CustomJS(args=dict(source=data_source,
                                          select_level_obj=select_level,
                                          toggle_label_obj=toggle_label,
                                          fig1=fig1, fig2=fig2, fig3=fig3,
                                          fig4=fig4, fig5=fig5, fig6=fig6),
                                code="""
                                    var data = source.data;
                                    var level = String(select_level_obj.active);
                                    var show_label = toggle_label_obj.active;

                                    var arr_empty = ['', '', '', '', '', '', '', '', '', '', '', ''];
                                    var mapping = {
                                        0: ['bj_level_1', 'cd_level_1', 'gz_level_1', 'sh_level_1', 'sy_level_1', 'all_level_1', '好'],
                                        1: ['bj_level_2', 'cd_level_2', 'gz_level_2', 'sh_level_2', 'sy_level_2', 'all_level_2', '中等'],
                                        2: ['bj_level_3', 'cd_level_3', 'gz_level_3', 'sh_level_3', 'sy_level_3', 'all_level_3', '对敏感人群不健康'],
                                        3: ['bj_level_4', 'cd_level_4', 'gz_level_4', 'sh_level_4', 'sy_level_4', 'all_level_4', '不健康'],
                                        4: ['bj_level_5', 'cd_level_5', 'gz_level_5', 'sh_level_5', 'sy_level_5', 'all_level_5', '非常不健康'],
                                        5: ['bj_level_6', 'cd_level_6', 'gz_level_6', 'sh_level_6', 'sy_level_6', 'all_level_6', '有毒害']
                                    }
                                    // 更新柱形图的数据;
                                    for (let i=0; i<data['bj_level_1'].length; i++) {
                                        data['fig_1_data'][i] = data[mapping[level][0]][i];
                                        data['fig_2_data'][i] = data[mapping[level][1]][i];
                                        data['fig_3_data'][i] = data[mapping[level][2]][i];
                                        data['fig_4_data'][i] = data[mapping[level][3]][i];
                                        data['fig_5_data'][i] = data[mapping[level][4]][i];
                                        data['fig_6_data'][i] = data[mapping[level][5]][i];
                                    }
                                    // 更新显示label的数据;toggle_label为false,将所有label列赋值为空;
                                    if (show_label) {
                                        data['fig_1_lab'] = data['fig_1_data'].slice();
                                        data['fig_2_lab'] = data['fig_2_data'].slice();
                                        data['fig_3_lab'] = data['fig_3_data'].slice();
                                        data['fig_4_lab'] = data['fig_4_data'].slice();
                                        data['fig_5_lab'] = data['fig_5_data'].slice();
                                        data['fig_6_lab'] = data['fig_6_data'].slice();
                                    }
                                    else {
                                        data['fig_1_lab'] = arr_empty.slice();
                                        data['fig_2_lab'] = arr_empty.slice();
                                        data['fig_3_lab'] = arr_empty.slice();
                                        data['fig_4_lab'] = arr_empty.slice();
                                        data['fig_5_lab'] = arr_empty.slice();
                                        data['fig_6_lab'] = arr_empty.slice();
                                    }
                                    // 更新title [IMP]
                                    fig1.title.text = 'AQI等级到达\"' + mapping[level][6] + '\"的天数:北京';
                                    fig2.title.text = 'AQI等级到达\"' + mapping[level][6] + '\"的天数:成都';
                                    fig3.title.text = 'AQI等级到达\"' + mapping[level][6] + '\"的天数:广州';
                                    fig4.title.text = 'AQI等级到达\"' + mapping[level][6] + '\"的天数:上海';
                                    fig5.title.text = 'AQI等级到达\"' + mapping[level][6] + '\"的天数:沈阳';
                                    fig6.title.text = 'AQI等级到达\"' + mapping[level][6] + '\"的天数:所有城市';

                                    source.trigger('change');
                                    fig1.trigger('change'); fig2.trigger('change'); fig3.trigger('change');
                                    fig4.trigger('change'); fig5.trigger('change'); fig6.trigger('change');
                                """)

    select_level.js_on_change('active', generic_callback)
    toggle_label.js_on_change('active', generic_callback)

    if mode == 'web':
        fig_layout = layout([select_level, toggle_label],
                            [fig1, fig2, fig3],
                            [fig4, fig5, fig6])
        return fig_layout
    if mode == 'local':
        document = curdoc()
        document.add_root(layout([select_level, toggle_label],
                                 [fig1, fig2, fig3],
                                 [fig4, fig5, fig6]))
        return document


if __name__ == '__main__':
    import os
    import sqlite3
    import pandas as pd
    from bokeh.models import ColumnDataSource
    from bokeh.io import output_file, save

    basedir = os.path.abspath(os.path.dirname(__file__))  # 本文件所在文件夹的绝对路径
    db_dir = os.path.dirname(basedir)  # sqlite所在的路径(base_dir的上一级路径)

    with sqlite3.connect(os.path.join(db_dir, 'db_tmp.db')) as conn:
        df = pd.read_sql("SELECT * FROM aqi_data",
                         con=conn)  # dataframe columns: 'city', 'date', 'mean_val', 'min_val', 'max_val', 'year'

    df['date'] = pd.to_datetime(df['date'])  # 转为日期类型

    ######################################################################################
    # 选择year的功能由网页表单提供
    df = df[df['year'] == '2015']
    ######################################################################################

    df['level'] = df['mean_val'].apply(get_aqi_level)
    df['month'] = df['date'].apply(lambda t: t.month)
    df = pd.DataFrame(df.groupby(['city', 'month', 'level'])['date'].count()).\
        reset_index(level=['city', 'month', 'level'])
    df.rename(columns={'date': 'num_days'}, inplace=True)

    months = list(range(1, 13))
    levels = ['好', '中等', '对敏感人群不健康', '不健康', '非常不健康', '有毒害']

    bj_level_1 = df[(df['city'] == 'Beijing') & (df['level'] == '好')][['month', 'num_days']]\
        .set_index('month')['num_days']
    bj_level_2 = df[(df['city'] == 'Beijing') & (df['level'] == '中等')][['month', 'num_days']]\
        .set_index('month')['num_days']
    bj_level_3 = df[(df['city'] == 'Beijing') & (df['level'] == '对敏感人群不健康')][['month', 'num_days']]\
        .set_index('month')['num_days']
    bj_level_4 = df[(df['city'] == 'Beijing') & (df['level'] == '不健康')][['month', 'num_days']]\
        .set_index('month')['num_days']
    bj_level_5 = df[(df['city'] == 'Beijing') & (df['level'] == '非常不健康')][['month', 'num_days']]\
        .set_index('month')['num_days']
    bj_level_6 = df[(df['city'] == 'Beijing') & (df['level'] == '有毒害')][['month', 'num_days']]\
        .set_index('month')['num_days']
    cd_level_1 = df[(df['city'] == 'Chengdu') & (df['level'] == '好')][['month', 'num_days']] \
        .set_index('month')['num_days']
    cd_level_2 = df[(df['city'] == 'Chengdu') & (df['level'] == '中等')][['month', 'num_days']] \
        .set_index('month')['num_days']
    cd_level_3 = df[(df['city'] == 'Chengdu') & (df['level'] == '对敏感人群不健康')][['month', 'num_days']] \
        .set_index('month')['num_days']
    cd_level_4 = df[(df['city'] == 'Chengdu') & (df['level'] == '不健康')][['month', 'num_days']] \
        .set_index('month')['num_days']
    cd_level_5 = df[(df['city'] == 'Chengdu') & (df['level'] == '非常不健康')][['month', 'num_days']] \
        .set_index('month')['num_days']
    cd_level_6 = df[(df['city'] == 'Chengdu') & (df['level'] == '有毒害')][['month', 'num_days']] \
        .set_index('month')['num_days']
    gz_level_1 = df[(df['city'] == 'Guangzhou') & (df['level'] == '好')][['month', 'num_days']] \
        .set_index('month')['num_days']
    gz_level_2 = df[(df['city'] == 'Guangzhou') & (df['level'] == '中等')][['month', 'num_days']] \
        .set_index('month')['num_days']
    gz_level_3 = df[(df['city'] == 'Guangzhou') & (df['level'] == '对敏感人群不健康')][['month', 'num_days']] \
        .set_index('month')['num_days']
    gz_level_4 = df[(df['city'] == 'Guangzhou') & (df['level'] == '不健康')][['month', 'num_days']] \
        .set_index('month')['num_days']
    gz_level_5 = df[(df['city'] == 'Guangzhou') & (df['level'] == '非常不健康')][['month', 'num_days']] \
        .set_index('month')['num_days']
    gz_level_6 = df[(df['city'] == 'Guangzhou') & (df['level'] == '有毒害')][['month', 'num_days']] \
        .set_index('month')['num_days']
    sh_level_1 = df[(df['city'] == 'Shanghai') & (df['level'] == '好')][['month', 'num_days']] \
        .set_index('month')['num_days']
    sh_level_2 = df[(df['city'] == 'Shanghai') & (df['level'] == '中等')][['month', 'num_days']] \
        .set_index('month')['num_days']
    sh_level_3 = df[(df['city'] == 'Shanghai') & (df['level'] == '对敏感人群不健康')][['month', 'num_days']] \
        .set_index('month')['num_days']
    sh_level_4 = df[(df['city'] == 'Shanghai') & (df['level'] == '不健康')][['month', 'num_days']] \
        .set_index('month')['num_days']
    sh_level_5 = df[(df['city'] == 'Shanghai') & (df['level'] == '非常不健康')][['month', 'num_days']] \
        .set_index('month')['num_days']
    sh_level_6 = df[(df['city'] == 'Shanghai') & (df['level'] == '有毒害')][['month', 'num_days']] \
        .set_index('month')['num_days']
    sy_level_1 = df[(df['city'] == 'Shenyang') & (df['level'] == '好')][['month', 'num_days']] \
        .set_index('month')['num_days']
    sy_level_2 = df[(df['city'] == 'Shenyang') & (df['level'] == '中等')][['month', 'num_days']] \
        .set_index('month')['num_days']
    sy_level_3 = df[(df['city'] == 'Shenyang') & (df['level'] == '对敏感人群不健康')][['month', 'num_days']] \
        .set_index('month')['num_days']
    sy_level_4 = df[(df['city'] == 'Shenyang') & (df['level'] == '不健康')][['month', 'num_days']] \
        .set_index('month')['num_days']
    sy_level_5 = df[(df['city'] == 'Shenyang') & (df['level'] == '非常不健康')][['month', 'num_days']] \
        .set_index('month')['num_days']
    sy_level_6 = df[(df['city'] == 'Shenyang') & (df['level'] == '有毒害')][['month', 'num_days']] \
        .set_index('month')['num_days']

    bj_level_1 = dict(bj_level_1); bj_level_2 = dict(bj_level_2); bj_level_3 = dict(bj_level_3)
    bj_level_4 = dict(bj_level_4); bj_level_5 = dict(bj_level_5); bj_level_6 = dict(bj_level_6)
    cd_level_1 = dict(cd_level_1); cd_level_2 = dict(cd_level_2); cd_level_3 = dict(cd_level_3)
    cd_level_4 = dict(cd_level_4); cd_level_5 = dict(cd_level_5); cd_level_6 = dict(cd_level_6)
    gz_level_1 = dict(gz_level_1); gz_level_2 = dict(gz_level_2); gz_level_3 = dict(gz_level_3)
    gz_level_4 = dict(gz_level_4); gz_level_5 = dict(gz_level_5); gz_level_6 = dict(gz_level_6)
    sh_level_1 = dict(sh_level_1); sh_level_2 = dict(sh_level_2); sh_level_3 = dict(sh_level_3)
    sh_level_4 = dict(sh_level_4); sh_level_5 = dict(sh_level_5); sh_level_6 = dict(sh_level_6)
    sy_level_1 = dict(sy_level_1); sy_level_2 = dict(sy_level_2); sy_level_3 = dict(sy_level_3)
    sy_level_4 = dict(sy_level_4); sy_level_5 = dict(sy_level_5); sy_level_6 = dict(sy_level_6)

    dicts = [bj_level_1, bj_level_2, bj_level_3, bj_level_4, bj_level_5, bj_level_6,
             cd_level_1, cd_level_2, cd_level_3, cd_level_4, cd_level_5, cd_level_6,
             gz_level_1, gz_level_2, gz_level_3, gz_level_4, gz_level_5, gz_level_6,
             sh_level_1, sh_level_2, sh_level_3, sh_level_4, sh_level_5, sh_level_6,
             sy_level_1, sy_level_2, sy_level_3, sy_level_4, sy_level_5, sy_level_6]

    for month in months:  # GroupBy结果可能出现某一类型缺失的情况:如xxxx年x月北京没有空气质量等级为'好'的情况
        for dict_data in dicts:
            if month not in dict_data:
                dict_data[month] = 0

    bj_level_1 = pd.Series(data=bj_level_1, index=months).values; bj_level_2 = pd.Series(data=bj_level_2, index=months).values
    bj_level_3 = pd.Series(data=bj_level_3, index=months).values; bj_level_4 = pd.Series(data=bj_level_4, index=months).values
    bj_level_5 = pd.Series(data=bj_level_5, index=months).values; bj_level_6 = pd.Series(data=bj_level_6, index=months).values
    cd_level_1 = pd.Series(data=cd_level_1, index=months).values; cd_level_2 = pd.Series(data=cd_level_2, index=months).values
    cd_level_3 = pd.Series(data=cd_level_3, index=months).values; cd_level_4 = pd.Series(data=cd_level_4, index=months).values
    cd_level_5 = pd.Series(data=cd_level_5, index=months).values; cd_level_6 = pd.Series(data=cd_level_6, index=months).values
    gz_level_1 = pd.Series(data=gz_level_1, index=months).values; gz_level_2 = pd.Series(data=gz_level_2, index=months).values
    gz_level_3 = pd.Series(data=gz_level_3, index=months).values; gz_level_4 = pd.Series(data=gz_level_4, index=months).values
    gz_level_5 = pd.Series(data=gz_level_5, index=months).values; gz_level_6 = pd.Series(data=gz_level_6, index=months).values
    sh_level_1 = pd.Series(data=sh_level_1, index=months).values; sh_level_2 = pd.Series(data=sh_level_2, index=months).values
    sh_level_3 = pd.Series(data=sh_level_3, index=months).values; sh_level_4 = pd.Series(data=sh_level_4, index=months).values
    sh_level_5 = pd.Series(data=sh_level_5, index=months).values; sh_level_6 = pd.Series(data=sh_level_6, index=months).values
    sy_level_1 = pd.Series(data=sy_level_1, index=months).values; sy_level_2 = pd.Series(data=sy_level_2, index=months).values
    sy_level_3 = pd.Series(data=sy_level_3, index=months).values; sy_level_4 = pd.Series(data=sy_level_4, index=months).values
    sy_level_5 = pd.Series(data=sy_level_5, index=months).values; sy_level_6 = pd.Series(data=sy_level_6, index=months).values

    all_level_1 = bj_level_1 + cd_level_1 + gz_level_1 + sh_level_1 + sy_level_1
    all_level_2 = bj_level_2 + cd_level_2 + gz_level_2 + sh_level_2 + sy_level_2
    all_level_3 = bj_level_3 + cd_level_3 + gz_level_3 + sh_level_3 + sy_level_3
    all_level_4 = bj_level_4 + cd_level_4 + gz_level_4 + sh_level_4 + sy_level_4
    all_level_5 = bj_level_5 + cd_level_5 + gz_level_5 + sh_level_5 + sy_level_5
    all_level_6 = bj_level_1 + cd_level_6 + gz_level_6 + sh_level_6 + sy_level_6

    data = dict(months=months,
                bj_level_1=bj_level_1, bj_level_2=bj_level_2, bj_level_3=bj_level_3,
                bj_level_4=bj_level_4, bj_level_5=bj_level_5, bj_level_6=bj_level_6,
                cd_level_1=cd_level_1, cd_level_2=cd_level_2, cd_level_3=cd_level_3,
                cd_level_4=cd_level_4, cd_level_5=cd_level_5, cd_level_6=cd_level_6,
                gz_level_1=gz_level_1, gz_level_2=gz_level_2, gz_level_3=gz_level_3,
                gz_level_4=gz_level_4, gz_level_5=gz_level_5, gz_level_6=gz_level_6,
                sh_level_1=sh_level_1, sh_level_2=sh_level_2, sh_level_3=sh_level_3,
                sh_level_4=sh_level_4, sh_level_5=sh_level_5, sh_level_6=sh_level_6,
                sy_level_1=sy_level_1, sy_level_2=sy_level_2, sy_level_3=sy_level_3,
                sy_level_4=sy_level_4, sy_level_5=sy_level_5, sy_level_6=sy_level_6,
                all_level_1=all_level_1, all_level_2=all_level_2, all_level_3=all_level_3,
                all_level_4=all_level_4, all_level_5=all_level_5, all_level_6=all_level_6,

                fig_1_data=bj_level_2, fig_2_data=cd_level_2, fig_3_data=gz_level_2,   # 作图用数据
                fig_4_data=sh_level_2, fig_5_data=sy_level_2, fig_6_data=all_level_2,
                fig_1_lab=['', '', '', '', '', '', '', '', '', '', '', ''],            # 显示标签的数据(默认不显示label,由JS更新)
                fig_2_lab=['', '', '', '', '', '', '', '', '', '', '', ''],
                fig_3_lab=['', '', '', '', '', '', '', '', '', '', '', ''],
                fig_4_lab=['', '', '', '', '', '', '', '', '', '', '', ''],
                fig_5_lab=['', '', '', '', '', '', '', '', '', '', '', ''],
                fig_6_lab=['', '', '', '', '', '', '', '', '', '', '', ''])

    source = ColumnDataSource(data=data)

    # 绘制线图,生成bokeh document
    doc = make_bar_matrix(source, mode='local')

    output_file('example_bar_matrix.html')
    save(doc)
