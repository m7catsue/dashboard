# -*- coding: utf-8 -*-
# 生成bokeh作图所需的DataSource
import os.path
import random
import math
import pandas as pd
from seaborn import color_palette
from bokeh.models import ColumnDataSource

from plots.plot_02_categorical import get_aqi_level
from plots.plot_04_heatmap import make_cn_data_source, make_us_state_data_source, make_world_data_source

base_sql_0 = "SELECT * FROM aqi_data WHERE year='%s'"
base_sql_1 = "SELECT city, date, mean_val from aqi_data WHERE year=%s"


def make_source_line(db, base_year=2015):
    """
    生成作线图make_line_plot()所需的DataSource;
    数据库连接db=g._database,由视图函数提供
    """
    df = pd.read_sql(base_sql_0 % base_year, con=db)
    df['date'] = pd.to_datetime(df['date'])
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
    return source


def make_source_categorical(db, base_year=2015):
    """
    生成作柱形图/饼图make_categorical()所需的DataSource;
    数据库连接db=g._database,由视图函数提供
    """
    df = pd.read_sql(base_sql_1 % base_year, con=db)
    df['level'] = df['mean_val'].apply(get_aqi_level)
    df = pd.DataFrame(df.groupby(['city', 'level'])['date'].count()).reset_index(level=['city', 'level'])
    df.rename(columns={'date': 'num_days'}, inplace=True)

    # GroupBy结果可能出现某一类型缺失的情况:如2015年成都没有空气质量等级为'好'的情况
    levels = ['好', '中等', '对敏感人群不健康', '不健康', '非常不健康', '有毒害']
    info = ['空气质量令人满意，基本无空气污染',
            '空气质量可接受，但某些污染物可能对极少数异常敏感的人群健康有较弱影响',
            '易感人群症状有轻度增加，健康人群出现刺激症状',
            '进一步加剧易感人群症状，可能对健康人群心脏、呼吸系统有影响',
            '心脏病和肺病患者症状显著加剧，运动耐受力降低，健康人群普遍出现症状',
            '健康人群运动耐受力降低，有明显强烈症状，提前出现某些疾病']

    bj = dict(df[df['city'] == 'Beijing'][['level', 'num_days']].set_index('level')[
                  'num_days'])  # dict(Series)由series得到dict:key是series.index
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

    percents_bj_rounded = ['%.2f%%' % (x / counts_bj.sum() * 100) for x in
                               counts_bj]  # 用于饼图tooltips的显示:将格式转换为保留2位小数的百分数
    percents_cd_rounded = ['%.2f%%' % (x / counts_cd.sum() * 100) for x in counts_cd]  # '%%'用于escape百分符号('%')
    percents_gz_rounded = ['%.2f%%' % (x / counts_gz.sum() * 100) for x in counts_gz]
    percents_sh_rounded = ['%.2f%%' % (x / counts_sh.sum() * 100) for x in counts_sh]
    percents_sy_rounded = ['%.2f%%' % (x / counts_sy.sum() * 100) for x in counts_sy]

    # start_angles/end_angles: 依据各类型的占比得到作饼图所需的各类的起始/终止的弧度(使用累计百分数计算)
    # (*)start_angles列表左端增加新元素0(累计百分比0%),end_angles列表即percents_xx(最后一个元素是累计百分比100%) [IMP]
    # 上述操作(*)步骤也保证了ColumnDataSource所有列长度相
    start_angles_bj = [2 * math.pi * p for p in ([0] + percents_bj[:-1])]; end_angles_bj = [2 * math.pi * p for p in percents_bj]
    start_angles_cd = [2 * math.pi * p for p in ([0] + percents_cd[:-1])]; end_angles_cd = [2 * math.pi * p for p in percents_cd]
    start_angles_gz = [2 * math.pi * p for p in ([0] + percents_gz[:-1])]; end_angles_gz = [2 * math.pi * p for p in percents_gz]
    start_angles_sh = [2 * math.pi * p for p in ([0] + percents_sh[:-1])]; end_angles_sh = [2 * math.pi * p for p in percents_sh]
    start_angles_sy = [2 * math.pi * p for p in ([0] + percents_sy[:-1])]; end_angles_sy = [2 * math.pi * p for p in percents_sy]

    # ColumnDataSource所有列必须长度相同 [IMP]
    data = dict(labels=levels, info=info,
                x_loc=[1, 2, 3, 4, 5, 6],  # [IMP] x_loc是作柱状图时的x轴坐标;作柱状图x_loc和labels的顺序必须一一对应
                colors=color_palette('RdBu_r', 6).as_hex(),  # [IMP] 通过seaborn获得渐变颜色的hex值;最后的'_r'表示reverse

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
    ##########################################################################################

    return source, stacked_source


def make_var_dict_cn():
    """绘制中国热力图所需的模拟数据"""
    var_dict_cn = dict()
    basedir = os.path.abspath(os.path.dirname(__file__))                  # 本文件所在文件夹的绝对路径
    map_data_dir = os.path.join(basedir, 'plots', 'map_data')             # 地图数据所在的文件夹
    cn_features = pd.read_json(os.path.join(map_data_dir, 'china.json'))['features']

    for province_obj in cn_features:
        province_name = province_obj['properties']['name']
        var_dict_cn[province_name] = random.randint(30, 500)
    return var_dict_cn


def make_var_dict_us_state():
    """绘制美国(州)热力图所需的模拟数据"""
    from bokeh.sampledata.us_states import data as states
    EXCLUDED = ("ak", "hi", "pr", "gu", "vi", "mp", "as")

    var_dict_us_state = dict()
    for state_code in states.keys():
        if state_code.lower() in EXCLUDED:
            continue
        var_dict_us_state[state_code] = random.randint(10, 250)
    return var_dict_us_state


def make_var_dict_world():
    """绘制世界热力图所需的模拟数据"""
    var_dict_country = dict()
    basedir = os.path.abspath(os.path.dirname(__file__))
    map_data_dir = os.path.join(basedir, 'plots', 'map_data')
    features = pd.read_json(os.path.join(map_data_dir, 'world-countries.json'))['features']
    # features = requests.get('https://raw.githubusercontent.com/datasets/'
    #                         'geo-boundaries-world-110m/master/countries.geojson').json()['features']

    for country_obj in features:
        country_name = country_obj['properties']['name']
        var_dict_country[country_name] = random.randint(10, 300)
    return var_dict_country
