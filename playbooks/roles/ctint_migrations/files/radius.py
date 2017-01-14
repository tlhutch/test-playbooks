###############################################################################
# RADIUS AUTHENTICATION SETTINGS
###############################################################################

# Ansible Tower can be configured to centrally use Radius as a source for
# authentication information.

# Radius server settings (skipped when RADIUS_SERVER is blank).
RADIUS_SERVER = '127.0.0.1'
RADIUS_PORT = 777
RADIUS_SECRET = 'fo0m4nchU'
