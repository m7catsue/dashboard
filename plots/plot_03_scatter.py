# -*- coding: utf-8 -*-
from bokeh.layouts import column, row, layout, gridplot, WidgetBox
from bokeh.models import ColumnDataSource, CustomJS, Legend, \
    HoverTool, PanTool, WheelZoomTool, BoxZoomTool, ResetTool
from bokeh.models.widgets import CheckboxButtonGroup, Dropdown, Select, Panel, Tabs
from bokeh.plotting import Figure
from bokeh.io import curdoc


def make_scatter_plot(data_source):
    """作散点图"""
    pass


if __name__ == '__main__':
    import os
    import sqlite3
    import pandas as pd
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
