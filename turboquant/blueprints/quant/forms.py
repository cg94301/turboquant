from flask_wtf import Form
from wtforms import TextAreaField, IntegerField, FloatField
from wtforms_components import EmailField
from wtforms.validators import DataRequired, Length, NumberRange


class XGBForm(Form):
    #num_round = IntegerField("How many trees?", [DataRequired(), NumberRange(min=1, max=1000)])
    #max_depth = IntegerField("How deep?", [DataRequired(), NumberRange(min=1, max=10)])
    #eta = FloatField("How fast?", [DataRequired()])
    num_round = IntegerField("How many trees?")
    max_depth = IntegerField("How deep?")
    eta = FloatField("How fast?")
