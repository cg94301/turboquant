from sqlalchemy import func

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
