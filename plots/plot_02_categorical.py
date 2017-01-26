# -*- coding: utf-8 -*-
import math
from seaborn import color_palette
from bokeh.layouts import column, row, layout, gridplot, WidgetBox
from bokeh.models import ColumnDataSource, FactorRange, LabelSet, CustomJS, HoverTool, TapTool, \
    FixedTicker, VBar, AnnularWedge  # VBar/HBar和AnnularWedge用于TapTool的renderer的设定
from bokeh.models.widgets import RadioButtonGroup, DataTable, TableColumn, StringFormatter, NumberFormatter
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


def make_categorical(categorical_source, stacked_bar_source, mode='web', show_label=False):
    """
    作带有widgets的柱形图/饼图/数据表;
    [IMP] (1)通过在figure中设置x_range=['a', 'b'...]将x轴类型设为Categorical;
          (2)通过DataSource中传入color列来为柱形图设置颜色;
          (3)通过seaborn获得渐变颜色的hex值;
    """
    if mode not in ['web', 'local']:
        raise ValueError("Error: 'mode' parameter must be 'web' or 'local'!")

    ##################################################################################
    # 作柱状图
    hover_bar = HoverTool(tooltips=[('空气质量等级', '@labels'),  # 每个plot需使用单独的hover_tool,不能共用
                                    ('该等级天数', '@counts_plt{int}'),
                                    ('全年天数占比', '@percents_plt_rounded')],
                          point_policy='follow_mouse')

    fig1 = Figure(plot_width=360, plot_height=360, toolbar_location=None, logo=None, tools=[hover_bar, TapTool()],
                  x_range=['好', '中等', '对敏感人群不健康', '不健康', '非常不健康', '有毒害'])  # 将x轴类型设为Categorical [IMP]

    renderer = fig1.vbar(x='x_loc', top='counts_plt',                 # x_loc是作柱状图时的x轴坐标
                         color='colors',                              # legends和colors通过DataSource传入
                         #legend='labels',
                         source=categorical_source,
                         width=0.5, bottom=0)                         # 柱状图中每个图形的'宽度'和'y轴起始点'

    # [IMP]自定义当TapTool选定(即鼠标单击)某个图形时,selected和nonselected的图形的颜色/边框等特征
    renderer.selection_glyph = VBar(fill_alpha=0.4, fill_color="navy",
                                    line_color="black", line_alpha=0.3, line_width=2)
    renderer.nonselection_glyph = VBar(fill_alpha=0.3, fill_color=None,
                                       line_color="navy", line_alpha=0.3, line_width=2)

    fig1.title.text = '空气质量指数(AQI)等级分布'
    fig1.xaxis.major_label_orientation = math.pi/8        # 旋转x轴上的刻度标签 (π=180°)

    # [IMP] 对柱状图添加类别标签(可选)
    # text_font_style: normal/italic/bold; text_align: left/center/right
    if show_label:
        label_set = LabelSet(x='x_loc', y='counts_plt', text='labels', y_offset=-6,
                             text_font_style='bold', text_font_size='5pt', text_color='#555555',
                             source=categorical_source, text_align='center')
        fig1.add_layout(label_set)

    ##################################################################################
    # 作饼图 (弧度制:π=180°; x=0, y=0设置饼图圆心的坐标位置)
    # wedge是实心饼图; annular_wedge是空心饼图
    # 对annular_wedge: inner_radius/outer_radius也可从DataSource传入;可对不同类型特殊设置,达到在空心饼图中的某类的'突出效果'

    hover_pie = HoverTool(tooltips=[('空气质量等级', '@labels'),  # 每个plot需使用单独的hover_tool,不能共用
                                    ('该等级天数', '@counts_plt{int}'),
                                    ('全年天数占比', '@percents_plt_rounded')],
                          point_policy='follow_mouse')

    fig2 = Figure(plot_width=360, plot_height=360, x_range=(-1, 1), y_range=(-1, 1),
                  toolbar_location=None, logo=None, tools=[hover_pie, TapTool()])

    renderer = fig2.annular_wedge(x=0, y=0, inner_radius=0.35, outer_radius=0.75,
                                  direction='anticlock', source=categorical_source,
                                  start_angle='start_angles_plt', end_angle='end_angles_plt', color='colors',
                                  legend='labels')

    # [IMP]自定义当TapTool选定(即鼠标单击)某个图形时,selected和nonselected的图形的颜色/边框等特征
    renderer.selection_glyph = AnnularWedge(fill_alpha=0.4, fill_color="navy",
                                            line_color="black", line_alpha=0.3, line_width=2)
    renderer.nonselection_glyph = AnnularWedge(fill_alpha=0.3, fill_color=None,
                                               line_color="navy", line_alpha=0.3, line_width=2)

    fig2.title.text = '空气质量指数(AQI)等级占比'

    # 更改figure内legend的属性(注意:bokeh未来可能会提供更方便的API)
    fig2.legend.location = 'top_right'                            # default: 'top_right'
    fig2.legend.margin = 3                                        # legend距离figure边缘的距离(default: 10)
    fig2.legend.padding = 3                                       # legend内的pading(default: 10)
    fig2.legend.spacing = 1                                       # legend内的行间隔(default: 3)
    fig2.legend.glyph_height, fig2.legend.glyph_width = 8, 8      # legend内的图例图像的高度/宽度(default: 20)
    fig2.legend.label_height, fig2.legend.label_width = 8, 8      # legend内的文字标签的高度/宽度(default: 20)
    fig2.legend.label_text_font_size = '4pt'                      # 文字大小(default 10)

    ##################################################################################
    # 对所有城市(bj,cd,gz,sh,sy)作堆积柱状图(单独的DataSource)
    # [IMP] 堆积柱状图的难点在于构建符合形式要求的DataSource(使用stacked_bar_source)
    hover_stacked = HoverTool(tooltips=[('城市', '@cities'),
                                        ('描述', '@desc')],
                              point_policy='follow_mouse')

    cities = ['北京', '成都', '广州', '上海', '沈阳']
    colors = color_palette('RdBu_r', 6).as_hex()
    fig3 = Figure(plot_width=360, plot_height=360, toolbar_location=None, logo=None, tools=[hover_stacked],
                  y_range=FactorRange(factors=cities), x_range=(0, 380))

    fig3.title.text = '空气质量指数(AQI)等级分布对比 (所有城市)'

    # [IMP] cities中的城市顺序须对应stack_offset中城市的顺序
    fig3.hbar(y='cities', height=0.5, left='stack_offset_0', right='stack_offset_1', color=colors[0], source=stacked_bar_source)
    fig3.hbar(y='cities', height=0.5, left='stack_offset_1', right='stack_offset_2', color=colors[1], source=stacked_bar_source)
    fig3.hbar(y='cities', height=0.5, left='stack_offset_2', right='stack_offset_3', color=colors[2], source=stacked_bar_source)
    fig3.hbar(y='cities', height=0.5, left='stack_offset_3', right='stack_offset_4', color=colors[3], source=stacked_bar_source)
    fig3.hbar(y='cities', height=0.5, left='stack_offset_4', right='stack_offset_5', color=colors[4], source=stacked_bar_source)
    fig3.hbar(y='cities', height=0.5, left='stack_offset_5', right='stack_offset_6', color=colors[5], source=stacked_bar_source)

    # [IMP] specify exact tick locations
    fig3.xaxis[0].ticker = FixedTicker(ticks=[0, 60, 120, 180, 240, 300, 360])

    ##################################################################################
    # 显示DataTable(数据表格): TableColumn中的field为DataSource中的列名
    # DataTable是widget而不是figure,需要对DataTable设置callback函数

    columns = [TableColumn(field="labels", title='空气质量等级', width=70,
                           formatter=StringFormatter(font_style='bold')),
               TableColumn(field="counts_plt", title='达到天数', width=50,
                           formatter=NumberFormatter()),
               TableColumn(field='percents_plt_rounded', title='百分比', width=50),
               TableColumn(field='info', title='对健康的影响')]

    data_table = DataTable(width=900, height=180, source=categorical_source, columns=columns,
                           fit_columns=True, selectable=True,
                           sortable=True, editable=False)

    ##################################################################################
    # 设置widget和CustomJS回调函数
    # (1)柱形图,(2)饼图,(3)数据表格共用同一个DataSource:对DataSource的更改将会更新所有图形(DataSource中的所有图形用到的列都要改变)
    # 堆积柱形图使用单独的DataSource,不受JS回调函数影响

    select_city = RadioButtonGroup(labels=['北京', '成都', '广州', '上海', '沈阳'], active=0)

    # 对于DataTable使用CustoomJS回调函数,需明确传入DataTable对象;若仅对souce改变,DataTable不会变化 [IMP]
    # RadioButtonGroup的active是int类型
    callback = CustomJS(args=dict(source=categorical_source, table=data_table), code="""
        var data = source.data;
        var city = String(cb_obj.active);
        var mapping = {
            0: ['counts_bj', 'start_angles_bj', 'end_angles_bj', 'percents_bj_rounded'],
            1: ['counts_cd', 'start_angles_cd', 'end_angles_cd', 'percents_cd_rounded'],
            2: ['counts_gz', 'start_angles_gz', 'end_angles_gz', 'percents_gz_rounded'],
            3: ['counts_sh', 'start_angles_sh', 'end_angles_sh', 'percents_sh_rounded'],
            4: ['counts_sy', 'start_angles_sy', 'end_angles_sy', 'percents_sy_rounded'],
        }
        for (let i=0; i<data['counts_bj'].length; i++) {
            data['counts_plt'][i] = data[mapping[city][0]][i];            // 更新柱形图数据
            data['start_angles_plt'][i] = data[mapping[city][1]][i];      // 更新饼图数据
            data['end_angles_plt'][i] = data[mapping[city][2]][i];
            data['percents_plt_rounded'][i] = data[mapping[city][3]][i];  // 更新tooltips中的数据
        }
        source.trigger('change');
        table.trigger('change');
    """)

    select_city.js_on_change('active', callback)

    if mode == 'web':
        fig_layout = column(select_city, row(fig1, fig2, fig3), data_table)
        return fig_layout
    if mode == 'local':
        document = curdoc()
        document.add_root(column(select_city, row(fig1, fig2, fig3), data_table))
        return document


