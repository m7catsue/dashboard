# -*- coding: utf-8 -*-
import os.path
import math
import pandas as pd
import seaborn as sns
from bokeh.plotting import Figure
from bokeh.models import ColumnDataSource, CustomJS, Legend, Patches, \
    HoverTool, PanTool, WheelZoomTool, BoxZoomTool, ResetTool, TapTool
from bokeh.models.widgets import RadioGroup
from bokeh.layouts import row


def make_cn_data_source(var_dict, num_color_level=7, log_scale=False):
    """
    生成用于绘制中国地图heat map的DataSource
    """
    basedir = os.path.abspath(os.path.dirname(__file__))
    map_data_dir = os.path.join(basedir, 'map_data')
    cn_features = pd.read_json(os.path.join(map_data_dir, 'china.json'))['features']   # 34个省级行政单位

    # 复制var_dict;var_dict为原始数据(tooltips显示),var_dict_plt用于决定color_index(可能作数值变换)
    var_dict_plt = var_dict.copy()

    # var_dict_plt(可能作数值变换)用于决定color_index; var_dict是真实值,不进行变换
    if log_scale:
        for key in var_dict_plt:
            var_dict_plt[key] = math.log(var_dict_plt[key])
            if var_dict_plt[key] < 0:
                var_dict_plt[key] = 0

    # 数值c用于决定各地区的color_index(用var_dict_plt中数据)
    colors_0 = sns.color_palette('Reds', num_color_level).as_hex()
    colors_1 = sns.color_palette('PuBu', num_color_level).as_hex()
    colors_2 = sns.color_palette('PuBuGn', num_color_level).as_hex()
    c = max(var_dict_plt.values()) / (num_color_level - 1)

    province_xs = []             # to plot bountries
    province_ys = []             # to plot bountries
    province_names = []          # to display province name
    province_vars = []           # to display province variable value
    province_colors_0 = []       # to display province color
    province_colors_1 = []
    province_colors_2 = []

    for province_obj in cn_features:
        province_name = province_obj['properties']['name']
        province_var = var_dict.get(province_name, 0)               # 在地图上显示var_dict中的真实值
        province_var_scaled = var_dict_plt.get(province_name, 0)    # province_var_scaled(var_dict_plt)用于决定color_index
        geometry_type = province_obj['geometry']['type']

        if geometry_type == 'MultiPolygon':
            for poly_coords in province_obj['geometry']['coordinates']:
                coords = poly_coords[0]
                province_xs.append(list(map(lambda x: x[0], coords)))
                province_ys.append(list(map(lambda x: x[1], coords)))
                # [IMP] for循环几次append几次 country_name, country_var, country_color
                province_names.append(province_name)
                province_vars.append(province_var)                  # province_var是真实值
                if float(province_var_scaled) > 0:
                    color_index = int(round(province_var_scaled / c, 0))
                    province_colors_0.append(colors_0[color_index])
                    province_colors_1.append(colors_1[color_index])
                    province_colors_2.append(colors_2[color_index])
                else:
                    province_colors_0.append(colors_0[0])           # 若var_dict中value为0,使用colors[0]
                    province_colors_1.append(colors_1[0])
                    province_colors_2.append(colors_2[0])
        else:
            coords = province_obj['geometry']['coordinates'][0]
            province_xs.append(list(map(lambda x: x[0], coords)))
            province_ys.append(list(map(lambda x: x[1], coords)))
            province_names.append(province_name)
            province_vars.append(province_var)                      # province_var用于tooltips显示真实值

            if float(province_var_scaled) > 0:
                color_index = int(round(province_var_scaled / c, 0))
                province_colors_0.append(colors_0[color_index])
                province_colors_1.append(colors_1[color_index])
                province_colors_2.append(colors_2[color_index])
            else:
                province_colors_0.append(colors_0[0])               # 若var_dict中value为0,使用colors[0]
                province_colors_1.append(colors_1[0])
                province_colors_2.append(colors_2[0])

    cn_source = ColumnDataSource(data=dict(province_xs=province_xs,
                                           province_ys=province_ys,
                                           province_name=province_names,
                                           province_var=province_vars,
                                           colors_0=province_colors_0,
                                           colors_1=province_colors_1,
                                           colors_2=province_colors_2,
                                           colors_plt=province_colors_0))
    return cn_source


