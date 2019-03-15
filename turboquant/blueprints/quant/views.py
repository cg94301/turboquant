from flask import (
    Blueprint,
    redirect,
    request,
    flash,
    url_for,
    render_template,
    send_file,
    jsonify)
from flask_login import login_required, current_user
from sqlalchemy import text,and_

from turboquant.blueprints.quant.forms import XGBForm, BulkDeleteForm, SearchForm
from turboquant.blueprints.quant.models import Strategy, Ticker, Portfolio
from turboquant.extensions import db
from flask_wtf import Form

from werkzeug.utils import secure_filename
import boto3,json,csv,sys,os

quant = Blueprint('quant', __name__,
                  template_folder='templates', url_prefix='/quant')

ALLOWED_EXTENSIONS = set(['csv'])

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

S3_BUCKET = 'cgiam.sagemaker'

s3 = boto3.client("s3")
client = boto3.client('lambda')
sfn = boto3.client('stepfunctions')

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


@quant.route('/data/', defaults={'page': 1}, methods=['GET'])
@quant.route('/data/page/<int:page>', methods=['GET'])
def data(page):

    print "*** debug", request
    print "*** debug", request.method
    print "*** debug", request.form.viewkeys()
    print "*** debug", request.form.keys()
    print "*** debug", 'upload' in request.form.keys()
    print "*** debug", 'update' in request.form.keys()
    
    # Use basic form for CSRF token
    form = Form()
    search_form = SearchForm()  
    bulk_form = BulkDeleteForm()

    sort_by = Ticker.sort_by(request.args.get('sort', 'created_on'),
                           request.args.get('direction', 'desc'))
    
    order_values = '{0} {1}'.format(sort_by[0], sort_by[1])
                    
    paginated_tickers = Ticker.query \
                              .filter(Ticker.user_id == current_user.id) \
                              .filter(Ticker.search(text(request.args.get('q', '')))) \
                              .order_by(text(order_values)) \
                              .paginate(page, 2, True) 
            
    return render_template('quant/page/data.html', tickers=paginated_tickers, form=form, bulk_form=bulk_form)


@quant.route('/quant/upload', methods=['POST'])
def tickers_upload():
    # Use basic form for CSRF token
    form = Form()
    
    
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
        
    return redirect(url_for('quant.data'))

@quant.route('/quant/bulk_delete', methods=['POST'])
def tickers_bulk_delete():
    
    form = BulkDeleteForm()

    if form.validate_on_submit():

        if request.form.get('scope') == 'all_items':
            
            ids = Ticker.query.with_entities(Ticker.tid).filter(Ticker.user_id == current_user.id).all()
            # SQLAlchemy returns back a list of tuples, we want a list of strs.
            ids = [str(item[0]) for item in ids] 

        else:
            ids = request.form.getlist('bulk_ids')        
        
        if 'skip' in request.form:
            print "Skip IDS:", ids
            
            tickersq = Ticker.query.filter(Ticker.user_id == current_user.id)
            for id in ids:
                x = tickersq.filter(Ticker.tid==id).first()
                if request.form.get('scope') == 'all_items':
                    x.skip = False
                else:
                    x.skip = not x.skip
                print "x",x
            db.session.commit()

        if 'delete' in request.form:
            print "Deleting IDS:", ids        

        flash('{0} ticker(s) were scheduled to be deleted.'.format(len(ids)),
              'success')
    else:
        flash('No tickers were deleted, something went wrong.', 'error')

    return redirect(url_for('quant.data'))


