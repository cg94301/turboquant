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
from turboquant.blueprints.quant.models import Strategy, Ticker
from turboquant.extensions import db
from flask_wtf import Form

from werkzeug.utils import secure_filename
import boto3,json

quant = Blueprint('quant', __name__,
                  template_folder='templates', url_prefix='/quant')

ALLOWED_EXTENSIONS = set(['csv'])

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

S3_BUCKET = 'cgiam.sagemaker'

s3 = boto3.client("s3")
client = boto3.client('lambda')

def upload_file_to_s3(file, bucket_name, uid, acl="public-read"):

    try:
        s3.upload_fileobj(
            file,
            bucket_name,
            'u' + str(uid) + '/' + file.filename,
            ExtraArgs={
                "ACL": acl,
                "ContentType": file.content_type
            }
        )

    except Exception as e:
        print("Something Happend: ", e)
        return e

    return "{}".format(file.filename)

@quant.before_request
@login_required
def before_request():
    """ Protect all of the quant endpoints. """
    pass


# Dashboard -------------------------------------------------------------------
@quant.route('/dashboard/')
def dashboard():
    return render_template('quant/page/dashboard.html')


@quant.route('/data/', defaults={'page': 1}, methods=['GET','POST'])
@quant.route('/data/page/<int:page>', methods=['GET','POST'])
def data(page):

    print "*** debug", request
    print "*** debug", request.method
    print "*** debug", request.form.viewkeys()
    print "*** debug", request.form.keys()
    print "*** debug", 'upload' in request.form.keys()
    print "*** debug", 'update' in request.form.keys()
    
    # Use basic form for CSRF token
    form = Form()
    
    if request.method == 'POST':

        if 'upload' in request.form.keys():

            print "upload"
            print "user_file", request.files.getlist('user_file')
        
            for uf in request.files.getlist('user_file'):
                print "uf:",uf

                file = uf

                """
                These attributes are also available

                file.filename
                file.content_type
                file.content_length
                file.mimetype
                """

                #if file.filename == "":
                #    flash('Please select a file', 'danger')
                ##return "Please select a file"

                if file and allowed_file(file.filename):
                    file.filename = secure_filename(file.filename)
                    output = upload_file_to_s3(file, S3_BUCKET, str(current_user.id) + '/ticker')
                    #return str(output)

                else:
                    flash('File format not allowed: ' + file.filename, 'danger')


            #elif 'update' in request.form.keys():

            payload = json.dumps({"uid":current_user.id})
            print "*** debug payload:%s" % payload
            print "*** debug", type(payload)
            payloadb = str.encode(payload)
                    

            response = client.invoke(
                FunctionName='arn:aws:lambda:us-west-2:188444798703:function:list_s3',
                Payload=payloadb,
            )

            tickercloud = response['Payload'].read()
            print "***debug respone:", tickercloud
            print "***debug type:", type(tickercloud)
            tickercloudd = json.loads(tickercloud)
            print "*** debug", type(tickercloudd)
            #print "*** debug", type(tickercloudd[0])
            #print "*** debug", tickercloudd[0]
                    
            #return redirect("quant/page/data.html")
            
            
            # Ticker.query.delete()

            tickercloud_names = [s[0] for s in tickercloudd]
            print "tickercloud_names", tickercloud_names

            tickerdb = Ticker.query.filter(Ticker.user_id == current_user.id)
            tickerdb_names = [s.tid for s in tickerdb.all()]
            print "tickerdb_names", tickerdb_names

            # tickercloud: [["AAPL", 233285, "2018-09-08T16:53:24+00:00"], ["ORCL", 197427, "2018-09-08T18:15:59+00:00"], ["SBUX", 226567, "2018-09-08T15:11:44+00:00"]]
            for tic in tickercloudd:
                print "debug: updating ", tic[0]

                # are there any tickers in DB that were removed from cloud?
                if tic[0] in tickerdb_names:
                    tickerdb_names.remove(tic[0])

                x = tickerdb.filter(Ticker.tid==tic[0]).first()
                print "x",x
                if x:
                    #x.tid = tic[0]
                    x.size = tic[1]
                    x.lastmodified = tic[2]
                else:
                    t = Ticker(user_id=current_user.id, tid=tic[0], skip=False, size=tic[1], lastmodified=tic[2])
                    db.session.add(t)

                #db.session.add(Ticker(user_id=current_user.id, tid=tid,size=size,lastmodified=lastmodified))

            print "tickerdb_names minus cloud:", tickerdb_names

            for tic in tickerdb_names:
                x = tickerdb.filter(Ticker.tid==tic).first()
                db.session.delete(x)

            db.session.commit()


                
                    
    paginated_tickers = Ticker.query \
                              .filter(Ticker.user_id == current_user.id) \
                              .order_by(Ticker.tid.asc()) \
                              .paginate(page, 20, True) 
            
    return render_template('quant/page/data.html', tickers=paginated_tickers, form=form)