if __name__ == '__main__':
    import os
    import sqlite3
    import pandas as pd
    import seaborn as sns
    from bokeh.io import output_file, save

    basedir = os.path.abspath(os.path.dirname(__file__))             # 本文件所在文件夹的绝对路径
    db_dir = os.path.dirname(basedir)                                # sqlite所在的路径(base_dir的上一级路径)

    with sqlite3.connect(os.path.join(db_dir, 'db_tmp.db')) as conn:
        df = pd.read_sql("SELECT * FROM aqi_data", con=conn)         # dataframe columns: 'city', 'date', 'mean_val', 'min_val', 'max_val', 'year'

    ######################################################################################
    # 选择year的功能由网页表单提供
    df = df[df['year'] == '2015']
    ######################################################################################

    df['level'] = df['mean_val'].apply(get_aqi_level)
    df = pd.DataFrame(df.groupby(['city', 'level'])['date'].count()).reset_index(level=['city', 'level'])
    df.rename(columns={'date': 'num_days'}, inplace=True)

    # [IMP] GroupBy结果可能出现某一类型缺失的情况:如2015年成都没有空气质量等级为'好'的情况
    levels = ['好', '中等', '对敏感人群不健康', '不健康', '非常不健康', '有毒害']
    info = ['空气质量令人满意，基本无空气污染',
            '空气质量可接受，但某些污染物可能对极少数异常敏感的人群健康有较弱影响',
            '易感人群症状有轻度增加，健康人群出现刺激症状',
            '进一步加剧易感人群症状，可能对健康人群心脏、呼吸系统有影响',
            '心脏病和肺病患者症状显著加剧，运动耐受力降低，健康人群普遍出现症状',
            '健康人群运动耐受力降低，有明显强烈症状，提前出现某些疾病']

    bj = dict(df[df['city'] == 'Beijing'][['level', 'num_days']].set_index('level')['num_days'])   # dict(Series)由series得到dict:key是series.index
    cd = dict(df[df['city'] == 'Chengdu'][['level', 'num_days']].set_index('level')['num_days'])
    gz = dict(df[df['city'] == 'Guangzhou'][['level', 'num_days']].set_index('level')['num_days'])
    sh = dict(df[df['city'] == 'Shanghai'][['level', 'num_days']].set_index('level')['num_days'])
    sy = dict(df[df['city'] == 'Shenyang'][['level', 'num_days']].set_index('level')['num_days'])
    dictionaries = [bj, cd, gz, sh, sy]
    for dictionary in dictionaries:
        for level in levels:
            if level not in dictionary:
                dictionary[level] = 0

    # 由dict作为data,levels作为index生成series;此时series.values的顺序一致,都由index的顺序决定
    # 各类型的数量和占比; [IMP] 做饼图所用的占比是"累计百分数"
    counts_bj = pd.Series(data=bj, index=levels).values + 0.000001  # [IMP] np.array+常数:对数组中每个元素+常数; 保证每个类别的占比不会为0%(至少是非常小的非零数)
    counts_cd = pd.Series(data=cd, index=levels).values + 0.000001  # [IMP] 若有某个类别占比为0%(如:从0°~0°,等于整个饼图的范围),则该类信息会在其他所有类的tooltips中显示
    counts_gz = pd.Series(data=gz, index=levels).values + 0.000001  # [IMP] 在tooltips显示时将counts_xx列中的float转为int: "@x{int}"
    counts_sh = pd.Series(data=sh, index=levels).values + 0.000001
    counts_sy = pd.Series(data=sy, index=levels).values + 0.000001

    counts_bj_cumsum = counts_bj.cumsum()                           # [IMP] array.cumsum()返回累计求和之后的新array
    counts_cd_cumsum = counts_cd.cumsum()
    counts_gz_cumsum = counts_gz.cumsum()
    counts_sh_cumsum = counts_sh.cumsum()
    counts_sy_cumsum = counts_sy.cumsum()
    percents_bj = [x / counts_bj.sum() for x in counts_bj_cumsum]
    percents_cd = [x / counts_cd.sum() for x in counts_cd_cumsum]
    percents_gz = [x / counts_gz.sum() for x in counts_gz_cumsum]
    percents_sh = [x / counts_sh.sum() for x in counts_sh_cumsum]
    percents_sy = [x / counts_sy.sum() for x in counts_sy_cumsum]

    percents_bj_rounded = ['%.2f%%' % (x/counts_bj.sum()*100) for x in counts_bj]  # 用于饼图tooltips的显示:将格式转换为保留2位小数的百分数
    percents_cd_rounded = ['%.2f%%' % (x/counts_cd.sum()*100) for x in counts_cd]  # '%%'用于escape百分符号('%')
    percents_gz_rounded = ['%.2f%%' % (x/counts_gz.sum()*100) for x in counts_gz]
    percents_sh_rounded = ['%.2f%%' % (x/counts_sh.sum()*100) for x in counts_sh]
    percents_sy_rounded = ['%.2f%%' % (x/counts_sy.sum()*100) for x in counts_sy]

    # start_angles/end_angles: 依据各类型的占比得到作饼图所需的各类的起始/终止的弧度(使用累计百分数计算)
    # (*)start_angles列表左端增加新元素0(累计百分比0%),end_angles列表即percents_xx(最后一个元素是累计百分比100%) [IMP]
    # 上述操作(*)步骤也保证了ColumnDataSource所有列长度相
    start_angles_bj = [2*math.pi*p for p in ([0] + percents_bj[:-1])]; end_angles_bj = [2*math.pi*p for p in percents_bj]
    start_angles_cd = [2*math.pi*p for p in ([0] + percents_cd[:-1])]; end_angles_cd = [2*math.pi*p for p in percents_cd]
    start_angles_gz = [2*math.pi*p for p in ([0] + percents_gz[:-1])]; end_angles_gz = [2*math.pi*p for p in percents_gz]
    start_angles_sh = [2*math.pi*p for p in ([0] + percents_sh[:-1])]; end_angles_sh = [2*math.pi*p for p in percents_sh]
    start_angles_sy = [2*math.pi*p for p in ([0] + percents_sy[:-1])]; end_angles_sy = [2*math.pi*p for p in percents_sy]

    # ColumnDataSource所有列必须长度相同 [IMP]
    data = dict(labels=levels, info=info,
                x_loc=[1, 2, 3, 4, 5, 6],                         # [IMP] x_loc是作柱状图时的x轴坐标;作柱状图x_loc和labels的顺序必须一一对应
                colors=sns.color_palette('RdBu_r', 6).as_hex(),   # [IMP] 通过seaborn获得渐变颜色的hex值;最后的'_r'表示reverse

                counts_bj=counts_bj, start_angles_bj=start_angles_bj, end_angles_bj=end_angles_bj,
                counts_cd=counts_cd, start_angles_cd=start_angles_cd, end_angles_cd=end_angles_cd,
                counts_gz=counts_gz, start_angles_gz=start_angles_gz, end_angles_gz=end_angles_gz,
                counts_sh=counts_sh, start_angles_sh=start_angles_sh, end_angles_sh=end_angles_sh,
                counts_sy=counts_sy, start_angles_sy=start_angles_sy, end_angles_sy=end_angles_sy,
                percents_bj_rounded=percents_bj_rounded,
                percents_cd_rounded=percents_cd_rounded,
                percents_gz_rounded=percents_gz_rounded,
                percents_sh_rounded=percents_sh_rounded,
                percents_sy_rounded=percents_sy_rounded,

                counts_plt=counts_bj,
                start_angles_plt=start_angles_bj, end_angles_plt=end_angles_bj,
                percents_plt_rounded=percents_bj_rounded)

    source = ColumnDataSource(data=data)

    ########################################################################################
    # 生成堆积柱形图(stacked bar)所需的数据

    arrays = [counts_bj_cumsum, counts_cd_cumsum, counts_gz_cumsum,
              counts_sh_cumsum, counts_sy_cumsum]

    stack_offset_0 = [0, 0, 0, 0, 0]
    stack_offset_1 = [array[0] for array in arrays]
    stack_offset_2 = [array[1] for array in arrays]
    stack_offset_3 = [array[2] for array in arrays]
    stack_offset_4 = [array[3] for array in arrays]
    stack_offset_5 = [array[4] for array in arrays]
    stack_offset_6 = [array[5] for array in arrays]

    stacked_source = ColumnDataSource(data=dict(cities=['北京', '成都', '广州', '上海', '沈阳'],
                                                desc=['空气污染情况较严重',
                                                      '空气污染情况较严重',
                                                      '在5个城市中,空气污染相对较轻',
                                                      '在5个城市中,空气污染相对较轻',
                                                      '空气污染情况较严重'],
                                                stack_offset_0=stack_offset_0, stack_offset_1=stack_offset_1,
                                                stack_offset_2=stack_offset_2, stack_offset_3=stack_offset_3,
                                                stack_offset_4=stack_offset_4, stack_offset_5=stack_offset_5,
                                                stack_offset_6=stack_offset_6))

    ########################################################################################

    # 绘制线图,生成bokeh document
    doc = make_categorical(source, stacked_source, mode='local')

    output_file('example_categorical.html')
    save(doc)

