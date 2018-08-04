from flask import (
    Blueprint,
    redirect,
    request,
    flash,
    url_for,
    render_template)
from flask_login import login_required, current_user
from sqlalchemy import text

from turboquant.blueprints.quant.forms import XGBForm
from turboquant.blueprints.quant.models import Strategy


quant = Blueprint('quant', __name__,
                  template_folder='templates', url_prefix='/quant')


@quant.before_request
@login_required
def before_request():
    """ Protect all of the quant endpoints. """
    pass


# Dashboard -------------------------------------------------------------------
@quant.route('/dashboard/')
def dashboard():
    return render_template('quant/page/dashboard.html')


@quant.route('/data/')
def data():
    return render_template('quant/page/data.html')


@quant.route('/generate/', methods=['GET','POST'])
def generate():
    print "configuration:",request
    print "configuration:",request.form
    print "configuration:",request.form.get('csrf_token')
    print "configuration:",request.form.get('num-round')
    print "configuration:",request.form.get('max-depth')
    print "configuration:",request.form.get('eta')    

    print "current_user:",current_user.id
    # Pre-populate the email field if the user is signed in.
    #form = XGBForm(obj=current_user)
    form = XGBForm()

    if form.validate_on_submit():
        # This prevents circular imports.
        from turboquant.blueprints.quant.tasks import launch_xgb_job, launch_sfn_job

        # launch_xgb_job(request.form.get('num-round'),
        task = launch_sfn_job.delay(current_user.id,
                                    request.form.get('num-round'),
                                    request.form.get('max-depth'),
                                    request.form.get('eta'))

        flash('Thanks, expect a response shortly.', 'success')
        return redirect(url_for('quant.generate'))

    return render_template('quant/page/generate.html', form=form)

#@quant.route('/strategies/')
#def strategies():
#
#    return render_template('quant/page/strategies.html')

@quant.route('/strategies/', defaults={'page': 1})
@quant.route('/strategies/page/<int:page>')
def strategies(page):
    paginated_strategies = Strategy.query \
        .filter(Strategy.user_id == current_user.id) \
        .order_by(Strategy.created_on.desc()) \
        .paginate(page, 20, True)

    return render_template('quant/page/strategies.html', strategies=paginated_strategies)
