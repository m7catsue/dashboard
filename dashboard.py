# -*- coding: utf-8 -*-
import os.path
import sqlite3
from flask import Flask, g, render_template, url_for
from flask_bootstrap import Bootstrap
from bokeh.embed import components
from forms import YearSelectionForm
from sources import make_source_line, make_source_categorical, make_var_dict_cn, make_var_dict_us_state, \
    make_var_dict_world, make_cn_data_source, make_us_state_data_source, make_world_data_source, make_source_matrix
from plots import make_line_plot, make_categorical, plot_cn_map, plot_us_state_map, plot_world_map, \
    make_bar_matrix

basedir = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.path.join(basedir, 'db_tmp.db')

app = Flask(__name__)
app.config['SECRET_KEY'] = 'm7catsue_evallery_indigo1990_secret_key'
bootstrap = Bootstrap(app)


def get_db():
    """获得数据库连接(db=g._database)"""
    db = getattr(g, '_database', None)
    if not db:
        db = g._database = sqlite3.connect(DATABASE)
    return db


@app.teardown_appcontext
def close_db(exception):
    """teardown应用上下文时,关闭数据库连接"""
    db = getattr(g, '_database', None)
    if db:
        db.close()


@app.route('/', methods=['GET', 'POST'])
def index():
    """Dashboard首页的视图函数"""
    db = get_db()                                   # get database connection
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

        return render_template('index.html',
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

    return render_template('index.html',
                           form=form, year=selected_year,
                           script1=script1, div1=div1,
                           script2=script2, div2=div2,
                           script3=script3, div3=div3)


@app.route('/heat_maps')
def heat_maps():
    """Dashboard热力图页面的视图函数"""
    from bokeh.models.widgets import Panel, Tabs
    source_cn = make_cn_data_source(make_var_dict_cn(), num_color_level=7, log_scale=False)
    source_us = make_us_state_data_source(make_var_dict_us_state(), num_color_level=7, log_scale=False)
    source_wd = make_world_data_source(make_var_dict_world(), num_color_level=9, log_scale=False)

    tab1 = Panel(child=plot_cn_map(source_cn, mode='web'), title='中国地图')
    tab2 = Panel(child=plot_us_state_map(source_us, mode='web'), title='美国地图')
    tab3 = Panel(child=plot_world_map(source_wd, mode='web'), title='世界地图')
    tabs = Tabs(tabs=[tab1, tab2, tab3], width=960, height=600, active=0)

    script_maps, div_maps = components(tabs)
    return render_template('maps.html',
                           script_maps=script_maps, div_maps=div_maps)


@app.route('/stream')
def stream():
    """单独任务"""
    return 'Not implemented yet.'


if __name__ == '__main__':
    app.run(debug=True)

