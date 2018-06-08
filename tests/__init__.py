import logging

logging.basicConfig(format="%(asctime)s [%(process)d][%(name)-4s:%(lineno)-2d][%(levelname)-4s] %(message)s")

logging.getLogger('factory').setLevel('WARN')