def plot_cn_map(data_source, mode='web'):
    """
    绘制基于中国地图的heat map
    """
    if mode not in ['web', 'local']:
        raise ValueError("Error: 'mode' parameter must be 'web' or 'local'!")

    hover = HoverTool(tooltips=[('Province', '@province_name'),
                                ('Value', '@province_var')],
                      point_policy='follow_mouse')
    tools = [PanTool(), WheelZoomTool(), BoxZoomTool(), TapTool(), hover, ResetTool()]

    fig = Figure(plot_width=720, plot_height=405, title='2016中国各省份空气污染物浓度示意图 (随机模拟数据)',
                 toolbar_location='above', tools=tools, logo=None, webgl=True)  # webgl=True: allows rendering via GPUs
    fig.patches('province_xs', 'province_ys',
                fill_color='colors_plt', fill_alpha=0.7,
                line_color="white", line_width=1.0,
                source=data_source)

    # 添加可选择heat map颜色的widget
    select_color = RadioGroup(labels=['配色方案: Reds', '配色方案: PuBu', '配色方案: PuBuGn'], active=0)
    callback = CustomJS(args=dict(source=data_source), code="""
        var data = source.data;
        var active = String(cb_obj.active);
        var mapping = {
            0: 'colors_0',
            1: 'colors_1',
            2: 'colors_2'
        }
        for (let i=0; i<data['province_name'].length; i++) {
            data['colors_plt'][i] = data[mapping[active]][i]
        }
        source.trigger('change');
    """)

    select_color.js_on_change('active', callback)

    if mode == 'web':
        return row(fig, select_color)
    if mode == 'local':
        return row(fig, select_color)


###################################################################################################################

states_ref = {'AK': 'Alaska', 'AL': 'Alabama','AR': 'Arkansas', 'AS': 'American Samoa', 'AZ': 'Arizona',
              'CA': 'California', 'CO': 'Colorado', 'CT': 'Connecticut', 'DC': 'District of Columbia',
              'DE': 'Delaware', 'FL': 'Florida', 'GA': 'Georgia', 'GU': 'Guam', 'HI': 'Hawaii',
              'IA': 'Iowa', 'ID': 'Idaho', 'IL': 'Illinois', 'IN': 'Indiana', 'KS': 'Kansas', 'KY': 'Kentucky',
              'LA': 'Louisiana', 'MA': 'Massachusetts', 'MD': 'Maryland', 'ME': 'Maine', 'MI': 'Michigan',
              'MN': 'Minnesota', 'MO': 'Missouri', 'MP': 'Northern Mariana Islands', 'MS': 'Mississippi',
              'MT': 'Montana', 'NA': 'National', 'NC': 'North Carolina', 'ND': 'North Dakota', 'NE': 'Nebraska',
              'NH': 'New Hampshire', 'NJ': 'New Jersey', 'NM': 'New Mexico', 'NV': 'Nevada',
              'NY': 'New York', 'OH': 'Ohio', 'OK': 'Oklahoma', 'OR': 'Oregon', 'PA': 'Pennsylvania',
              'PR': 'Puerto Rico', 'RI': 'Rhode Island', 'SC': 'South Carolina', 'SD': 'South Dakota',
              'TN': 'Tennessee', 'TX': 'Texas', 'UT': 'Utah', 'VA': 'Virginia', 'VI': 'Virgin Islands',
              'VT': 'Vermont', 'WA': 'Washington', 'WI': 'Wisconsin', 'WV': 'West Virginia', 'WY': 'Wyoming'}


