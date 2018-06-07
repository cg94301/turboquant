from flask import (
    Blueprint,
    redirect,
    request,
    flash,
    url_for,
    render_template)
from flask_login import login_required, current_user
from sqlalchemy import text

from turboquant.blueprints.strategy.forms import XGBForm
from turboquant.blueprints.strategy.models import Dashboard

strategy = Blueprint('strategy', __name__,
                  template_folder='templates', url_prefix='/strategy')


@strategy.before_request
@login_required
def before_request():
    """ Protect all of the strategy endpoints. """
    pass


# Dashboard -------------------------------------------------------------------
@strategy.route('/dashboard/')
def dashboard():
    group_and_count_plans = Dashboard.group_and_count_plans()
    group_and_count_coupons = Dashboard.group_and_count_coupons()
    group_and_count_users = Dashboard.group_and_count_users()
    group_and_count_payouts = Dashboard.group_and_count_payouts()

    return render_template('strategy/page/dashboard.html',
                           group_and_count_plans=group_and_count_plans,
                           group_and_count_coupons=group_and_count_coupons,
                           group_and_count_users=group_and_count_users,
                           group_and_count_payouts=group_and_count_payouts)


@strategy.route('/configuration/', methods=['GET','POST'])
def configuration():
    print "configuration:",request
    print "configuration:",request.form
    print "configuration:",request.form.get('csrf_token')
    print "configuration:",request.form.get('num-round')
    print "configuration:",request.form.get('max-depth')
    print "configuration:",request.form.get('eta')    

    # Pre-populate the email field if the user is signed in.
    form = XGBForm(obj=current_user)

    if form.validate_on_submit():
        # This prevents circular imports.
        from turboquant.blueprints.contact.tasks import deliver_contact_email

        deliver_contact_email.delay(request.form.get('num-round'),
                                    request.form.get('max-depth'))

        flash('Thanks, expect a response shortly.', 'success')
        return redirect(url_for('strategy.configuration'))

    return render_template('strategy/page/configuration.html', form=form)

@strategy.route('/widgets/')
def widgets():
    group_and_count_plans = Dashboard.group_and_count_plans()
    group_and_count_coupons = Dashboard.group_and_count_coupons()
    group_and_count_users = Dashboard.group_and_count_users()
    group_and_count_payouts = Dashboard.group_and_count_payouts()

    return render_template('strategy/page/widgets.html',
                           group_and_count_plans=group_and_count_plans,
                           group_and_count_coupons=group_and_count_coupons,
                           group_and_count_users=group_and_count_users,
                           group_and_count_payouts=group_and_count_payouts)
