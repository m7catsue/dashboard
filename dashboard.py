# -*- coding: utf-8 -*-
import sys
import os.path
import sqlite3
import time
import math
import random

from flask import Flask, g, render_template, jsonify, redirect, url_for
from flask_bootstrap import Bootstrap
from flask_caching import Cache

from bokeh.models import AjaxDataSource
from bokeh.embed import components

from forms import YearSelectionForm, AqiQueryForm
from sources import make_source_line, make_source_categorical, make_var_dict_cn, make_var_dict_us_state, \
    make_var_dict_world, make_cn_data_source, make_us_state_data_source, make_world_data_source, make_source_matrix
from plots import make_line_plot, make_categorical, plot_cn_map, plot_us_state_map, plot_world_map, \
    make_bar_matrix, make_streaming_plots
from decorators import crossdomain

basedir = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.path.join(basedir, 'db_tmp.db')                # database path

app = Flask(__name__)
app.config['SECRET_KEY'] = 'm7catsue_evallery_indigo1990_secret_key'
app.config['DEBUG'] = True
if sys.platform == 'win32':                                  # 使用simple cache在windows环境下测试
    app.config['CACHE_TYPE'] = 'simple'
if sys.platform == 'linux':                                  # redis数据库需要Linux环境
    app.config['CACHE_TYPE'] = 'redis'
    app.config['CACHE_KEY_PREFIX'] = 'dashboard_cache'       # A prefix that is added before all keys, which makes it
    app.config['CACHE_REDIS_HOST'] = 'localhost'             # possible to use the same server for different apps.
    app.config['CACHE_REDIS_PORT'] = '6379'
    app.config['CACHE_REDIS_URL'] = 'redis://localhost:6379'

bootstrap = Bootstrap(app)
cache = Cache(app)  # [IMP] 需要在生成Cache实例前对其参数进行设置(app.config);或者生成cache实例时传入参数config={dict}


@app.before_request
def before_request():
    """在执行响应每个request之前;获得数据库连接(db=g._database);
    [IMP] g是app context global,因为其在before_request()函数中设定,所有视图函数在执行时都会获得g"""
    db = getattr(g, '_database', None)
    if not db:
        g.database = sqlite3.connect(DATABASE)


@app.teardown_appcontext
def close_db(exception):
    """teardown应用上下文时,关闭数据库连接"""
    db = getattr(g, '_database', None)
    if db:
        db.close()


@app.route('/')             # [IMP] @cache.cached装饰器须位于@route装饰器和视图函数之间,
@cache.cached(timeout=300)  # 否则缓存的将是@route装饰器的结果,而不是视图函数的结果
def index():
    """Dashboard Demo首页"""
    aqi_form = AqiQueryForm()                                # 导航栏AQI实时查询表单
    return render_template('index.html', aqi_form=aqi_form)


#############################
#
# (1) Dashboard
#
#############################