def make_us_county_data_source(var_dict, num_color_level=7, log_scale=False):
    """
    生成用于绘制美国地图heat map的DataSource (county level)
    """
    from bokeh.sampledata.us_states import data as states            # dict
    from bokeh.sampledata.us_counties import data as counties        # dict

    EXCLUDED = ("ak", "hi", "pr", "gu", "vi", "mp", "as")            # 对于'conties'排除这些州
    state_xs = [states[code]["lons"] for code in states if code.lower() not in EXCLUDED]
    state_ys = [states[code]["lats"] for code in states if code.lower() not in EXCLUDED]
    county_xs = [counties[code]["lons"] for code in counties if counties[code]["state"] not in EXCLUDED]
    county_ys = [counties[code]["lats"] for code in counties if counties[code]["state"] not in EXCLUDED]

    # 复制var_dict;var_dict为原始数据(tooltips显示),var_dict_plt用于决定color_index(可能作数值变换)
    var_dict_plt = var_dict.copy()

    # var_dict_plt(可能作数值变换)用于决定color_index; var_dict是真实值,不进行变换
    if log_scale:
        for key in var_dict_plt:
            var_dict_plt[key] = math.log(var_dict_plt[key])
            if var_dict_plt[key] < 0:
                var_dict_plt[key] = 0

    # 数值c用于决定各地区的color_index(用var_dict_plt中数据)
    colors = sns.color_palette('Blues', num_color_level).as_hex()
    c = max(var_dict_plt.values()) / (num_color_level - 1)

    county_names = []
    county_state_names = []
    county_variables = []
    county_colors = []

    for county_id in counties.keys():
        if counties[county_id]["state"] in EXCLUDED:
            continue
        county_name = counties[county_id]['name']
        county_state_code = counties[county_id]['state'].upper()
        county_state_name = states_ref[county_state_code]
        county_var = var_dict.get(county_name, 0)                     # 用于tooltips显示的真实值 (var_dict)
        county_var_scaled = var_dict_plt.get(county_name, 0)          # 用于决定color_index (var_dict_plt)

        county_names.append(county_name)
        county_state_names.append(county_state_name)
        county_variables.append(county_var)

        if float(county_var_scaled) > 0:
            color_index = int(round(county_var_scaled / c, 0))
            county_colors.append(colors[color_index])
        else:
            county_colors.append(colors[0])                           # 若var_dict中value为0,使用colors[0]

    us_source = ColumnDataSource(data=dict(state_xs=state_xs, state_ys=state_ys,
                                           county_xs=county_xs, county_ys=county_ys,
                                           county_names=county_names,
                                           county_state_names=county_state_names,
                                           colors=county_colors,
                                           county_vars=county_variables))
    return us_source


def plot_us_county_map(data_source, mode='web'):
    """
    绘制基于美国地图的heat map (county_level)
    """
    if mode not in ['web', 'local']:
        raise ValueError("Error: 'mode' parameter must be 'web' or 'local'!")

    hover = HoverTool(tooltips=[('State', '@county_state_names'),
                                ('County', '@county_names'),
                                ('Value', '@county_vars')],
                      point_policy='follow_mouse')
    tools = [PanTool(), WheelZoomTool(), BoxZoomTool(), TapTool(), hover, ResetTool()]

    fig = Figure(plot_width=1280, plot_height=720, title="2016美国空气污染物浓度示意图 (随机模拟数据)",
                 toolbar_location="right", tools=tools, logo=None, webgl=True)  # webgl=True: allows rendering via GPUs

    fig.patches('state_xs', 'state_ys', fill_alpha=0.7,
                line_color="#884444", line_width=2, line_alpha=0.3,
                source=data_source)

    fig.patches('county_xs', 'county_ys',                                       # polygons are called Patches in Bokeh
                fill_color='colors', fill_alpha=0.7,
                line_color="white", line_width=1.0,
                source=data_source)

    if mode == 'web':
        return fig
    if mode == 'local':
        return fig


####################################################################################################################

