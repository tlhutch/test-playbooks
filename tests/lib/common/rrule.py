import re
import dateutil.rrule

class RRule(dateutil.rrule.rrule):
    '''Sub-class rrule to support __str__'''

    FREQNAMES = ['YEARLY','MONTHLY','WEEKLY','DAILY','HOURLY','MINUTELY','SECONDLY']
    def __str__(self):
        parts = list()
        parts.append('FREQ=' + self.FREQNAMES[self._freq])
        if self._interval:
            parts.append('INTERVAL=' + str(self._interval))
        if self._wkst:
            parts.append('WKST=' + str(self._wkst))
        if self._count:
            parts.append('COUNT=' + str(self._count))

        for name, value in [
                ('BYSETPOS', self._bysetpos),
                ('BYMONTH', self._bymonth),
                ('BYMONTHDAY', self._bymonthday),
                ('BYYEARDAY', self._byyearday),
                ('BYWEEKNO', self._byweekno),
                ('BYWEEKDAY', self._byweekday),
                # ('BYWEEKDAY', (dateutil.rrule.weekdays[num] for num in self._byweekday)),
                ('BYHOUR', self._byhour),
                ('BYMINUTE', self._byminute),
                ('BYSECOND', self._bysecond),
                ]:
            if name == "BYWEEKDAY" and value:
                value = (dateutil.rrule.weekdays[num] for num in value)
            if value:
                parts.append(name + '=' + ','.join(str(v) for v in value))

        return '''DTSTART:%s RRULE:%s ''' % (re.sub(r'[:-]', '', self._dtstart.strftime("%Y%m%dT%H%M%SZ")), ';'.join(parts))