@app.route('/dashboard/<year>', methods=['GET', 'POST'])
def dashboard(year):
    """
    Dashboard页面视图函数;
    html模板中:从主页和导航栏重定向到dashboard页面将默认year初始值为2015
    """
    db = g.database                                          # get database connection
    aqi_form = AqiQueryForm()                                # 导航栏AQI实时查询表单
    form = YearSelectionForm()

    if form.validate_on_submit():                            # 用户通过表单新提交的年份:selected_year
        selected_year = form.year.data
        return redirect(url_for('dashboard', year=str(selected_year)))

    form.year.data = str(year)                               # 将页面中form的选项设为request.path中的年份(用户的上一次选择),
                                                             # 而不是form的默认选项'2015',使用户体验更具有一致性
    source_line = make_source_line(db, base_year=year)       # request.path中的年份:year
    source_cat1, source_cat2 = make_source_categorical(db, base_year=year)
    source_matrix = make_source_matrix(db, base_year=year)

    line_layout = make_line_plot(source_line, mode='web')
    categorical_layout = make_categorical(source_cat1, source_cat2, mode='web')
    bar_matrix_layout = make_bar_matrix(source_matrix, mode='web')

    script1, div1 = components(line_layout)
    script2, div2 = components(categorical_layout)
    script3, div3 = components(bar_matrix_layout)

    return render_template('dashboard.html', aqi_form=aqi_form,
                           form=form, year=year,
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
    """
    Heat Maps页面的视图函数
    """
    aqi_form = AqiQueryForm()                                 # 导航栏AQI实时查询表单
    from bokeh.models.widgets import Panel, Tabs
    source_cn = make_cn_data_source(make_var_dict_cn(), num_color_level=7, log_scale=False)
    source_us = make_us_state_data_source(make_var_dict_us_state(), num_color_level=7, log_scale=False)
    source_wd = make_world_data_source(make_var_dict_world(), num_color_level=9, log_scale=False)

    tab1 = Panel(child=plot_cn_map(source_cn, mode='web'), title='中国地图')
    tab2 = Panel(child=plot_us_state_map(source_us, mode='web'), title='美国地图')
    tab3 = Panel(child=plot_world_map(source_wd, mode='web'), title='世界地图')

    tabs = Tabs(tabs=[tab1, tab2, tab3], width=900, height=405, active=2)

    script_maps, div_maps = components(tabs)
    return render_template('maps.html', aqi_form=aqi_form,
                           script_maps=script_maps, div_maps=div_maps)


####################################
#
# (3) Plotting Streaming Data
#
####################################

server_start = time.time()  # 服务器启动时间


# 对于PUT、DELETE以及其他类型如application/json的POST请求，在发送AJAX请求之前，浏览器会先发送一个OPTIONS请求（称为preflighted请求）到这个URL上，询问目标服务器是否接受;
# 服务器必须响应并明确指出允许的Method;浏览器确认服务器响应的Access-Control-Allow-Methods头确实包含将要发送的AJAX请求的Method，才会继续发送AJAX，否则，抛出一个错误.
# http://www.liaoxuefeng.com/wiki/001434446689867b27157e896e74d51a89c25cc8b43bdb3000/001434499861493e7c35be5e0864769a2c06afb4754acc6000
@app.route('/data', methods=['GET', 'OPTIONS', 'POST'])
@crossdomain(origin="*", methods=['GET', 'POST'], headers=None)
def get_streaming_data():
    """
    生成streaming的模拟数据;
    构造模拟数据仅依赖"时间",而不能依靠其他全局变量(尤其是mutable对象),因为:
    (1)'/data'端节点模拟外部API,API请求应该保证"无状态"(stateless);
    (2)当有web应用有多个worker进程时,进程a使用某个全局变量,此时若另一个用户进行request则进程b也操作该全局变量,
       这时由于进程b也对全局变量的操作,进程a和进程b同时在使用/修改全局变量,导致data corruption;

    [IMP] 模拟API数据源, 须保证"无状态"(参见REST API中的stateless特性),所有信息都包含在请求中;
    [IMP] flask中的g,session等上下文全局变量无法通过Ajax请求(API请求)传递到本视图函数(即使这个endpoint隶属于dashboard站点);

    [INFO] 在dashboard demo中get_streaming_data()视图函数是 procedurally generate模拟数据,
           也可以将get_streaming_data()更改为(1)查询数据库并返回结果,(2)进行外部API请求并返回解析后的结果
    """
    x = (time.time() - server_start)
    y_sin = math.sin(x)
    y_cos = math.cos(x)
    y_random = random.uniform(-1, 1)
    return jsonify(x=x, y_sin=y_sin, y_cos=y_cos, y_random=y_random)


@app.route('/stream')
@cache.cached(timeout=300)  # streaming页面可以cache因为AjaxDataSource每次初始为空
def stream():
    """
    对streaming的模拟数据进行实时的数据可视化;

    [IMP] 对data_url参数使用url_for()动态生成相应地址,而不使用直接的地址,
    因为在windows环境下测试时,data_url需为'localhost:5000/data', 而在在AWS服务器上部署时,则需将data_url修改为EC2实例的公网ip;
    使用url_for()函数可省略上述对data_url的更改
    """
    aqi_form = AqiQueryForm()                                 # 导航栏AQI实时查询表单
    ajax_source = AjaxDataSource(data=dict(x=[], y_sin=[], y_cos=[], y_random=[]),
                                 data_url=url_for('get_streaming_data'),
                                 polling_interval=200, mode='append', max_size=500)
    fig_layout = make_streaming_plots(ajax_source, mode='web')

    script, div = components(fig_layout)
    return render_template('stream.html', aqi_form=aqi_form,
                           script_stream=script, div_stream=div)


if __name__ == '__main__':
    app.threaded = True
    app.run()

