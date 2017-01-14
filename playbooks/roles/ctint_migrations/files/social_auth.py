###############################################################################
# SOCIAL AUTHENTICATION SETTINGS
###############################################################################

# Ansible Tower can be configured to centrally use OAuth2 or SAML as a source
# for authentication information.

# Google OAuth2
# -------------

# Create a project at https://console.developers.google.com/ and obtain an
# OAuth2 key and secret for a web application.  Provide the following callback
# URL for your application, replacing tower.example.com with the FQDN to your
# Tower server:
#
# https://foo.com/sso/complete/google-oauth2/
#
# Ensure that the Google+ API is enabled.

SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = '260504019230-4c9ihqupnkc6fpnhcf2gan0qaskrk65a.apps.googleusercontent.com'
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = 'kXG6bTcJxSW217YncQJdaBSK'

# Uncomment the line below to restrict the domains who are allowed to login
# using Google OAuth2.

SOCIAL_AUTH_GOOGLE_OAUTH2_WHITELISTED_DOMAINS = ['example.com']

# Uncomment the line below when only allowing a single domain to authenticate
# using Google OAuth2; Google will not display any other accounts if the user
# is logged in with multiple Google accounts.

SOCIAL_AUTH_GOOGLE_OAUTH2_AUTH_EXTRA_ARGUMENTS = {'hd': 'example.com'}

# Refer to Python Social Auth documentation for advanced settings:
#
#     https://python-social-auth.readthedocs.org/en/latest/backends/google.html#google-oauth2

# Github OAuth2
# -------------

# Create a developer application at https://github.com/settings/developers and
# obtain an OAuth2 key (Client ID) and secret (Client Secret).  Provide the
# following callback URL for your application, replacing tower.example.com
# with the FQDN to your Tower server:
#
# https://foo.com/sso/complete/github/

SOCIAL_AUTH_GITHUB_KEY = '4ce06b336274e59db27e'
SOCIAL_AUTH_GITHUB_SECRET = 'b282bd79ec460be55343f3ab5eb2949de6820036'

# Create an organization-owned application at
# https://github.com/organizations/<yourorg>/settings/applications and obtain
# an OAuth2 key (Client ID) and secret (Client Secret).  Provide the
# following callback URL for your application, replacing tower.example.com
# with the FQDN to your Tower server:
#
# https://foo.com/sso/complete/github-org/

SOCIAL_AUTH_GITHUB_ORG_KEY = '4ce06b336274e59db27e'
SOCIAL_AUTH_GITHUB_ORG_SECRET = 'b282bd79ec460be55343f3ab5eb2949de6820036'
SOCIAL_AUTH_GITHUB_ORG_NAME = 'ansible-test'

# Create an organization-owned application at
# https://github.com/organizations/<yourorg>/settings/applications and obtain
# an OAuth2 key (Client ID) and secret (Client Secret).  Provide the
# following callback URL for your application, replacing tower.example.com
# with the FQDN to your Tower server:
#
# https://foo.com/sso/complete/github-team/
#
# Find the numeric team ID using the Github API:
#
#     http://fabian-kostadinov.github.io/2015/01/16/how-to-find-a-github-team-id/

SOCIAL_AUTH_GITHUB_TEAM_KEY = '4ce06b336274e59db27e'
SOCIAL_AUTH_GITHUB_TEAM_SECRET = 'b282bd79ec460be55343f3ab5eb2949de6820036'
SOCIAL_AUTH_GITHUB_TEAM_ID = '1824663'

# Refer to Python Social Auth documentation for advanced settings:
#
#     https://python-social-auth.readthedocs.org/en/latest/backends/github.html
#

# SAML Service Provider
# ---------------------

# Set to a URL for a domain name you own (does not need to be a valid URL;
# only used as a unique ID).

SOCIAL_AUTH_SAML_SP_ENTITY_ID = 'https://ec2-54-226-127-168.compute-1.amazonaws.com'

# Create a keypair for Tower to use as a service provider (SP) and include the
# certificate and private key contents here.

