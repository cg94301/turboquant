from turboquant.app import create_celery_app
import boto3
import json
#from random import randint
import random
from turboquant.blueprints.quant.models import Strategy, Ticker
from sqlalchemy import and_
import itertools
import random

celery = create_celery_app()

def get_jobid(uid,len):
    code = ''.join(random.choice('0123456789abcdefghijklmnopqrstuvwxyz') for i in range(len))
    # Drop the user ID as part of job name?
    # Maybe good to enable for debug. 
    #jobid = str(uid) + '-' + str(code)
    jobid = str(code)    
    return jobid

@celery.task()
def launch_xgb_job(id, num_round, max_depth, eta):
    """
    Send a contact e-mail.

    :param email: E-mail address of the visitor
    :type user_id: str
    :param message: E-mail message
    :type user_id: str
    :return: None
    """
    print "id:",id
    print "num_round:",num_round
    print "max_depth:",max_depth
    print "eta:",eta

    client = boto3.client('lambda')
    params = {'id':id, 'num_round':num_round, 'max_depth':max_depth, 'eta':eta}
    payload = json.dumps(params)
    payloadb = str.encode(payload)

    # InvocationType 'Event' -> asynchronous
    # InvocationType 'DryRun' -> test w/o actually calling the function
    response = client.invoke(
        FunctionName='arn:aws:lambda:us-west-2:188444798703:function:create_training_job',
        InvocationType='DryRun',
        LogType='None',
        Payload=payloadb,
    )

    print "response:",response


    
    return {}

@celery.task()
def launch_backtest(uid):

    client = boto3.client('lambda')
    
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

    rs = response['Payload']
    print "stats:",rs
    
@celery.task()
def launch_batch_job(uid,params):

    # ML params
    # raw parameter ranges
    print "params:",params

    # Run ML for all tickers that are not skipped
    # Note: Get tickers live when task actually executes in queue.
    tickersq = Ticker.query.filter(and_(Ticker.user_id == uid, Ticker.skip == False)).all()
    tickers = [t.tid for t in tickersq]
    print "task tickers:", tickers

    # Step 1:
    # PREPROCESS CSV
    # do preprocessing for all tickers here

    client = boto3.client('lambda')
    payload = {"uid": uid, "seed":"", "tickers":tickers}
    payloads = json.dumps(payload)
    payloadb = str.encode(payloads)

    # InvocationType 'Event' -> asynchronous
    # InvocationType 'DryRun' -> test w/o actually calling the function
    response = client.invoke(
        FunctionName='arn:aws:lambda:us-west-2:188444798703:function:preproc2',
        Payload=payloadb,
    )

    # seed can be reused for debug purposes
    rs = response['Payload']
    rseed = rs.read()
    print "rseed:", rseed

    # Step 2:
    # Create all permuatations from provided ranges
    
    num_round_from = int(params['num_round_from'])
    num_round_to = int(params['num_round_to'])
    num_round_step = int(params['num_round_step'])
    max_depth_from = int(params['max_depth_from'])
    max_depth_to = int(params['max_depth_to'])
    eta_from = float(params['eta_from'])
    eta_to = float(params['eta_to'])
    print type(num_round_from)

    num_round = [num_round_from, num_round_to]
    num_round_max = max(num_round)
    num_round_min = min(num_round)
    num_round_range = range(num_round_min, num_round_max+1, num_round_step)
    print num_round_range
    
    max_depth = [max_depth_from, max_depth_to]
    max_depth_max = max(max_depth)
    max_depth_min = min(max_depth)
    max_depth_range = range(max_depth_min, max_depth_max+1, 1)
    print max_depth_range


    # translate from float to exponent
    eta_lookup = {1:0,0.1:-1,0.01:-2,0.001:-3}
    eta = [eta_from, eta_to]
    eta_max = max(eta)
    eta_min = min(eta)
    #print "max",eta_max
    #print "min",eta_min
    #print eta_lookup[eta_max]
    #print eta_lookup[eta_min]

    eta_range =[ 10** exponent for exponent in range(eta_lookup[eta_min], eta_lookup[eta_max]+1)]
    print eta_range
    
    ticker_range = tickers
    print ticker_range

    comb = list(itertools.product(ticker_range,num_round_range,max_depth_range,eta_range))
    print "You have configured %s strategies:" % len(comb)
    print comb


    #jobid = get_jobid(uid,10)
    #print "jobid:", jobid
    #print (jobid,) + comb[0]

    # Give every job an identifier.
    comb_id = [ (get_jobid(uid,10),) + job for job in comb ]
    print "Running the following jobs:"
    print comb_id

    # This is how jobs look like. List of tuples.
    # [('1-zgmyrhbh', u'CVX', 400, 1, 0.1), ('1-1tdntl4m', u'CVX', 400, 2, 0.1), ('1-g8zaebpf', u'CVX', 400, 3, 0.1), ('1-j06euwhm', u'AAPL', 400, 1, 0.1), ('1-v5qm5xv6', u'AAPL', 400, 2, 0.1), ('1-3oudkvz9', u'AAPL', 400, 3, 0.1)]

    # Launch job in cloud.
    # Call SFN to do batch processing.
    # tqml7 is batch processor. Calls tqml8 for individual runs.

    # {"uid":1,"jobs":[('1-zgmyrhbh', u'CVX', 400, 1, 0.1), ('1-1tdntl4m', u'CVX', 400, 2, 0.1)],"batch_size":1, "active":[], "all_done": False, "any_done": False }

    wait_time = 20
    batch_size = 2
    # Since we dont' track the user ID in job name anymore,
    # why use specific SFN ID? REQUIRED. BREAKS IF generic ID is used.
    sfnid = get_jobid(uid,12)
    
    client = boto3.client('stepfunctions')
    params = {"batch": {"uid": uid, "jobs":comb_id, "batch_size":batch_size, "active":[], "all_done": False, "any_done": False, "wait_time": wait_time, "seed": rseed}}
    payload = json.dumps(params)
    payloadb = str.encode(payload)

    try:
        response = client.start_execution(
            stateMachineArn='arn:aws:states:us-west-2:188444798703:stateMachine:tqbatch',
            input=payloadb,
            name=sfnid
        )

        print "launched tqbatch:", response['executionArn']
        # write to DB. pending jobs.
        # this does not use session. instead uses class method.
        jobs = []

        for job in comb_id:
            s = Strategy()
            s.user_id = uid
            s.name = job[0]
            s.ticker = job[1]
            ##s.startdate = response['startDate']
            #s.execution_arn = response['executionArn']
            s.status = 'PENDING'
            s.save()        
            
            # bulk save needs Session?
            #s = Session()
            #jobs = [ Strategy(user_id=uid, name=job[0], ticker=job[1], status='PENDING') for job in comb_id]               
            #s.bulk_save_objects(jobs)
            #s.commit()
            
            # launched w/ delay. no return value.
    except:
        print "Launch failed!"
    
    return None

