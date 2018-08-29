from turboquant.app import create_celery_app
import boto3
import json
#from random import randint
import random
from turboquant.blueprints.quant.models import Strategy

celery = create_celery_app()


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
    params = {'id':name, 'ticker':ticker, 'num_round': num_round,'max_depth': max_depth, 'eta': eta, 'wait_time': wait_time, 'seed': seed}
    payload = json.dumps(params)
    payloadb = str.encode(payload)

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