SOCIAL_AUTH_SAML_SP_PUBLIC_CERT = '''
-----BEGIN CERTIFICATE-----
MIIDhTCCAm2gAwIBAgIJAOmNmsPuoqz6MA0GCSqGSIb3DQEBCwUAMFgxCzAJBgNV
BAYTAlVTMQswCQYDVQQIDAJOQzEQMA4GA1UEBwwHUmFsZWlnaDEQMA4GA1UECgwH
QW5zaWJsZTEYMBYGA1UEAwwPd3d3LmFuc2libGUuY29tMCAXDTE3MDExMzA3MTEw
NVoYDzIyOTAxMDI4MDcxMTA1WjBYMQswCQYDVQQGEwJVUzELMAkGA1UECAwCTkMx
EDAOBgNVBAcMB1JhbGVpZ2gxEDAOBgNVBAoMB0Fuc2libGUxGDAWBgNVBAMMD3d3
dy5hbnNpYmxlLmNvbTCCASIwDQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEBAOTZ
rFka/55q7+jfxxAouon0iMgHEqlaTzcF25X+4vJbbSDY6F/+ecGvrFcegrXp8srM
m61SwGvnC1SEUxOue+zqbUCZMqWB9lQi9WuliXD6Ya9BoxJ/CMgVy2IQz8gHopHs
E4PJVsNq7POp++ozmN55m+sTL4RXbm9PNQq1tpPj/787q2+j1bq/h1v6mCghXVHZ
gkJnr7nn/SyLS/ve9KjQO7voqTSurKtFSkaBrcY4RONLULZqj1Biih0WTD4WCfYj
7+nLT+7iEnUyeIovPxXRYCZ7FJWr0dl96T/WGkhEdWUS0qgyFweRgWk11ZIudqTA
Awym/qz6ONO9fTPS2dkCAwEAAaNQME4wHQYDVR0OBBYEFEXjZ5rLiFKV9u3Y0QpS
S8dQQUwWMB8GA1UdIwQYMBaAFEXjZ5rLiFKV9u3Y0QpSS8dQQUwWMAwGA1UdEwQF
MAMBAf8wDQYJKoZIhvcNAQELBQADggEBANfM1vVwo25ueBcguU4kPjUDPaiLqUIo
m0g7Pp745+x5b+fIq+psiVMXCDpWsbHHXa3LdtwWLJ+HI3AW9OC+/J/pZuFV29wA
dfTmIMUKovPN5cM6e+YO9qornZNCvNI3prFn0KmEpmKi25fDgsbAKRFUfwKdG9Nj
KtaXYU27ZG/zFDyYryjT34gCLttbqUvCqHg0I++31LMFKTtYRkyZU/zJ0eIKFbI5
ylcKMIN89Emg3RFvJQ/uDjy97LaUK4e51Doh2Em1dzYKBDXfmOjOCE/I/oCqVQfw
aYmn+79MuLkLdWjMegSb/719FY9YRe9IvrthHH/bx5wcai8G3CZsTX8=
-----END CERTIFICATE-----
'''
SOCIAL_AUTH_SAML_SP_PRIVATE_KEY = '''
-----BEGIN PRIVATE KEY-----
MIIEvwIBADANBgkqhkiG9w0BAQEFAASCBKkwggSlAgEAAoIBAQDk2axZGv+eau/o
38cQKLqJ9IjIBxKpWk83BduV/uLyW20g2Ohf/nnBr6xXHoK16fLKzJutUsBr5wtU
hFMTrnvs6m1AmTKlgfZUIvVrpYlw+mGvQaMSfwjIFctiEM/IB6KR7BODyVbDauzz
qfvqM5jeeZvrEy+EV25vTzUKtbaT4/+/O6tvo9W6v4db+pgoIV1R2YJCZ6+55/0s
i0v73vSo0Du76Kk0rqyrRUpGga3GOETjS1C2ao9QYoodFkw+Fgn2I+/py0/u4hJ1
MniKLz8V0WAmexSVq9HZfek/1hpIRHVlEtKoMhcHkYFpNdWSLnakwAMMpv6s+jjT
vX0z0tnZAgMBAAECggEBAJK9vNSaCkRjX5hcPUFwTER/Z2GTn3S2MsseV3IzsQQk
ebIxQ7eh7iKy6XgnWTsaWxOM5VnbEQVfbhVwj/Cz1kTRAOMGGMKltfS3QdUXnSyz
cAW3ub/3cwMRbotgKkuiEa0tykmbxaWin3OSkLTZBvHI2qB+ed6LTYXULTfD0uG6
f07fcCR176TSoAlpsAFZpIHsjd1jgrZWXqqThe+Dj1BPleyopHZcYcnaEo+ssgq8
r+OKtOKWLQX71ThYltfoMpmQuvw0a4JxetCZ+pVw2prjGzmXskR8OMZEXvkbs1Qk
8hp6vy+sgS+XsiztC689e9TlD/dFeGmcxR35G8YfarECgYEA+RXNV0UfuSlIdKpq
2k3LTy8zJjN1UrHaiF/8Rw6Sz0b5gwMrdCux+V1p5lUHvg6sUIr9D8ZaUfYRqT98
Lpq7g35MRzDKx64xVFeb/TUy5pJY6eXbCV4xxBj5c8rU8AtI7/HTcZHwXKfYP6DY
JLIJUZUxmWAy0LiDzoQFvm+KWO0CgYEA6zQQ4P/RQ9BQSvbaOxiXaPZQBsWoq0ba
fcqBKcOy7G4F7rA0/EPAI9BlJnDjCq1WnCatazOanp15U856G5aUIh+vOtfqf+Os
V7wNN8hL8sfGU/NmCy3WHno3So4RkVzldHUQWg93Vm35LLNuz8Dw/Ed+J4N4j79r
VGTwyQMMAx0CgYEAjto0JALeyMCmb1J1abIIEefN+/CzLrQV0vTJqK7w/7OC0eJ1
f3C3533tiE3n3NZpeN/ddriZgDwRsPFZ9RiExkse0A1pns+GNwrvyW5DPP1dxPcw
gdTl0cNI/WGscebm88XLMG00Xs9cNFG45IK+2W0pPv9u5UmNPll1OdyaiZkCgYAc
uasmD5g7NAHaZfOZLBOx2gNEEHfdEzY0DrtfomsDvRw0XojaFlwtA5KW80qHT0w4
nfCoGxFTNeBPf/Qh0m4dDMmV4jDdlazCulDS8z9zUzrBngRkcSCpcDu4e0lh+3p6
kqGAnkrw31WDRBbQgLvt071wjfn3dGVjVUCjDCA3cQKBgQC16jdSSY9loWEiNFsR
5d5DaV123UHM9C2PTOc+5jv6T3xX53Ah2TWyfn1+IcGSU4DTZv61+wvLXNh4k89r
6PzeBmvcOtVYV9tF+fwsZTQhtlUNCP8CsX75k7KeLxaoIwbkzMn4KtRcnvAeKvsV
gTCGnzE5GXF2/NPa2zqPf1sdpg==
-----END PRIVATE KEY-----
'''

