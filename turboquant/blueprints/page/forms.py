from wtforms.validators import DataRequired
from wtforms_alchemy.validators import Unique
from wtforms_components import EmailField, Email

from lib.util_wtforms import ModelForm
from turboquant.blueprints.user.models import User


class EmailForm(ModelForm):
    email = EmailField(validators=[
        DataRequired(),
        Email(),
        Unique(User.email)
    ])