@celery.task()
def launch_sfn_job(id, ticker, num_round, max_depth, eta):
    """
    Send a contact e-mail.

    :param email: E-mail address of the visitor
    :type user_id: str
    :param message: E-mail message
    :type user_id: str
    :return: None
    """
    print "id:",id
    print "num_round:",num_round
    print "max_depth:",max_depth
    print "eta:",eta


    #seed = randint(0, 4294967295)
    #code = ''.join(random.choice('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz') for i in range(8))
    #code = ''.join(random.choice('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ') for i in range(8))
    code = ''.join(random.choice('0123456789abcdefghijklmnopqrstuvwxyz') for i in range(8))
    name = str(id) + '-' + str(code)
    
    print "name:",name

    seed = None
    wait_time = 20
    print "seed:",seed
    
    client = boto3.client('stepfunctions')
    params = {'uid': id, 'id':name, 'ticker':ticker, 'num_round': num_round,'max_depth': max_depth, 'eta': eta, 'wait_time': wait_time, 'seed': seed}
    payload = json.dumps(params)
    payloadb = str.encode(payload)

    # TODO: call combine. get list of jobs so they can enter DB. Then call new SFN with that list.
    
    # InvocationType 'Event' -> asynchronous
    # InvocationType 'DryRun' -> test w/o actually calling the function
    response = client.start_execution(
        stateMachineArn='arn:aws:states:us-west-2:188444798703:stateMachine:tqml6',
        input=payloadb,
        name=name
    )

    print "response:",response

    # this is the response from CLI invocation

    # {
    #   "startDate": 1533187380.5, 
    #   "executionArn": "arn:aws:states:us-west-2:188444798703:execution:tqml5:ef689b71-ef5a-4e9f-9bbd-183a055ba761"
    # }

    # In this case ARN would be: arn:aws:states:us-west-2:188444798703:execution:tqml5:1-2157837237
    
    # looks like this launch is non-blocking.
    s = Strategy()
    s.user_id = id
    s.name = name
    s.ticker = ticker
    #s.startdate = response['startDate']
    s.execution_arn = response['executionArn']
    s.status = 'PENDING'
    s.save()
    
    return None

@celery.task()
def describe_jobs(id):

    # Get all strategy arns
    strategies_arn = Strategy.query\
           .filter(Strategy.user_id == id)

    arns = [arn.execution_arn for arn in strategies_arn]
    print "*** debug", arns
    payload = json.dumps(arns)
    print "*** debug:%s" % payload
    print "*** debug", type(payload)
    payloadb = str.encode(payload)

    # why is region not found from .aws ??
    client = boto3.client('lambda', region_name='us-west-2')
    #client = boto3.client('lambda')
    response = client.invoke(
        FunctionName='arn:aws:lambda:us-west-2:188444798703:function:describe_execution',
        Payload=payloadb,
    )

    print "*** debug", response    
