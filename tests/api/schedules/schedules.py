from dateutil.relativedelta import relativedelta
from datetime import datetime
from dateutil import rrule

from towerkit.rrule import RRule
import pytest

from tests.api import APITest


@pytest.mark.usefixtures('authtoken')
class SchedulesTest(APITest):

    @pytest.fixture(ids=('minutely', 'hourly', 'daily', 'weekly', 'monthly', 'yearly'),
                    params=[('MINUTELY', 'minutes'), ('HOURLY', 'hours'), ('DAILY', 'days'), ('WEEKLY', 'weeks'),
                            ('MONTHLY', 'months'), ('YEARLY', 'years')])
    def immediate_rrule(self, request):
        """Creates an RRule with the next recurrence targeted for 30 seconds from invocation"""
        frequency, kwarg = request.param
        dtstart = datetime.utcnow() + relativedelta(**{kwarg: -1, 'seconds': 30})
        freq = getattr(rrule, frequency)
        return RRule(freq, dtstart=dtstart)

    def minutely_rrule(self, **kwargs):
        return RRule(rrule.MINUTELY, dtstart=datetime.utcnow() + relativedelta(minutes=-1, seconds=+30), **kwargs)

    def strftime(self, dt):
        return dt.strftime('%Y-%m-%dT%H:%M:%SZ')
