import logging
import urllib3

logging.basicConfig(format="%(asctime)s [%(process)d][%(name)-4s:%(lineno)-2d][%(levelname)-4s] %(message)s")

logging.getLogger('factory').setLevel('WARN')
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