# Configure the following settings with information about your app and contact
# information.

SOCIAL_AUTH_SAML_ORG_INFO = {
    'en-US': {
        'name': 'example',
        'displayname': 'Example',
        'url': 'http://www.example.com',
    },
}
SOCIAL_AUTH_SAML_TECHNICAL_CONTACT = {
    'givenName': 'Some User',
    'emailAddress': 'suser@example.com',
}
SOCIAL_AUTH_SAML_SUPPORT_CONTACT = {
    'givenName': 'Some User',
    'emailAddress': 'suser@example.com',
}

# Configure the entity ID, SSO URL and certificate for each identity provider
# (IdP) in use.  Multiple SAML IdPs are supported.

# Some IdPs may provide user data using attribute names that differ from the
# default OIDs (https://github.com/omab/python-social-auth/blob/master/social/backends/saml.py#L16).
# Attribute names may be overridden for each IdP as shown below.

SOCIAL_AUTH_SAML_ENABLED_IDPS = {
    #'myidp': {
    #    'entity_id': 'https://idp.example.com',
    #    'url': 'https://myidp.example.com/sso',
    #    'x509cert': '',
    #},
    'onelogin': {
        'entity_id': 'https://app.onelogin.com/saml/metadata/605388',
        'url': 'https://ansible.onelogin.com/trust/saml2/http-post/sso/605388',
        'x509cert': '''
MIIEJjCCAw6gAwIBAgIUfuSD54OPSBhndDHh3gZorvrIaoAwDQYJKoZIhvcNAQEF
BQAwXTELMAkGA1UEBhMCVVMxFjAUBgNVBAoMDUFuc2libGUsIEluYy4xFTATBgNV
BAsMDE9uZUxvZ2luIElkUDEfMB0GA1UEAwwWT25lTG9naW4gQWNjb3VudCA2NDEy
NzAeFw0xNTA1MTIxNTU2NTBaFw0yMDA1MTMxNTU2NTBaMF0xCzAJBgNVBAYTAlVT
MRYwFAYDVQQKDA1BbnNpYmxlLCBJbmMuMRUwEwYDVQQLDAxPbmVMb2dpbiBJZFAx
HzAdBgNVBAMMFk9uZUxvZ2luIEFjY291bnQgNjQxMjcwggEiMA0GCSqGSIb3DQEB
AQUAA4IBDwAwggEKAoIBAQC2YfKbJZSssbtotYrOD35OLIqQBIrxVK7G7tRno5pg
h1ZLJSCitqCuauEi4xYCV9Rd2RisJN0gwqg5VqBeRgtwQIDe4pNljxAkSS/UChl6
mMnA0OT46iBWD2fiTIx2W82BrCSN+f3oNvJcigbp3IdS1Njr23HCS9K6zQ7Oby2F
TbIEoKW0I+8V7dRPLyEtNoyf7GUQvf4sLGTbK3Bh1QBK4wFGMjOcigLu1OE8+F+o
emVMTVTlky3veSGbqX8IPReVtqqYx2e55pdAs1Fo75M2OqOZArSlzQBaK+1WP5gr
z1VQMywc+S+kma5ES3xetw94kLoTbknyt23BKeUVqCrtAgMBAAGjgd0wgdowDAYD
VR0TAQH/BAIwADAdBgNVHQ4EFgQUG6dSxZkCptzLshpJU3222h57ra4wgZoGA1Ud
IwSBkjCBj4AUG6dSxZkCptzLshpJU3222h57ra6hYaRfMF0xCzAJBgNVBAYTAlVT
MRYwFAYDVQQKDA1BbnNpYmxlLCBJbmMuMRUwEwYDVQQLDAxPbmVMb2dpbiBJZFAx
HzAdBgNVBAMMFk9uZUxvZ2luIEFjY291bnQgNjQxMjeCFH7kg+eDj0gYZ3Qx4d4G
aK76yGqAMA4GA1UdDwEB/wQEAwIHgDANBgkqhkiG9w0BAQUFAAOCAQEAGGN/SgN7
pbwquue4HhoFx2ssMTZUfdswlB6rdq81gc03Jxum38B+WrUpNcJgQtkg7N++0/q6
zXlfSROPBnLYq1pmwcMvZ+puySgRrtxNpavvUZjdfEkYrXxmEXdnwlxitsL1Lmry
vM/lPxBxWYzrR4Cz51f44bKvTnYUa0lEi73K+4H/nb5F+P+GD4F4Fv4267eLMbj8
83j7Zw3iEVMOtF7O7coS+fwVym5KuBafzCzfiYdbAK9ceCb80TP2M9As03B9rhCi
Qeqc9lAtMmx1L1umCyBkX8aA1OLZ1gnFt0jYGmpWzXMUECrPWfuADB750lJuR5Tf
+0Kk+xrlgUe7zA==
''',
        'attr_user_permanent_id': 'name_id',
        'attr_first_name': 'User.FirstName',
        'attr_last_name': 'User.LastName',
        'attr_username': 'User.email',
        'attr_email': 'User.email',
    },
}

