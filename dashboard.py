# -*- coding: utf-8 -*-
import os.path
import sqlite3
import redis
import json
import math
import random
import numpy as np

from flask import Flask, session, g, render_template, jsonify, url_for
from flask_bootstrap import Bootstrap
from flask_caching import Cache

from bokeh.models import AjaxDataSource
from bokeh.embed import components

from forms import YearSelectionForm
from sources import make_source_line, make_source_categorical, make_var_dict_cn, make_var_dict_us_state, \
    make_var_dict_world, make_cn_data_source, make_us_state_data_source, make_world_data_source, make_source_matrix
from plots import make_line_plot, make_categorical, plot_cn_map, plot_us_state_map, plot_world_map, \
    make_bar_matrix, make_streaming_plots
from decorators import crossdomain

basedir = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.path.join(basedir, 'db_tmp.db')                       # database path

redis_db = redis.StrictRedis(host="localhost", port=6379, db=0)     # create a global redis connection pool

app = Flask(__name__)
app.config['SECRET_KEY'] = 'm7catsue_evallery_indigo1990_secret_key'
app.config['DEBUG'] = True
bootstrap = Bootstrap(app)
# 使用simple cache在windows环境下测试
cache = Cache(app, config={'CACHE_TYPE': 'simple'})
#cache = Cache(app, config={
    #'CACHE_TYPE': 'redis',                            # redis数据库需要Linux环境
    #'CACHE_KEY_PREFIX': 'dashboard_cache',            # A prefix that is added before all keys, which makes it
    #'CACHE_REDIS_HOST': 'localhost',                  # possible to use the same server for different apps.
    #'CACHE_REDIS_PORT': '6379',
    #'CACHE_REDIS_URL': 'redis://localhost:6379'
#})


#x = list(np.arange(0, 1, 0.1))                         # streaming模拟数据
#y_sin = [math.sin(xi) for xi in x]
#y_cos = [math.cos(xi) for xi in x]
#y_random = [random.uniform(-1, 1) for i in range(10)]  # random.random()返回[0.0, 1.0)之间的浮点数


@app.before_request
def before_request():
    """在执行响应每个request之前:
    (1)获得数据库连接(db=g._database);
    (2)为浏览器设置临时id和streaming使用的初始数据;

    [IMP] g是app context global,因为其在before_request()函数中设定,所有视图函数在执行时都会获得g"""
    db = getattr(g, '_database', None)
    if not db:
        g.database = sqlite3.connect(DATABASE)

    if 'tmp_id' not in session:
        from string import ascii_lowercase
        tmp_id = ''.join(random.choice(ascii_lowercase) for i in range(12))
        session['tmp_id'] = tmp_id

        x = list(np.arange(0, 1, 0.1))
        y_sin = [math.sin(xi) for xi in x]
        y_cos = [math.cos(xi) for xi in x]
        y_random = [random.uniform(-1, 1) for i in range(10)]

        json_data = [x, y_sin, y_cos, y_random]
        json_string = json.dumps(json_data)

        redis_db.set(tmp_id, json_string)


@app.teardown_appcontext
def close_db(exception):
    """teardown应用上下文时,关闭数据库连接"""
    db = getattr(g, '_database', None)
    if db:
        db.close()


@app.route('/')
@cache.cached(timeout=300)  # 保存页面缓存5分钟(300秒)
def index():
    """Dashboard Demo首页"""
    return render_template('index.html')


#############################
#
# (1) Dashboard
#
#############################


