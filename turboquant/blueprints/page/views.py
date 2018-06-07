from flask import Blueprint, render_template, redirect, url_for

page = Blueprint('page', __name__, template_folder='templates')


#@page.route('/')
#def index():
#    return redirect(url_for('user.login'))

@page.route('/')
#@page.route('/index/')
def home():
    return render_template('page/home.html')


@page.route('/terms')
def terms():
    return render_template('page/terms.html')


@page.route('/privacy')
def privacy():
    return render_template('page/privacy.html')