def make_us_state_data_source(var_dict, num_color_level=7, log_scale=False):
    """
    生成用于绘制美国地图heat map的DataSource (state level)
    """
    from bokeh.sampledata.us_states import data as states  # dict

    EXCLUDED = ("ak", "hi", "pr", "gu", "vi", "mp", "as")  # 对于'conties'排除这些州
    state_xs = [states[code]["lons"] for code in states if code.lower() not in EXCLUDED]
    state_ys = [states[code]["lats"] for code in states if code.lower() not in EXCLUDED]

    # 复制var_dict;var_dict为原始数据(tooltips显示),var_dict_plt用于决定color_index(可能作数值变换)
    var_dict_plt = var_dict.copy()

    # var_dict_plt(可能作数值变换)用于决定color_index; var_dict是真实值,不进行变换
    if log_scale:
        for key in var_dict_plt:
            var_dict_plt[key] = math.log(var_dict_plt[key])
            if var_dict_plt[key] < 0:
                var_dict_plt[key] = 0

    # 数值c用于决定各地区的color_index(用var_dict_plt中数据)
    colors_0 = sns.color_palette('Reds', num_color_level).as_hex()
    colors_1 = sns.color_palette('PuBu', num_color_level).as_hex()
    colors_2 = sns.color_palette('PuBuGn', num_color_level).as_hex()
    c = max(var_dict_plt.values()) / (num_color_level - 1)

    state_names = []
    state_variables = []
    state_colors_0 = []
    state_colors_1 = []
    state_colors_2 = []

    for state_code in states.keys():
        if state_code.lower() in EXCLUDED:
            continue
        state_name = states_ref[state_code]
        state_var = var_dict.get(state_code, 0)               # 用于tooltips显示的真实值 (var_dict)
        state_var_scaled = var_dict_plt.get(state_code, 0)    # 用于决定color_index (var_dict_plt)

        state_names.append(state_name)
        state_variables.append(state_var)

        if float(state_var_scaled) > 0:
            color_index = int(round(state_var_scaled / c, 0))
            state_colors_0.append(colors_0[color_index])
            state_colors_1.append(colors_1[color_index])
            state_colors_2.append(colors_2[color_index])
        else:
            state_colors_0.append(colors_0[0])                # 若var_dict中value为0,使用colors[0]
            state_colors_1.append(colors_1[0])
            state_colors_2.append(colors_2[0])

    us_source = ColumnDataSource(data=dict(state_xs=state_xs, state_ys=state_ys,
                                           state_name=state_names,
                                           state_vars=state_variables,
                                           colors_0=state_colors_0,
                                           colors_1=state_colors_1,
                                           colors_2=state_colors_2,
                                           colors_plt=state_colors_0))
    return us_source


def plot_us_state_map(data_source, mode='web'):
    """
    绘制基于美国地图的heat map (state_level)
    """
    if mode not in ['web', 'local']:
        raise ValueError("Error: 'mode' parameter must be 'web' or 'local'!")

    hover = HoverTool(tooltips=[('State', '@state_name'),
                                ('Value', '@state_vars')],
                      point_policy='follow_mouse')
    tools = [PanTool(), WheelZoomTool(), BoxZoomTool(), TapTool(), hover, ResetTool()]

    fig = Figure(plot_width=720, plot_height=405, title="2016美国各州空气污染物浓度示意图 (随机模拟数据)",
                 toolbar_location="above", tools=tools, logo=None, webgl=True)  # webgl=True: allows rendering via GPUs

    fig.patches('state_xs', 'state_ys',
                fill_color='colors_plt', fill_alpha=0.7,
                line_color="white", line_width=1.0,
                source=data_source)

    # 添加可选择heat map颜色的widget
    select_color = RadioGroup(labels=['配色方案: Reds', '配色方案: PuBu', '配色方案: PuBuGn'], active=0)
    callback = CustomJS(args=dict(source=data_source), code="""
            var data = source.data;
            var active = String(cb_obj.active);
            var mapping = {
                0: 'colors_0',
                1: 'colors_1',
                2: 'colors_2'
            }
            for (let i=0; i<data['state_name'].length; i++) {
                data['colors_plt'][i] = data[mapping[active]][i]
            }
            source.trigger('change');
        """)

    select_color.js_on_change('active', callback)

    if mode == 'web':
        return row(fig, select_color)
    if mode == 'local':
        return row(fig, select_color)


