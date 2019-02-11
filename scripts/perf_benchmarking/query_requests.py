from datetime import timedelta
import logging
import sys

from towerkit import api

from .benchmarking import delete_all_created, no_op, write_results  # noqa


logging.basicConfig(level='DEBUG')
log = logging.getLogger()
handler = logging.StreamHandler(sys.stdout)
handler.setLevel('DEBUG')
log.addHandler(handler)

v1 = api.ApiV1().load_default_authtoken().get()


endpoints = (('organization', v1.organizations),
             ('user', v1.users),
             ('team', v1.teams),
             ('credential', v1.credentials),
             ('inventory', v1.inventory),
             ('host', v1.hosts),
             ('group', v1.groups),
             ('project', v1.projects),
             ('job template', v1.job_templates),
             ('job', v1.jobs))

# getting tens of thousands of items over is unnecessary.
item_limit = 2000

job_times = []  # (job_url, job.elapsed)
job_event_times = []  # (job_event_url, job_event.last_elapsed)

job_event_job_count = 0
for resource, endpoint in endpoints:
    loop = True
    page = 1
    item_count = 0
    while loop:
        big_get = endpoint.get(page=page, page_size=200)
        loop = big_get.next
        if loop:
            page = int(loop.split('=')[1].split('&')[0])
        write_results(big_get.last_elapsed, operation='Querying 200 created {0}s'.format(resource),
                      user='admin', endpoint=big_get.endpoint, method='get')
        results = big_get.results
        for result in results:
            if item_count > item_limit:
                loop = False
                break
            item_count += 1
            result.get()
            write_results(result.last_elapsed, operation='Getting {0}'.format(resource),
                          user='admin', endpoint=str(result.endpoint), method='get')
            if resource == 'job':
                job_times.append((result.endpoint, timedelta(seconds=result.elapsed)))
                if job_event_job_count <= item_limit:
                    job_events_endpoint = result.related.job_events
                    while True:
                        events = job_events_endpoint.get()
                        for event in events.results:
                            event.get()
                            job_event_times.append((event.endpoint, event.last_elapsed))
                            job_event_job_count += 1
                            if job_event_job_count > item_limit:
                                break
                        if not events.next or job_event_job_count > item_limit:
                            break
                        job_events_endpoint = events.next

for job_event_url, elapsed in job_event_times:
    write_results(elapsed, operation='Getting job event',
                  user='admin', endpoint=job_event_url, method='get')

for job_url, job_time in job_times:
    write_results(job_time, operation='Run job',
                  user='admin', endpoint=job_url, method='na')
