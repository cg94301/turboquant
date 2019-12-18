from flask_wtf import FlaskForm
from wtforms import HiddenField, StringField, PasswordField
from wtforms.validators import DataRequired, Length, Optional, Regexp
from wtforms_alchemy.validators import Unique
from wtforms_components import EmailField, Email

from lib.util_wtforms import ModelForm
from turboquant.blueprints.user.models import User
from turboquant.blueprints.user.validations import ensure_identity_exists, \
    ensure_existing_password_matches


class LoginForm(FlaskForm):
    next = HiddenField()
    identity = StringField('Username or Email',
                           [DataRequired(), Length(3, 254)])
    password = PasswordField('Password', [DataRequired(), Length(8, 128)])
    # remember = BooleanField('Stay signed in')


class BeginPasswordResetForm(FlaskForm):
    identity = StringField('Username or Email',
                           [DataRequired(),
                            Length(3, 254),
                            ensure_identity_exists])


class PasswordResetForm(FlaskForm):
    reset_token = HiddenField()
    password = PasswordField('Password', [DataRequired(), Length(8, 128)])


class SignupForm(ModelForm):
    email = EmailField(validators=[
        DataRequired(),
        Email(),
        Unique(User.email)
    ])
    password = PasswordField('Password', [DataRequired(), Length(8, 128)])


class WelcomeForm(ModelForm):
    username_message = 'Letters, numbers and underscores only please.'

    username = StringField(validators=[
        Unique(User.username,),
        DataRequired(),
        Length(1, 16),
        Regexp(r'^\w+$', message=username_message)
    ])


class UpdateCredentials(ModelForm):
    current_password = PasswordField('Current password',
                                     [DataRequired(),
                                      Length(8, 128),
                                      ensure_existing_password_matches])

    email = EmailField(validators=[
        Email(),
        Unique(User.email)
    ])
    password = PasswordField('Password', [Optional(), Length(8, 128)])