@quant.route('/generate/', methods=['GET','POST'])
def generate():
    print "configuration:",request
    print "configuration:",request.form
    print "configuration:",request.form.get('csrf_token')
    print "current_user:",current_user.id
    # Pre-populate the email field if the user is signed in.
    #form = XGBForm(obj=current_user)
    form = XGBForm()

    
    if form.validate_on_submit():
        # This prevents circular imports.
        from turboquant.blueprints.quant.tasks import launch_batch_job

        # launch_xgb_job(request.form.get('num-round'),
        #task = launch_sfn_job.delay(current_user.id,
        #                            'AAPL',
        #                            request.form.get('num-round-from'),
        #                            request.form.get('max-depth-from'),
        #                            request.form.get('eta-from'))

        num_round_from = request.form.get('num-round-from')
        num_round_to = request.form.get('num-round-to')
        num_round_step = request.form.get('num-round-step')
        max_depth_from = request.form.get('max-depth-from')
        max_depth_to = request.form.get('max-depth-to')
        eta_from = request.form.get('eta-from')
        eta_to = request.form.get('eta-to')    

        params = {"num_round_from": num_round_from, "num_round_to": num_round_to, "num_round_step": num_round_step,
                  "max_depth_from": max_depth_from, "max_depth_to": max_depth_to,
                  "eta_from": eta_from, "eta_to": eta_to}        

        # do combinatorics here. take ticker from DB not cloud. the launch sfn with list of jobs.
        # move preprocess into data step.
        
        payload = json.dumps({"uid":current_user.id, "params":params})
        print "*** debug payload:%s" % payload
        print "*** debug", type(payload)
        payloadb = str.encode(payload)        
        
        task = launch_batch_job.delay(current_user.id, params)
        
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

    uid = current_user.id
    
    if request.method == 'POST':
        
        
        #if form.validate_on_submit():
        #from turboquant.blueprints.quant.tasks import describe_jobs

        # don't use delay. synchronous response.
        # when used w/o .delay the AWS credentials are not found.
        # delay scheduled from docker machine celery which has .aws
        # synchronous scheduled from docker machine webiste which has no .aws
        #response = describe_jobs.delay(current_user.id)

        # Get all strategy jobids
        strategies = Strategy.query.filter(Strategy.user_id == uid)

        jobids = [job.name for job in strategies]
        print "*** debug jobids:", jobids
        payload = json.dumps({"jobs":jobids})
        print "*** debug payload:%s" % payload
        print "*** debug", type(payload)
        payloadb = str.encode(payload)

        #client = boto3.client('lambda', region_name='us-west-2')
        #client = boto3.client('lambda')
        response = client.invoke(
            FunctionName='arn:aws:lambda:us-west-2:188444798703:function:describe_execution',
            Payload=payloadb,
        )

        stats = response['Payload'].read()
        print "***debug respone:", stats
        print "***debug type:", type(stats)
        statsd = json.loads(stats)

        for stat in statsd:
        
            jobid_out = stat['jobid']
            print "***jobid:", jobid_out
            status_out = stat['status']
            print "***debug status:", status_out

            # find if exists and update.
            q = Strategy.query.filter_by(name=jobid_out).first()
            q.status = status_out
        
            # outpuf from SFN is json encoded string
            if 'output' in stat:
                outputd = json.loads(stat['output'])
                print outputd
                print type(outputd)
                outputd = outputd['train']
                auc_out = outputd['stats']['auc']
                print "***debug:", auc_out
                q.auc = auc_out

                precision_out = outputd['stats']['precision']
                recall_out = outputd['stats']['recall']
                q.precision = precision_out
                q.recall = recall_out

                sharpe_out = outputd['fin']['sharpe']
                q.sharpe = sharpe_out
                #q = db.session.query().\
                    #   filter(Strategy.name == jobid_out).\
                    #   update({"status": status_out})
                #db.session.commit()
                #    #return redirect(url_for('quant.strategies'))



            db.session.commit()
    

    
    paginated_strategies = Strategy.query \
        .filter(Strategy.user_id == current_user.id) \
        .order_by(Strategy.created_on.desc()) \
        .paginate(page, 20, True)

    return render_template('quant/page/strategies.html', strategies=paginated_strategies, form=form)