###################################################################################################################
def make_world_data_source(var_dict, num_color_level=9, log_scale=False):
    """
    生成用于绘制世界地图heat map的DataSource
    """
    basedir = os.path.abspath(os.path.dirname(__file__))
    map_data_dir = os.path.join(basedir, 'map_data')
    features = pd.read_json(os.path.join(map_data_dir, 'world-countries.json'))['features']

    #features = requests.get('https://raw.githubusercontent.com/datasets/'
                            #'geo-boundaries-world-110m/master/countries.geojson').json()['features']

    # 复制var_dict;var_dict为原始数据(tooltips显示),var_dict_plt用于决定color_index(可能作数值变换)
    var_dict_plt = var_dict.copy()

    # var_dict_plt(可能作数值变换)用于决定color_index; var_dict是真实值,不进行变换
    if log_scale:
        for key in var_dict_plt:
            var_dict_plt[key] = math.log(var_dict_plt[key])
            if var_dict_plt[key] < 0:
                var_dict_plt[key] = 0

    # 数值c用于决定各地区的color_index(用var_dict_plt中数据)
    colors_0 = sns.color_palette('RdBu_r', num_color_level).as_hex()
    colors_1 = sns.color_palette('PuBu', num_color_level).as_hex()
    colors_2 = sns.color_palette('PuBuGn', num_color_level).as_hex()
    c = max(var_dict_plt.values()) / (num_color_level - 1)

    country_xs = []                   # to plot bountries
    country_ys = []                   # to plot bountries
    country_names = []                # to display province name
    country_vars = []                 # to display province variable value
    country_colors_0 = []             # to display province color
    country_colors_1 = []
    country_colors_2 = []

    for country_obj in features:
        country_name = country_obj['properties']['name']
        country_var = var_dict.get(country_name, 0)             # 在地图上显示var_dict中的真实值
        country_var_scaled = var_dict_plt.get(country_name, 0)  # province_var_scaled(var_dict_plt)用于决定color_index
        geometry_type = country_obj['geometry']['type']

        # coordinates for 'MultiPolygon' should contain one more level of arrays
        if geometry_type == 'MultiPolygon':
            for poly_coords in country_obj['geometry']['coordinates']:
                coords = poly_coords[0]
                country_xs.append(list(map(lambda x: x[0], coords)))
                country_ys.append(list(map(lambda x: x[1], coords)))
                # [IMP] for循环几次append几次 country_name, country_var, country_color
                country_names.append(country_name)
                country_vars.append(country_var)                # province_var是真实值
                if float(country_var_scaled) > 0:
                    color_index = int(round(country_var_scaled / c, 0))
                    country_colors_0.append(colors_0[color_index])
                    country_colors_1.append(colors_1[color_index])
                    country_colors_2.append(colors_2[color_index])
                else:
                    country_colors_0.append(colors_0[0])        # 若var_dict中value为0,使用colors[0]
                    country_colors_1.append(colors_1[0])
                    country_colors_2.append(colors_2[0])

        else:
            coords = country_obj['geometry']['coordinates'][0]
            country_xs.append(list(map(lambda x: x[0], coords)))
            country_ys.append(list(map(lambda x: x[1], coords)))
            country_names.append(country_name)
            country_vars.append(country_var)  # province_var用于tooltips显示真实值

            if float(country_var_scaled) > 0:
                color_index = int(round(country_var_scaled / c, 0))
                country_colors_0.append(colors_0[color_index])
                country_colors_1.append(colors_1[color_index])
                country_colors_2.append(colors_2[color_index])
            else:
                country_colors_0.append(colors_0[0])  # 若var_dict中value为0,使用colors[0]
                country_colors_1.append(colors_1[0])
                country_colors_2.append(colors_2[0])

    world_source = ColumnDataSource(data=dict(country_xs=country_xs,
                                              country_ys=country_ys,
                                              country_name=country_names,
                                              country_var=country_vars,
                                              colors_0=country_colors_0,
                                              colors_1=country_colors_1,
                                              colors_2=country_colors_2,
                                              colors_plt=country_colors_1))
    return world_source