@quant.route('/quant/bulk_strategies', methods=['POST'])
def strategies_bulk_delete():
    
    form = BulkDeleteForm()

    if form.validate_on_submit():
        #ids = Strategy.get_bulk_action_ids_quant(current_user.id,
        #                                         request.form.get('scope'),
        #                                         request.form.getlist('bulk_ids'),
        #                                         'name')

        ## Prevent circular imports.
        #from turboquant.blueprints.billing.tasks import delete_users
        ## sqlalchemy bulk delete
        #delete_users.delay(ids)
        
        if request.form.get('scope') == 'all_items':
            
            ids = Strategy.query.with_entities(Strategy.name).filter(Strategy.user_id == current_user.id).all()
            # SQLAlchemy returns back a list of tuples, we want a list of strs.
            ids = [str(item[0]) for item in ids] 

        else:
            ids = request.form.getlist('bulk_ids')

        if 'portfolio' in request.form:
            print "Portfolio IDS:", ids
            
            strategiesq = Strategy.query.filter(Strategy.user_id == current_user.id)
            for id in ids:
                x = strategiesq.filter(Strategy.name==id).first()
                if request.form.get('scope') == 'all_items':
                    x.portfolio = False
                else:
                    x.portfolio = not x.portfolio
                print "x",x
            db.session.commit()

        if 'delete' in request.form:
            print "Deleting IDS:", ids

        flash('{0} strategies were scheduled to be deleted.'.format(len(ids)),
              'success')
    else:
        flash('No strategies were deleted, something went wrong.', 'error')

    return redirect(url_for('quant.strategies'))

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
            
    search_form = SearchForm()    
    bulk_form = BulkDeleteForm()

    print "request:",request.args.keys()
    
    sort_by = Strategy.sort_by(request.args.get('sort', 'created_on'),
                           request.args.get('direction', 'desc'))
    
    order_values = '{0} {1}'.format(sort_by[0], sort_by[1])
    
    paginated_strategies = Strategy.query \
        .filter(Strategy.user_id == current_user.id) \
        .filter(Strategy.search(text(request.args.get('q', '')))) \
        .order_by(text(order_values)) \
        .paginate(page, 10, True)

    return render_template('quant/page/strategies.html', strategies=paginated_strategies, form=form, bulk_form=bulk_form)


