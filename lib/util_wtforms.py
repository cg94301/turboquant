from flask_wtf import FlaskForm
from wtforms_alchemy import model_form_factory

from turboquant.extensions import db

BaseModelForm = model_form_factory(FlaskForm)


class ModelForm(BaseModelForm):
    """
    Allow WTForms-Alchemy to work with Flask-WTF.
    """
    @classmethod
    def get_session(self):
        return db.session        

def choices_from_dict(source, prepend_blank=True):
    """
    Convert a dict to a format that's compatible with WTForm's choices. It also
    optionally prepends a "Please select one..." value.

    Example:
      # Convert this data structure:
      STATUS = OrderedDict([
          ('unread', 'Unread'),
          ('open', 'Open'),
          ('contacted', 'Contacted'),
          ('closed', 'Closed')
      ])

      # Into this:
      choices = [('', 'Please select one...'), ('unread', 'Unread) ...]

    :param source: Input source
    :type source: dict
    :param prepend_blank: An optional blank item
    :type prepend_blank: bool
    :return: list
    """
    choices = []

    if prepend_blank:
        choices.append(('', 'Please select one...'))

    for key, value in source.items():
        pair = (key, value)
        choices.append(pair)

    return choices


def choices_from_list(source, prepend_blank=True):
    """
    Convert a list to a format that's compatible with WTForm's choices. It also
    optionally prepends a "Please select one..." value.

    Example:
      # Convert this data structure:
      TIMEZONES = (
        'Africa/Abidjan',
        'Africa/Accra',
        'Africa/Addis_Ababa'
      )

      # Into this:
      choices = [('', 'Please select one...'),
                 ('Africa/Abidjan', 'Africa/Abidjan) ...]

    :param source: Input source
    :type source: list or tuple
    :param prepend_blank: An optional blank item
    :type prepend_blank: bool
    :return: list
    """
    choices = []

    if prepend_blank:
        choices.append(('', 'Please select one...'))

    for item in source:
        pair = (item, item)
        choices.append(pair)

    return choices
