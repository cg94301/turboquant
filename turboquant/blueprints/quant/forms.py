from collections import OrderedDict
from flask_wtf import Form
from wtforms import TextAreaField, IntegerField, FloatField, SelectField
from wtforms_components import EmailField
from wtforms.validators import DataRequired, Length, NumberRange
from lib.util_wtforms import choices_from_dict

class XGBForm(Form):
    #num_round = IntegerField("How many trees?", [DataRequired(), NumberRange(min=1, max=1000)])
    #max_depth = IntegerField("How deep?", [DataRequired(), NumberRange(min=1, max=10)])
    #eta = FloatField("How fast?", [DataRequired()])
    num_round_from = IntegerField()
    num_round_to = IntegerField()
    num_round_step = IntegerField()
    max_depth_from = IntegerField()
    max_depth_to = IntegerField()
    eta_from = FloatField()
    eta_to = FloatField()

    
class BulkDeleteForm(Form):
    SCOPE = OrderedDict([
        ('all_selected_items', 'All selected items'),
        ('all_items', 'ALL items')
    ])

    scope = SelectField('Privileges', [DataRequired()],
                        choices=choices_from_dict(SCOPE, prepend_blank=False))    