@quant.route('/portfolio/', methods=['GET','POST'])
def portfolio():

    form = Form()
    uid = current_user.id

    compile_busy = False
    
    if request.method == 'POST':

        if 'retrieve' in request.form:
            print "retrieve"

            try:
                # Download equity curve file from S3.
                s3.download_file(S3_BUCKET, 'u' + str(uid) + '/data/turboquant.py', '/tmp/turboquant.' + str(uid) + '.py')   
            except:
                print "not ready"
                compile_busy = True
                #flash('Compile not ready. Try again a bit later.')
                print "Oops! ",sys.exc_info()
                #return redirect(url_for('quant.portfolio'))


            print "debug. retrieve continues."
            
            try:
                return send_file('/tmp/turboquant.1.py', as_attachment=True, attachment_filename='turboquant.py')
            except:
                print "Oops! ",sys.exc_info()            


        if 'compile' in request.form:

            # Delete Strategy first from AWS.
            try:
                response = s3.delete_object(Bucket=S3_BUCKET, Key='u' + str(uid) + '/data/turboquant.py')
                print "delete response:", response
            except:
                print "Strategy delete error: " , sys.exc_info()

            # Delete Strategy from local.
            try:
                os.remove('/tmp/turboquant.' + str(uid) + '.py')
            except:
                print "Strategy local remove error: " , sys.exc_info()        
        
            print "Compiling portfolio:"

            # { "data": {
            #     "uid": 1,
            #     "jobs": [["1-3zr381lryj","SBUX"],["1-89suhahgfk","ORCL"],["1-c0xd1m5j6n","CVX"],["1-dtq58uj5im","AAPL"]],
            #     "portfolio": [["1-3zr381lryj","SBUX"],["1-89suhahgfk","ORCL"],["1-c0xd1m5j6n","CVX"],["1-dtq58uj5im","AAPL"]],
            #     "batch_size": 2,
            #     "active": [],
            #     "all_done": false,
            #     "any_done": false,
            #     "wait_time": 10,
            #     "target": "py"
            # }
            # }
            
            # portfolio strategies: [(u'AAPL', u'fwezr2w2si'), (u'CVX', u'1-c0xd1m5j6n')]
            
            # Is it better to encapsulate as task? Or start directly from here?
    
            selectedq = Strategy.query.filter(and_(Strategy.user_id == uid, Strategy.portfolio == True)).all()
            
            selected = [(t.name,t.ticker) for t in selectedq]
            print "portfolio strategies:", selected
    

            #jobs = [("1-3zr381lryj","SBUX"),("1-89suhahgfk","ORCL"),("1-c0xd1m5j6n","CVX"),("1-dtq58uj5im","AAPL")]
            jobs = selected
            portfolio = jobs
    
            params = {"data": {"uid": uid, "jobs": jobs, "portfolio": portfolio, "batch_size": 2, "active":[], "all_done": False, "any_done": False, "wait_time": 10, "target": "py"}}
            payload = json.dumps(params)
            payloadb = str.encode(payload)
    
            response = sfn.start_execution(
                stateMachineArn='arn:aws:states:us-west-2:188444798703:stateMachine:tqmake',
                input=payloadb
                #name=sfnid
            )

            print "tqmake: ", response            

            
        if 'backtest' in request.form:
            print "backtest"

            from turboquant.blueprints.quant.tasks import launch_backtest

            # Launch backtest.
            # {
            #   "uid":204, "portfolio": {"SBUX":"204-0uvd0q69wq","AAPL":"204-ywliaf9tp0"}
            # }
            #task = launch_backtest(current_user.id)            

            selectedq = Strategy.query.filter(and_(Strategy.user_id == uid, Strategy.portfolio == True)).all()

            selected = [(t.ticker,t.name) for t in selectedq]
            #print "portfolio strategies:", selected

            params = {"uid":uid, "portfolio":dict(selected)}

            print "params:",params
            payload = json.dumps(params)
            payloadb = str.encode(payload)

            response = client.invoke(
                FunctionName='arn:aws:lambda:us-west-2:188444798703:function:portfolio',
                Payload=payloadb,
            )

            stats = response['Payload'].read()
            statsd = json.loads(stats)
            print type(statsd)
            print "stats:", statsd
            find = statsd['fin']
            
            # Update Portfolio DB with stats if entry exists.
            # Otherwise create new entry.
            portfolio = Portfolio.query.filter(Portfolio.user_id == current_user.id).first()
            print "portfolio post db:", portfolio
            if portfolio:
                portfolio.sharpe = find['sharpe']
                portfolio.sortino = find['sortino']
                portfolio.mar = find['mar']
                portfolio.returnYearly = find['returnYearly']
                portfolio.volaYearly = find['volaYearly']
                portfolio.maxDD = find['maxDD']
                portfolio.maxDDBegin = find['maxDDBegin']
                portfolio.maxDDEnd = find['maxDDEnd']
                portfolio.maxTimeOffPeak = find['maxTimeOffPeak']
                portfolio.maxTimeOffPeakBegin = find['maxTimeOffPeakBegin']
                portfolio.maxTimeOffPeakEnd = find['maxTimeOffPeakEnd']
            else:
                p = Portfolio(user_id=current_user.id,
                              sharpe=find['sharpe'],
                              sortino=find['sortino'],
                              mar=find['mar'],
                              returnYearly=find['returnYearly'],
                              volaYearly=find['volaYearly'],
                              maxDD=find['maxDD'],
                              maxDDBegin=find['maxDDBegin'],
                              maxDDEnd=find['maxDDEnd'],
                              maxTimeOffPeak=find['maxTimeOffPeak'],
                              maxTimeOffPeakBegin=find['maxTimeOffPeakBegin'],
                              maxTimeOffPeakEnd=find['maxTimeOffPeakEnd'])
                db.session.add(p)

            db.session.commit()
            
            
    # Query portfolio
    portfolio = Portfolio.query.filter(Portfolio.user_id == current_user.id).first()
    print type(portfolio)
    print "portfolio db:", portfolio
                    
    return render_template('quant/page/portfolio.html', form=form, portfolio=portfolio, compile_busy=compile_busy)