def plot_world_map(data_source, mode='web'):
    """绘制基于世界地图的heat map"""
    if mode not in ['web', 'local']:
        raise ValueError("Error: 'mode' parameter must be 'web' or 'local'!")

    hover = HoverTool(tooltips=[('Country', '@country_name'),
                                ('Value', '@country_var')],
                      point_policy='follow_mouse')
    tools = [PanTool(), WheelZoomTool(), BoxZoomTool(), TapTool(), hover, ResetTool()]

    fig = Figure(plot_width=720, plot_height=405, title='2016世界各国空气污染物浓度示意图 (随机模拟数据)',
                 toolbar_location='above', tools=tools, logo=None, webgl=True)  # webgl=True: allows rendering via GPUs
    fig.patches('country_xs', 'country_ys',
                fill_color='colors_plt', fill_alpha=0.7,
                line_color="white", line_width=0.5,
                source=data_source)

    # 添加可选择heat map颜色的widget
    select_color = RadioGroup(labels=['配色方案: RdBu_r', '配色方案: PuBu', '配色方案: PuBuGn'], active=1)
    callback = CustomJS(args=dict(source=data_source), code="""
            var data = source.data;
            var active = String(cb_obj.active);
            var mapping = {
                0: 'colors_0',
                1: 'colors_1',
                2: 'colors_2'
            }
            for (let i=0; i<data['country_name'].length; i++) {
                data['colors_plt'][i] = data[mapping[active]][i]
            }
            source.trigger('change');
        """)

    select_color.js_on_change('active', callback)

    if mode == 'web':
        return row(fig, select_color)
    if mode == 'local':
        return row(fig, select_color)


if __name__ == '__main__':
    import os.path
    import random
    import pandas as pd
    from bokeh.models.widgets import Panel, Tabs
    from bokeh.io import output_file, show

    #######################################################################################################
    # 生成中国个省份的模拟数据(var_dict_cn)
    var_dict_cn = dict()
    basedir = os.path.abspath(os.path.dirname(__file__))                              # 本文件所在文件夹的绝对路径
    map_data_dir = os.path.join(basedir, 'map_data')                                  # 地图数据所在的文件夹
    cn_features = pd.read_json(os.path.join(map_data_dir, 'china.json'))['features']

    for province_obj in cn_features:
        province_name = province_obj['properties']['name']
        var_dict_cn[province_name] = random.randint(30, 500)

    source_cn = make_cn_data_source(var_dict_cn, num_color_level=7, log_scale=False)
    fig_cn = plot_cn_map(source_cn, mode='local')

    #######################################################################################################
    # 生成美国各州/各县的模拟数据(var_dict_us)
    from bokeh.sampledata.us_states import data as states                             # dict
    from bokeh.sampledata.us_counties import data as counties                         # dict
    EXCLUDED = ("ak", "hi", "pr", "gu", "vi", "mp", "as")

    """
    var_dict_us_county = dict()
    for county_id in counties:
        if counties[county_id]["state"] in EXCLUDED:
            continue
        county_name = counties[county_id]['name']
        var_dict_us_county[county_name] = random.randint(10, 300)

    source_us_county = make_us_county_data_source(var_dict_us_county, num_color_level=7, log_scale=False)
    fig_us_county = plot_us_county_map(source_us_county, mode='local')
    show(fig_us_county)
    """

    var_dict_us_state = dict()
    for state_code in states.keys():
        if state_code.lower() in EXCLUDED:
            continue
        var_dict_us_state[state_code] = random.randint(10, 250)

    source_us_state = make_us_state_data_source(var_dict_us_state, num_color_level=7, log_scale=False)
    fig_us_state = plot_us_state_map(source_us_state, mode='local')

    #######################################################################################################
    # 生成世界各国的模拟数据(var_dict_world)
    var_dict_country = dict()
    basedir = os.path.abspath(os.path.dirname(__file__))
    map_data_dir = os.path.join(basedir, 'map_data')
    features = pd.read_json(os.path.join(map_data_dir, 'world-countries.json'))['features']
    # features = requests.get('https://raw.githubusercontent.com/datasets/'
    #                         'geo-boundaries-world-110m/master/countries.geojson').json()['features']
    for country_obj in features:
        country_name = country_obj['properties']['name']
        var_dict_country[country_name] = random.randint(10, 300)

    source_world = make_world_data_source(var_dict_country, num_color_level=7, log_scale=False)
    fig_world = plot_world_map(source_world, mode='local')

    #######################################################################################################

    # 使用Panel和Tab:
    tab1 = Panel(child=fig_cn, title='中国地图')
    tab2 = Panel(child=fig_us_state, title='美国地图')
    tab3 = Panel(child=fig_world, title='世界地图')

    tabs = Tabs(tabs=[tab1, tab2, tab3], width=1050, height=540, active=2)

    output_file('example_heat_maps.html')
    show(tabs)



