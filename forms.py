# -*- coding: utf-8 -*-
from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField
from wtforms.validators import DataRequired


class YearSelectionForm(FlaskForm):
    """Dashboard页面选择年份的表单(static choices)"""
    year = SelectField('Select Year:', choices=[('2013', '2013年'), ('2014', '2014年'),
                                                ('2015', '2015年'), ('2016', '2016年(截止11月30日)')],
                       default='2015')
    submit = SubmitField('提交')