# Once configuration is complete, you will need to register your SP with each
# IdP.  Provide the entity ID and the following callback URL for your
# application, replacing tower.example.com with the FQDN to your Tower server:
#
#     https://tower.example.com/sso/complete/saml/
#
# If your IdP allows uploading an XML metadata file, you can download one from
# your Tower installation customized with the settings above:
#
#     https://tower.example.com/sso/metadata/saml/

# Organiztion and Team Mapping
# ----------------------------

# Mapping to organization admins/users from social auth accounts. This setting
# controls which users are placed into which Tower organizations based on
# their username and email address.  Dictionary keys are organization names.
# organizations will be created if not present if the license allows for
# multiple organizations, otherwise the single default organization is used
# regardless of the key.  Values are dictionaries defining the options for
# each organization's membership.  For each organization it is possible to
# specify which users are automatically users of the organization and also
# which users can administer the organization.
#
# - admins: None, True/False, string or list/tuple of strings.
#   If None, organization admins will not be updated.
#   If True, all users using social auth will automatically be added as admins
#   of the organization.
#   If False, no social auth users will be automatically added as admins of
#   the organiation.
#   If a string or list of strings, specifies the usernames and emails for
#   users who will be added to the organization.  Compiled regular expressions
#   may also be used instead of string literals.
# - remove_admins: True/False. Defaults to False.
#   If True, a user who does not match will be removed from the organization's
#   administrative list.
# - users: None, True/False, string or list/tuple of strings. Same rules apply
#   as for admins.
# - remove_users: True/False. Defaults to False. Same rules as apply for remove_admins

