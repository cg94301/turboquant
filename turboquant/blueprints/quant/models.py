from sqlalchemy import func, or_

#from turboquant.blueprints.user.models import User
from turboquant.blueprints.billing.models.subscription import Subscription
from turboquant.blueprints.bet.models.bet import Bet

import datetime

from lib.util_datetime import timedelta_months
from lib.util_sqlalchemy import ResourceMixin
from turboquant.extensions import db

class Strategy(ResourceMixin, db.Model):
    __tablename__ = 'strategies'
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id',
                                                  onupdate='CASCADE',
                                                  ondelete='CASCADE'),
                        index=True, nullable=False)
    portfolio = db.Column(db.Boolean,default=False)
    name = db.Column(db.String(128))
    ticker = db.Column(db.String(128))
    execution_arn = db.Column(db.String(128))
    status = db.Column(db.String(32))
    auc = db.Column(db.Float(32))
    precision = db.Column(db.Float(32))
    recall = db.Column(db.Float(32))
    sharpe = db.Column(db.Float(32))

    def __init__(self, **kwargs):
        # CAll Flask-SQLAlchemy's constructor.
        super(Strategy, self).__init__(**kwargs)

    @classmethod
    def search(cls, query=''):
        """
        Search a resource by 1 or more fields.

        :param query: Search query
        :type query: str
        :return: SQLAlchemy filter
        """
        # replace with default in function signature
        #if not query:
        #    return ''

        search_query = '%{0}%'.format(query)
        search_chain = (Strategy.name.ilike(search_query),
                        Strategy.status.ilike(search_query),
                        Strategy.ticker.ilike(search_query))

        return or_(*search_chain)
    
        
class Ticker(ResourceMixin, db.Model):
    __tablename__ = 'tickers'
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id',
                                                  onupdate='CASCADE',
                                                  ondelete='CASCADE'),
                        index=True, nullable=False)
    
    tid = db.Column(db.String(128))
    size = db.Column(db.Integer())
    lastmodified = db.Column(db.String(128))
    skip = db.Column(db.Boolean)

    def __init__(self, **kwargs):
        # CAll Flask-SQLAlchemy's constructor.
        super(Ticker, self).__init__(**kwargs)

    @classmethod
    def search(cls, query=''):
        """
        Search a resource by 1 or more fields.

        :param query: Search query
        :type query: str
        :return: SQLAlchemy filter
        """

        # replace with default in function signature
        #if not query:
        #    return ''

        search_query = '%{0}%'.format(query)
        search_chain = (Ticker.tid.ilike(search_query))

        return or_(search_chain)

class Portfolio(ResourceMixin, db.Model):
    __tablename__ = 'portfolios'
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id',
                                                  onupdate='CASCADE',
                                                  ondelete='CASCADE'),
                        index=True, nullable=False)
    
    sharpe = db.Column(db.Float(32))
    sortino = db.Column(db.Float(32))
    mar = db.Column(db.Float(32))
    returnYearly = db.Column(db.Float(32))
    volaYearly = db.Column(db.Float(32))
    maxDD = db.Column(db.Float(32))
    maxDDBegin = db.Column(db.Integer())
    maxDDEnd = db.Column(db.Integer())
    maxTimeOffPeak = db.Column(db.Integer())
    maxTimeOffPeakBegin = db.Column(db.Integer())
    maxTimeOffPeakEnd = db.Column(db.Integer())
    
    def __init__(self, **kwargs):
        # CAll Flask-SQLAlchemy's constructor.
        super(Portfolio, self).__init__(**kwargs)    
    
#class Dashboard(object):
#    @classmethod
#    def group_and_count_users(cls):
#        """
#        Perform a group by/count on all users.
#
#        :return: dict
#        """
#        return Dashboard._group_and_count(User, User.role)
#
#    @classmethod
#    def group_and_count_plans(cls):
#        """
#        Perform a group by/count on all subscriber types.
#
#        :return: dict
#        """
#        return Dashboard._group_and_count(Subscription, Subscription.plan)
#
#    @classmethod
#    def group_and_count_coupons(cls):
#        """
#        Obtain coupon usage statistics across all subscribers.
#
#        :return: tuple
#        """
#        not_null = db.session.query(Subscription).filter(
#            Subscription.coupon.isnot(None)).count()
#        total = db.session.query(func.count(Subscription.id)).scalar()
#
#        if total == 0:
#            percent = 0
#        else:
#            percent = round((not_null / float(total)) * 100, 1)
#
#        return not_null, total, percent
#
#    @classmethod
#    def group_and_count_payouts(cls):
#        """
#        Perform a group by/count on all payouts.
#
#        :return: dict
#        """
#        return Dashboard._group_and_count(Bet, Bet.payout)
#
#    @classmethod
#    def _group_and_count(cls, model, field):
#        """
#        Group results for a specific model and field.
#
#        :param model: Name of the model
#        :type model: SQLAlchemy model
#        :param field: Name of the field to group on
#        :type field: SQLAlchemy field
#        :return: dict
#        """
#        count = func.count(field)
#        query = db.session.query(count, field).group_by(field).all()
#
#        results = {
#            'query': query,
#            'total': model.query.count()
#        }
#
#        return results
