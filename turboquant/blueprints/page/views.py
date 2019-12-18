from flask import Blueprint, render_template
from turboquant.blueprints.page.forms import EmailForm

page = Blueprint('page', __name__, template_folder='templates')


# @page.route('/')
# def index():
#    return redirect(url_for('user.login'))

@page.route('/', methods=['GET', 'POST'])
# @page.route('/index/')
def home():

    form = EmailForm()

    # Don't use label
    form.email.label.text = ''

    return render_template('page/home.html', form=form)


@page.route('/terms')
def terms():
    return render_template('page/terms.html')


@page.route('/privacy')
def privacy():
    return render_template('page/privacy.html')