@quant.route('/portfolio/data', methods=['GET'])
def portfolio_data():
    # Read CSV equity file into list of dict.
    equity=[]
    uid = current_user.id

    # Download equity curve file from S3.
    s3.download_file(S3_BUCKET, 'u' + str(uid) + '/data/equity.csv', '/tmp/equity.' + str(uid) + '.csv')    
    
    with open('/tmp/equity.' + str(uid) + '.csv') as csvfile:
        reader = csv.DictReader(csvfile)
        #print type(reader)
        #print reader
        for row in reader:
            #print(row['date'], row['equity'])
            equity.append({"date":row['date'], "equity":row['equity']})
            
            #print "equity:", equity

    return jsonify({"equity":equity})


@quant.route('/portfolio/compile', methods=['GET'])
def compile():

    uid = current_user.id

    # Delete Strategy first from AWS.
    try:
        response = s3.delete_object(Bucket=S3_BUCKET, Key='u' + str(uid) + '/data/turboquant.py')
        print "delete response:", response
    except:
        print "Strategy delete error: " , sys.exc_info()

    # Delete Strategy from local.
    try:
        os.remove('/tmp/turboquant.' + str(uid) + '.py')
    except:
        print "Strategy local remove error: " , sys.exc_info()        
        
    print "Compiling portfolio:"

    # { "data": {
    #     "uid": 1,
    #     "jobs": [["1-3zr381lryj","SBUX"],["1-89suhahgfk","ORCL"],["1-c0xd1m5j6n","CVX"],["1-dtq58uj5im","AAPL"]],
    #     "portfolio": [["1-3zr381lryj","SBUX"],["1-89suhahgfk","ORCL"],["1-c0xd1m5j6n","CVX"],["1-dtq58uj5im","AAPL"]],
    #     "batch_size": 2,
    #     "active": [],
    #     "all_done": false,
    #     "any_done": false,
    #     "wait_time": 10,
    #     "target": "py"
    # }
    # }

    # portfolio strategies: [(u'AAPL', u'fwezr2w2si'), (u'CVX', u'1-c0xd1m5j6n')]

    # Is it better to encapsulate as task? Or start directly from here?
    
    selectedq = Strategy.query.filter(and_(Strategy.user_id == uid, Strategy.portfolio == True)).all()

    selected = [(t.name,t.ticker) for t in selectedq]
    print "portfolio strategies:", selected
    

    #jobs = [("1-3zr381lryj","SBUX"),("1-89suhahgfk","ORCL"),("1-c0xd1m5j6n","CVX"),("1-dtq58uj5im","AAPL")]
    jobs = selected
    portfolio = jobs
    
    params = {"data": {"uid": uid, "jobs": jobs, "portfolio": portfolio, "batch_size": 2, "active":[], "all_done": False, "any_done": False, "wait_time": 10, "target": "py"}}
    payload = json.dumps(params)
    payloadb = str.encode(payload)
    
    response = sfn.start_execution(
        stateMachineArn='arn:aws:states:us-west-2:188444798703:stateMachine:tqmake',
        input=payloadb
        #name=sfnid
    )

    print "tqmake: ", response
    
    return redirect(url_for('quant.portfolio'))


@quant.route('/portfolio/retrieve', methods=['GET'])
def retrieve():


    print "Retrieving Strategy:"

    uid = current_user.id


    try:
        # Download equity curve file from S3.
        s3.download_file(S3_BUCKET, 'u' + str(uid) + '/data/turboquant.py', '/tmp/turboquant.' + str(uid) + '.py')   
    except:
        print "not ready"
        flash('Compile not ready. Try again a bit later.')
        print "Oops! ",sys.exc_info()
        #return redirect(url_for('quant.portfolio'))

    
    try:
        return send_file('/tmp/turboquant.1.py')
    except:
        print "Oops! ",sys.exc_info()
        
    #return redirect(url_for('quant.portfolio'))
