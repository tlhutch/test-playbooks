import os
import hashlib
import time
import tempfile
import json
from datetime import datetime, timedelta


def generate_license_file(**kwargs):
    meta = generate_license(**kwargs)

    (fd, fname) = tempfile.mkstemp(suffix='.json')
    os.write(fd, json.dumps(meta))
    os.close(fd)

    return fname


def generate_aws_file(**kwargs):
    meta = generate_aws(**kwargs)

    (fd, fname) = tempfile.mkstemp(suffix='.json')
    os.write(fd, json.dumps(meta))
    os.close(fd)

    return fname


def generate_license(instance_count=20, contact_email="art@vandelay.com",
                     company_name="Vandelay Industries", contact_name="Art Vandelay",
                     license_date=None, days=None, trial=None, eula_accepted=True):

    def to_seconds(itime):
        '''
        Convenience method to convert a time into seconds
        '''
        return int(float(time.mktime(itime.timetuple())))

    # TODO: default to random UTF-8 fields for company_name, company_email and
    # contact_email
    # Generate license key (see ansible-commander/private/license_writer.py)
    meta = dict(instance_count=instance_count,
                contact_email=contact_email,
                company_name=company_name,
                contact_name="Art Vandelay")

    # Be sure to accept the eula
    meta['eula_accepted'] = eula_accepted

    # Only generate a trial license if requested
    if isinstance(trial, bool):
        meta['trial'] = trial

    # Determine license_date
    if days is not None:
        meta['license_date'] = to_seconds(datetime.now() + timedelta(days=days))
    elif license_date is not None:
        meta['license_date'] = license_date

    sha = hashlib.sha256()
    sha.update("ansibleworks.license.000")
    sha.update(meta['company_name'].encode('utf-8'))
    sha.update(str(meta['instance_count']))
    sha.update(str(meta['license_date']))

    # Only generate a trial license if requested
    if meta.get('trial', False):
        sha.update(str(meta['trial']))

    meta['license_key'] = sha.hexdigest()
    return meta


def generate_aws(instance_count=30, ami_id="ami-eb81b182", instance_id="i-fd64c1d3"):
    # Generate license key (see ansible-commander/private/license_writer.py)
    meta = dict(instance_count=instance_count)

    sha = hashlib.sha256()
    sha.update("ansibleworks.license.000")
    sha.update(str(meta['instance_count']))
    sha.update(str(ami_id))
    sha.update(str(instance_id))
    meta['license_key'] = sha.hexdigest()

    return meta
