from flask_wtf import Form

from wtforms.validators import DataRequired, Length, Optional, Regexp
from wtforms_components import EmailField, Email, Unique

from lib.util_wtforms import ModelForm
from turboquant.blueprints.user.models import User, db


class EmailForm(ModelForm):
    email = EmailField(validators=[
        DataRequired(),
        Email(),
        Unique(
            User.email,
            get_session=lambda: db.session
        )
    ])
