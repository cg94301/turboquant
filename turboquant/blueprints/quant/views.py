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
from turboquant.extensions import db
from flask_wtf import Form

import boto3,json

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
                                    'SBUX',
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

@quant.route('/strategies/', defaults={'page': 1}, methods=['GET','POST'])
@quant.route('/strategies/page/<int:page>', methods=['GET','POST'])
def strategies(page):

    print "*** debug", request.method
    print "*** debug", request.form

    # Use basic form for CSRF token
    form = Form()
    
    if request.method == 'POST':
        
        
        #if form.validate_on_submit():
        from turboquant.blueprints.quant.tasks import describe_jobs

        # don't use delay. synchronous response.
        # when used w/o .delay the AWS credentials are not found.
        # delay scheduled from docker machine celery which has .aws
        # synchronous scheduled from docker machine webiste which has no .aws
        #response = describe_jobs.delay(current_user.id)

        # Get all strategy arns
        strategies_arn = Strategy.query\
                                 .filter(Strategy.user_id == current_user.id)

        arns = [arn.execution_arn for arn in strategies_arn]
        print "*** debug arns:", arns
        payload = json.dumps({"executionArn":arns})
        print "*** debug payload:%s" % payload
        print "*** debug", type(payload)
        payloadb = str.encode(payload)

        #testarn = {"executionArn": ["arn:aws:states:us-west-2:188444798703:execution:tqml5:1-2qzl45i1"] }
        #testarnstr = json.dumps(testarn)
        #testarnstrb = str.encode(testarnstr)
        #print "*** debug:", type(testarnstr)
        #print "*** debug:", testarnstrb

        # why is region not found from .aws ??
        #client = boto3.client('lambda', region_name='us-west-2')
        client = boto3.client('lambda')
        response = client.invoke(
            FunctionName='arn:aws:lambda:us-west-2:188444798703:function:describe_execution',
            Payload=payloadb,
        )

        stats = response['Payload'].read()
        print "***debug respone:", stats
        print "***debug type:", type(stats)
        statsd = json.loads(stats)

        for stat in statsd:
        
            name_out = stat['name']
            print "***name:", name_out
            status_out = stat['status']
            print "***debug status:", status_out

            q = Strategy.query.filter_by(name=name_out).first()
            q.status = status_out
        
            # outpuf from SFN is json encoded string
            if 'output' in stat:
                outputd = json.loads(stat['output'])
                auc_out = outputd['statistics']['auc']
                print "***debug:", auc_out
                q.auc = auc_out

                precision_out = outputd['statistics']['precision']
                recall_out = outputd['statistics']['recall']
                q.precision = precision_out
                q.recall = recall_out
                #q = db.session.query().\
                    #   filter(Strategy.name == name_out).\
                    #   update({"status": status_out})
                #db.session.commit()
                #    #return redirect(url_for('quant.strategies'))



            db.session.commit()
    

    
    paginated_strategies = Strategy.query \
        .filter(Strategy.user_id == current_user.id) \
        .order_by(Strategy.created_on.desc()) \
        .paginate(page, 20, True)

    return render_template('quant/page/strategies.html', strategies=paginated_strategies, form=form)