SOCIAL_AUTH_ORGANIZATION_MAP = {
    # Add all users to the default organization.
    'Default': {
        'users': True,
    },
}

# Organization mappings may be specified separately for each social auth
# backend.  If defined, these configurations will take precedence over the
# global configuration above.

SOCIAL_AUTH_GOOGLE_OAUTH2_ORGANIZATION_MAP = {"Default": {"admins": True}}
SOCIAL_AUTH_GITHUB_ORGANIZATION_MAP = {"Default": {"admins": True}}
SOCIAL_AUTH_GITHUB_ORG_ORGANIZATION_MAP = {"Default": {"admins": True}}
SOCIAL_AUTH_GITHUB_TEAM_ORGANIZATION_MAP = {"Default": {"admins": True}}
SOCIAL_AUTH_SAML_ORGANIZATION_MAP = {"Default": {"admins": True}}

# Mapping of team members (users) from social auth accounts. Keys are team
# names (will be created if not present). Values are dictionaries of options
# for each team's membership, where each can contain the following parameters:
# - organization: string. The name of the organization to which the team
#   belongs.  The team will be created if the combination of organization and
#   team name does not exist.  The organization will first be created if it
#   does not exist.  If the license does not allow for multiple organizations,
#   the team will always be assigned to the single default organization.
# - users: None, True/False, string or list/tuple of strings.
#   If None, team members will not be updated.
#   If True/False, all social auth users will be added/removed as team
#   members.
#   If a string or list of strings, specifies expressions used to match users.
#   User will be added as a team member if the username or email matches.
#   Compiled regular expressions may also be used instead of string literals.
# - remove: True/False. Defaults to False. If True, a user who does not match
#   the rules above will be removed from the team.

SOCIAL_AUTH_TEAM_MAP = {"teamA": {"organization": "orgA"}}

# Team mappings may be specified separately for each social auth backend.  If
# defined, these configurations will take precedence over the the global
# configuration above.

SOCIAL_AUTH_GOOGLE_OAUTH2_TEAM_MAP = {"teamA": {"organization": "orgA"}}
SOCIAL_AUTH_GITHUB_TEAM_MAP = {"teamA": {"organization": "orgA"}}
SOCIAL_AUTH_GITHUB_ORG_TEAM_MAP = {"teamA": {"organization": "orgA"}}
SOCIAL_AUTH_GITHUB_TEAM_TEAM_MAP = {"teamA": {"organization": "orgA"}}
SOCIAL_AUTH_SAML_TEAM_MAP = {"teamA": {"organization": "orgA"}}

# Uncomment the line below (i.e. set SOCIAL_AUTH_USER_FIELDS to an empty list)
# to prevent new user accounts from being created.  Only users who have
# previously logged in using social auth or have a user account with a matching
# email address will be able to login.

SOCIAL_AUTH_USER_FIELDS = ["foo"]

# It is also possible to add custom functions to the social auth pipeline for
# more advanced organization and team mapping.  Use at your own risk.

#def custom_social_auth_pipeline_function(backend, details, user=None, *args, **kwargs):
#    print 'custom:', backend, details, user, args, kwargs

#SOCIAL_AUTH_PIPELINE += (
#    'awx.settings.production.custom_social_auth_pipeline_function',
#)