@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    """Dashboard页面视图函数;
    dashboard页面不使用cache:若使用,则在选择提交其他年份进行查询时,会返回同一年份的缓存页面 [IMP]"""
    db = g.database                                 # get database connection
    form = YearSelectionForm()
    selected_year = form.year.data                  # get selected_year(string)

    if form.validate_on_submit():
        source_line = make_source_line(db, base_year=form.year.data)
        source_cat1, source_cat2 = make_source_categorical(db, base_year=form.year.data)
        source_matrix = make_source_matrix(db, base_year=form.year.data)

        line_layout = make_line_plot(source_line, mode='web')
        categorical_layout = make_categorical(source_cat1, source_cat2, mode='web')
        bar_matrix_layout = make_bar_matrix(source_matrix, mode='web')

        script1, div1 = components(line_layout)
        script2, div2 = components(categorical_layout)
        script3, div3 = components(bar_matrix_layout)

        return render_template('dashboard.html',
                               form=form, year=selected_year,
                               script1=script1, div1=div1,
                               script2=script2, div2=div2,
                               script3=script3, div3=div3)

    source_line = make_source_line(db, base_year=form.year.data)
    source_cat1, source_cat2 = make_source_categorical(db, base_year=form.year.data)
    source_matrix = make_source_matrix(db, base_year=form.year.data)

    line_layout = make_line_plot(source_line, mode='web')
    categorical_layout = make_categorical(source_cat1, source_cat2, mode='web')
    bar_matrix_layout = make_bar_matrix(source_matrix, mode='web')

    script1, div1 = components(line_layout)
    script2, div2 = components(categorical_layout)
    script3, div3 = components(bar_matrix_layout)

    return render_template('dashboard.html',
                           form=form, year=selected_year,
                           script1=script1, div1=div1,
                           script2=script2, div2=div2,
                           script3=script3, div3=div3)


##################################
#
# (2) Heat Maps
#
##################################


@app.route('/heat_maps')
@cache.cached(timeout=600)  # 保存页面缓存10分钟;heat map页面均为静态bokeh documents
def heat_maps():
    """Heat Maps页面的视图函数"""
    from bokeh.models.widgets import Panel, Tabs
    source_cn = make_cn_data_source(make_var_dict_cn(), num_color_level=7, log_scale=False)
    source_us = make_us_state_data_source(make_var_dict_us_state(), num_color_level=7, log_scale=False)
    source_wd = make_world_data_source(make_var_dict_world(), num_color_level=9, log_scale=False)

    tab1 = Panel(child=plot_cn_map(source_cn, mode='web'), title='中国地图')
    tab2 = Panel(child=plot_us_state_map(source_us, mode='web'), title='美国地图')
    tab3 = Panel(child=plot_world_map(source_wd, mode='web'), title='世界地图')

    tabs = Tabs(tabs=[tab1, tab2, tab3], width=900, height=405, active=2)

    script_maps, div_maps = components(tabs)
    return render_template('maps.html', script_maps=script_maps, div_maps=div_maps)


####################################
#
# (3) Plotting Streaming Data
#
####################################


@app.route('/data/<tmp_id>', methods=['GET', 'OPTIONS', 'POST'])
@crossdomain(origin="*", methods=['GET', 'POST'], headers=None)
def get_streaming_data(tmp_id):
    """生成streaming的模拟数据"""
    redis_db = redis.StrictRedis(host="localhost", port=6379, db=0)

    json_string = redis_db.get(tmp_id)
    json_data = json.loads(json_string).decode('utf-8')
    x, y_sin, y_cos, y_random = json_data[0], json_data[1], json_data[2], json_data[3]

    x.append(x[-1] + 0.1)
    y_sin.append(math.sin(x[-1]))
    y_cos.append(math.cos(x[-1]))
    y_random.append(random.uniform(-1, 1))

    new_json_data = [x, y_sin, y_cos, y_random]
    redis_db.set(tmp_id, json.dumps(new_json_data))

    return jsonify(x=x[-1], y_sin=y_sin[-1], y_cos=y_cos[-1], y_random=y_random[-1])


@app.route('/stream')
@cache.cached(timeout=120)
def stream():
    """对streaming的模拟数据进行实时的数据可视化;

    [IMP] 对data_url参数使用url_for()动态生成相应地址,而不使用直接的地址,
    因为在windows环境下测试时,data_url需为'localhost:5000/data', 而在在AWS服务器上部署时,则需将data_url修改为EC2实例的公网ip;
    使用url_for()函数可省略上述对data_url的更改"""
    print(session['tmp_id'])
    print(url_for('get_streaming_data', tmp_id=session['tmp_id']))
    ajax_source = AjaxDataSource(data=dict(x=[], y_sin=[], y_cos=[], y_random=[]),
                                 data_url=url_for('get_streaming_data', tmp_id=session['tmp_id']),
                                 polling_interval=200, mode='append', max_size=500)
    fig_layout = make_streaming_plots(ajax_source, mode='web')

    script, div = components(fig_layout)
    return render_template('stream.html', script_stream=script, div_stream=div)


if __name__ == '__main__':
    app.run(threaded=True)
    #app.run(processes=3)

