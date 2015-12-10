import pytest
import fauxfactory
# from users import admin_user


@pytest.fixture(scope="function")
def credential_kind_choices(request, authtoken, api_credentials_pg):
    '''Return ssh credential'''
    return dict(api_credentials_pg.options().json['actions']['POST']['kind']['choices'])


@pytest.fixture(scope="function")
def ssh_credential(request, authtoken, api_credentials_pg, admin_user, testsetup):
    '''Create ssh credential'''
    payload = dict(name="credentials-%s" % fauxfactory.gen_utf8(),
                   description="machine credential - %s" % fauxfactory.gen_utf8(),
                   kind='ssh',
                   user=admin_user.id,
                   username=testsetup.credentials['ssh']['username'],
                   password=testsetup.credentials['ssh']['password'],)

    # TODO - support overriding the payload via a pytest marker
    fixture_args = getattr(request.function, 'ssh_credential', None)
    if fixture_args and 'kwargs' in fixture_args:
        payload.update(fixture_args.kwargs)

    obj = api_credentials_pg.post(payload)
    request.addfinalizer(obj.silent_delete)
    return obj


@pytest.fixture(scope="function")
def ssh_credential_ask(request, authtoken, api_credentials_pg, admin_user, testsetup):
    '''Create ssh credential with 'ASK' password'''
    payload = dict(name="credentials-%s" % fauxfactory.gen_utf8(),
                   description="machine credential with ASK password - %s" % fauxfactory.gen_utf8(),
                   kind='ssh',
                   user=admin_user.id,
                   username=testsetup.credentials['ssh']['username'],
                   password='ASK',)
    obj = api_credentials_pg.post(payload)
    request.addfinalizer(obj.delete)
    return obj


@pytest.fixture(scope="function")
def ssh_credential_with_ssh_key_data_and_sudo(request, ansible_facts, authtoken, api_credentials_pg, admin_user, testsetup):
    '''Create ssh credential with the following properties:
        * username: SUDO_USER
        * become_method: sudo
        * ssh_key_data: <str>
    '''
    SUDO_USER = ansible_facts.values()[0]['ansible_facts']['ansible_env']['SUDO_USER']

    payload = dict(name=fauxfactory.gen_utf8(),
                   description=fauxfactory.gen_utf8(),
                   kind='ssh',
                   user=admin_user.id,
                   username=SUDO_USER,
                   become_method="sudo",
                   ssh_key_data=testsetup.credentials['ssh']['ssh_key_data'])

    obj = api_credentials_pg.post(payload)
    request.addfinalizer(obj.delete)
    return obj


@pytest.fixture(scope="function", params=['sudo', 'su', 'pbrun'])
def ssh_credential_multi_ask(request, authtoken, api_credentials_pg, admin_user, testsetup):
    '''Create ssh credential with multiple 'ASK' passwords'''
    if request.param not in ('sudo', 'su', 'pbrun'):
        raise Exception("Unsupported parameter value: %s" % request.param)

    payload = dict(name="credentials-%s" % fauxfactory.gen_utf8(),
                   description="machine credential with mulit-ASK password - %s" % fauxfactory.gen_utf8(),
                   kind='ssh',
                   user=admin_user.id,
                   username=testsetup.credentials['ssh']['username'],
                   password='ASK',
                   ssh_key_data=testsetup.credentials['ssh']['encrypted']['ssh_key_data'],
                   ssh_key_unlock='ASK',
                   vault_password='ASK',
                   become_method=request.param,
                   become_username=testsetup.credentials['ssh']['become_username'],
                   become_password='ASK')
    obj = api_credentials_pg.post(payload)
    request.addfinalizer(obj.delete)
    return obj


@pytest.fixture(scope="function")
def team_ssh_credential(request, testsetup, authtoken, team_with_org_admin):
    '''Create team ssh credential'''
    payload = dict(name="credential-%s" % fauxfactory.gen_utf8(),
                   description="machine credential for team:%s" % team_with_org_admin.name,
                   kind='ssh',
                   team=team_with_org_admin.id,
                   username=testsetup.credentials['ssh']['username'],
                   password=testsetup.credentials['ssh']['password'],)
    obj = team_with_org_admin.get_related('credentials').post(payload)
    request.addfinalizer(obj.silent_delete)
    return obj


@pytest.fixture(scope="function")
def aws_credential(request, authtoken, api_credentials_pg, admin_user, testsetup):
    '''Create a randomly named Amazon Cloud credential'''
    payload = dict(name="awx-credential-%s" % fauxfactory.gen_utf8(),
                   description="AWS credential %s" % fauxfactory.gen_utf8(),
                   kind='aws',
                   user=admin_user.id,
                   username=testsetup.credentials['cloud']['aws']['username'],
                   password=testsetup.credentials['cloud']['aws']['password'],)
    obj = api_credentials_pg.post(payload)
    request.addfinalizer(obj.delete)
    return obj


@pytest.fixture(scope="function")
def rax_credential(request, authtoken, api_credentials_pg, admin_user, testsetup):
    '''Create a randomly named Rackspace Cloud credential'''
    payload = dict(name="rax-credential-%s" % fauxfactory.gen_utf8(),
                   description="Rackspace credential %s" % fauxfactory.gen_utf8(),
                   kind='rax',
                   user=admin_user.id,
                   username=testsetup.credentials['cloud']['rax']['username'],
                   password=testsetup.credentials['cloud']['rax']['password'],)
    obj = api_credentials_pg.post(payload)
    request.addfinalizer(obj.delete)
    return obj


@pytest.fixture(scope="function")
def azure_credential(request, authtoken, api_credentials_pg, admin_user, testsetup):
    '''Create a randomly named Azure Cloud credential'''
    payload = dict(name="azure-credential-%s" % fauxfactory.gen_utf8(),
                   description="Microsoft Azure credential %s" % fauxfactory.gen_utf8(),
                   kind='azure',
                   user=admin_user.id,
                   username=testsetup.credentials['cloud']['azure']['username'],
                   ssh_key_data=testsetup.credentials['cloud']['azure']['ssh_key_data'],)
    obj = api_credentials_pg.post(payload)
    request.addfinalizer(obj.delete)
    return obj


@pytest.fixture(scope="function")
def gce_credential(request, authtoken, api_credentials_pg, admin_user, testsetup):
    '''Create a randomly named Google Compute Engine credential'''
    payload = dict(name="gce-credential-%s" % fauxfactory.gen_utf8(),
                   description="Google Compute Engine credential %s" % fauxfactory.gen_utf8(),
                   kind='gce',
                   user=admin_user.id,
                   username=testsetup.credentials['cloud']['gce']['username'],
                   project=testsetup.credentials['cloud']['gce']['project'],
                   ssh_key_data=testsetup.credentials['cloud']['gce']['ssh_key_data'],)
    obj = api_credentials_pg.post(payload)
    request.addfinalizer(obj.delete)
    return obj


@pytest.fixture(scope="function")
def vmware_credential(request, authtoken, api_credentials_pg, admin_user, testsetup):
    '''Create a randomly named VMware vCenter credential'''
    payload = dict(name="vmware-credential-%s" % fauxfactory.gen_utf8(),
                   description="VMware vCenter credential %s" % fauxfactory.gen_utf8(),
                   kind='vmware',
                   user=admin_user.id,
                   host=testsetup.credentials['cloud']['vmware']['host'],
                   username=testsetup.credentials['cloud']['vmware']['username'],
                   password=testsetup.credentials['cloud']['vmware']['password'],)
    obj = api_credentials_pg.post(payload)
    request.addfinalizer(obj.delete)
    return obj


@pytest.fixture(scope="function")
def openstack_credential(request, authtoken, api_credentials_pg, admin_user, testsetup):
    '''Create a randomly named Openstack credential'''
    payload = dict(name="openstack-credential-%s" % fauxfactory.gen_utf8(),
                   description="Openstack credential %s" % fauxfactory.gen_utf8(),
                   kind='openstack',
                   user=admin_user.id,
                   host=testsetup.credentials['cloud']['openstack']['host'],
                   username=testsetup.credentials['cloud']['openstack']['username'],
                   password=testsetup.credentials['cloud']['openstack']['password'],
                   project=testsetup.credentials['cloud']['openstack']['project'])
    obj = api_credentials_pg.post(payload)
    request.addfinalizer(obj.delete)
    return obj


#
# Convenience fixture that iterates through supported cloud_credential types
#
@pytest.fixture(scope="function", params=['aws', 'rax', 'azure', 'gce', 'vmware', 'openstack'])
def cloud_credential(request):
    return request.getfuncargvalue(request.param + '_credential')


@pytest.fixture(scope="function")
def scm_credential_key_unlock_ASK(request, authtoken, api_credentials_pg, admin_user):
    '''Create scm credential with scm_key_unlock="ASK"'''
    payload = dict(name="credentials-%s" % fauxfactory.gen_utf8(),
                   description="SCM credential %s (scm_key_unlock:ASK)" % fauxfactory.gen_utf8(),
                   kind='scm',
                   username='git',
                   scm_key_unlock='ASK',
                   user=admin_user.id,)
    obj = api_credentials_pg.post(payload)
    request.addfinalizer(obj.delete)
    return obj


@pytest.fixture(scope="function")
def many_ssh_credentials(request, authtoken, testsetup, api_credentials_pg, admin_user):
    obj_list = list()
    for i in range(55):
        payload = dict(name="credential_%d_%s" % (i, fauxfactory.gen_utf8()),
                       description="machine credential - %d - %s" % (i, fauxfactory.gen_utf8()),
                       kind='ssh',
                       user=admin_user.id,
                       username=testsetup.credentials['ssh']['username'],
                       password=testsetup.credentials['ssh']['password'],)
        obj = api_credentials_pg.post(payload)
        request.addfinalizer(obj.delete)
        obj_list.append(obj)
    return obj_list


# The following ssh keys were generated by command line.
# Passphrases for all encrypted keys is "fo0m4nchU"

#
# Unencrypted RSA ssh key
#
@pytest.fixture(scope="function")
def unencrypted_rsa_ssh_credential(request, authtoken, api_credentials_pg, admin_user):
    '''Create rsa ssh_credential'''
    unencrypted_rsa_ssh_key_data = '''\
-----BEGIN RSA PRIVATE KEY-----
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
-----END RSA PRIVATE KEY-----
'''
    payload = dict(name="unencrypted rsa ssh_credentials-%s" % fauxfactory.gen_utf8(),
                   description="machine credential - %s" % fauxfactory.gen_utf8(),
                   kind='ssh',
                   user=admin_user.id,
                   username=fauxfactory.gen_alphanumeric(),
                   ssh_key_data=unencrypted_rsa_ssh_key_data)

    obj = api_credentials_pg.post(payload)
    request.addfinalizer(obj.silent_delete)
    return obj


#
# Encrypted RSA ssh key
#
@pytest.fixture(scope="function")
def encrypted_rsa_ssh_credential(request, authtoken, api_credentials_pg, admin_user):
    '''Create rsa ssh_credential'''
    encrypted_rsa_ssh_key_data = '''\
-----BEGIN RSA PRIVATE KEY-----
Proc-Type: 4,ENCRYPTED
DEK-Info: DES-EDE3-CBC,080794E763049C90

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
-----END RSA PRIVATE KEY-----
'''
    payload = dict(name="encrypted rsa ssh_credentials-%s" % fauxfactory.gen_utf8(),
                   description="machine credential - %s" % fauxfactory.gen_utf8(),
                   kind='ssh',
                   user=admin_user.id,
                   username=fauxfactory.gen_alphanumeric(),
                   ssh_key_data=encrypted_rsa_ssh_key_data,
                   ssh_key_unlock='ASK')

    obj = api_credentials_pg.post(payload)
    request.addfinalizer(obj.silent_delete)
    return obj


#
# Unencrypted DSA ssh key
#
@pytest.fixture(scope="function")
def unencrypted_dsa_ssh_credential(request, authtoken, api_credentials_pg, admin_user):
    '''Create dsa ssh_credential'''
    unencrypted_dsa_ssh_key_data = '''\
-----BEGIN DSA PRIVATE KEY-----
MIIBvAIBAAKBgQCrgdgWQ4UWPitmiRxjj5hu7bMk2CbJM8ituMN8jEguQjUqTqC6
J/hD0BxbnxLD2LKp1D5wSaACs2F41uAQkUF9YH4/jjCYHUgdISoAt6lApVWLbGZP
tQp6VExFK1JoLS5V3fX3Jn7sdN/ydmmuIf3KjY6tG3z/wp33wFxcfr2tBwIVAMBI
xnlo/hswogHI2zHPDEoBMpy/AoGAa7Cvdnf12BjWH2o64hiFcM0e3GlkbiFQ2UiJ
Zm6awpl8Q+4dpo328gwkz/NbtaiV33+3uqFdoDzNMgOMphwZrpK9+n6Nj7vdBz7Z
tj/5Jcnh0GYwQF/b+qBzgijYwXiXQ3oEDX/4b8MtBDgmrzcoe+YGyZTP6pDXnTeb
RkX/6/MCgYEAkQ3xIap50ZTa1PynAvH4pfiGmyEezLcTwB0HFVeNjFDTRT4LwQro
3EmqO3CN5/ebEkHyvOanORf+nL9QMM81Qgag0Dr6tIdVSkrTxXBKSKpber/uGQJm
tZeco9bzY5jkGMdyJYFxMwqo7oD6HLjSiqX15dv9L+2uPCUorB/yGeYCFQClPCNc
JEnKWO3VFPs3Lu9KeXjuTA==
-----END DSA PRIVATE KEY-----
'''
    payload = dict(name="unencrypted dsa ssh_credentials-%s" % fauxfactory.gen_utf8(),
                   description="machine credential - %s" % fauxfactory.gen_utf8(),
                   kind='ssh',
                   user=admin_user.id,
                   username=fauxfactory.gen_alphanumeric(),
                   ssh_key_data=unencrypted_dsa_ssh_key_data)

    obj = api_credentials_pg.post(payload)
    request.addfinalizer(obj.silent_delete)
    return obj


#
# Encrypted DSA ssh key
#
@pytest.fixture(scope="function")
def encrypted_dsa_ssh_credential(request, authtoken, api_credentials_pg, admin_user):
    '''Create dsa ssh_credential'''
    encrypted_dsa_ssh_key_data = '''\
-----BEGIN DSA PRIVATE KEY-----
Proc-Type: 4,ENCRYPTED
DEK-Info: DES-EDE3-CBC,14A3E16D2DF981E6

NWiAZVLu3oWLqBP9YpoN/eWTQAvbGEwSysZYa1ngOrkmDHfyzQF+kChX0siJ6okM
s5UiqBXTNL4OB2otZ1aKJ0Qss7YOgiX6yXc8I84Pct1xrcxREur8pyBTAG3zGDUm
pE7Rs/KwYwxjwpv+vqeuI3m9qTYCXEwg6emO1o8o1hNAramjCSRWFjXV+D0beK9y
9TYl3IgNxJyar3ybxwd6bAkSIECxUTcOTVzpI/IlerllrpDuaOSXCX1gUXBgvjaL
S24F1to9xoOyKIIL42nf3QjCoxm9lTB7xjxnxEGCMUdop4M/joUknHl5qSl0l3wL
fkfebmGALIv8WHbYK6OoF2y3vJ/fEibH99eIhvxcQqqTYGgjAM8eTfMdCLuOemX1
SCS10hG3/EYh+UAziZi1pLcXIizVNGV35T7zjExDl28Q70X974g/sooJN9CZdfMh
Xsiv+HA1U3b2Wc9Qo4nqLlmVj8/XfA940QCsdjcq238xVmIYmMwyNOtTjZTyPwRz
g5oFDkFOwH2sblxVr4d2FuWDquh4mfmqzP8f+Zqbn0IX2Ag5NXQbUAOoUJQdgkTf
/DBZByl0l5NIvQpeJN/Rng==
-----END DSA PRIVATE KEY-----
'''
    payload = dict(name="encrypted dsa ssh_credentials-%s" % fauxfactory.gen_utf8(),
                   description="machine credential - %s" % fauxfactory.gen_utf8(),
                   kind='ssh',
                   user=admin_user.id,
                   username=fauxfactory.gen_alphanumeric(),
                   ssh_key_data=encrypted_dsa_ssh_key_data,
                   ssh_key_unlock='ASK')

    obj = api_credentials_pg.post(payload)
    request.addfinalizer(obj.silent_delete)
    return obj


#
# Unencrypted ECDSA ssh key
#
@pytest.fixture(scope="function")
def unencrypted_ecdsa_ssh_credential(request, authtoken, api_credentials_pg, admin_user):
    '''Create ecdsa ssh_credential'''
    unencrypted_ecdsa_ssh_key_data = '''\
-----BEGIN EC PRIVATE KEY-----
MIHbAgEBBEHjAEGCdkDc3s0K+s5K7hN99+ShI2nTT2mc8DSvRSwuotPGdUQsmKzR
p0H4Nzgzi+lSLhKCmXvb8IoWB0AHve1f0qAHBgUrgQQAI6GBiQOBhgAEAO9jnMBX
27lBYPlPzQa5+R7qPgjPQiwzxC2WiMbX8BxfS6rgCPsLdbmg3BqkN70lq4mazNBK
27PMRuzlOcbYxmtQARWGnN9d+4n1C6r0KK7GWdV/RBqG+usaPrvONiNzMR0rHRtm
WHoOUmTyvtczIQd38pZ4wQQDiZSjHKC0q1SeZgbc
-----END EC PRIVATE KEY-----
'''
    payload = dict(name="unencrypted ecdsa ssh_credentials-%s" % fauxfactory.gen_utf8(),
                   description="machine credential - %s" % fauxfactory.gen_utf8(),
                   kind='ssh',
                   user=admin_user.id,
                   username=fauxfactory.gen_alphanumeric(),
                   ssh_key_data=unencrypted_ecdsa_ssh_key_data)

    obj = api_credentials_pg.post(payload)
    request.addfinalizer(obj.silent_delete)
    return obj


#
# Encrypted ECDSA ssh key
#
@pytest.fixture(scope="function")
def encrypted_ecdsa_ssh_credential(request, authtoken, api_credentials_pg, admin_user):
    '''Create ecdsa ssh_credential'''
    encrypted_ecdsa_ssh_key_data = '''\
-----BEGIN EC PRIVATE KEY-----
Proc-Type: 4,ENCRYPTED
DEK-Info: AES-128-CBC,D771731A0526AA4F33693467BC159DB9

+M8jVkn0LLHC1AdOLVdwhbWOASCmZLjyHgI+ipodTORJNcHNF8JDFVnkiMW88v9I
WOi0uDMsBIWtvomvkw9AgTyeF9IyLYjGvv9yRAsg4AvmzMEIgUg3kTywgGT8mAud
20oj0gZ3Z9un55iBYUnpCUj+EbiXe3SnZB+3RyRiY6lZjefGRBGcVFjb4lQfa24D
Rk6k2dyMLs3w4WSR0LW5q49d/qQeohZ20lmMuRCdK2W1lJJ34EHRIOOdTL83gXjr
DYLXEqBsy+KJmVmOp6A7410bm0NuJWSipqjaN/R6mwA=
-----END EC PRIVATE KEY-----
'''
    payload = dict(name="encrypted ecdsa ssh_credentials-%s" % fauxfactory.gen_utf8(),
                   description="machine credential - %s" % fauxfactory.gen_utf8(),
                   kind='ssh',
                   user=admin_user.id,
                   username=fauxfactory.gen_alphanumeric(),
                   ssh_key_data=encrypted_ecdsa_ssh_key_data,
                   ssh_key_unlock='ASK')

    obj = api_credentials_pg.post(payload)
    request.addfinalizer(obj.silent_delete)
    return obj


#
# Unencrypted open ssh key
#
@pytest.fixture(scope="function")
def unencrypted_open_ssh_credential(request, authtoken, api_credentials_pg, admin_user):
    '''Create open ssh_credential'''
    unencrypted_open_ssh_key_data = '''\
-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAABFwAAAAdzc2gtcn
NhAAAAAwEAAQAAAQEAsWPe6KPP0X8UU4Fp9BFv/yOWYjLrfAduwJsGOgWWQytDXamuZNNC
DrTYaZK/zkrMiQXhvoUdZnVb8AkL3HA0DodrCHZPzlkK2zZn1S2XOb0i8CGq+8pGTEw5Sw
icMJV3J12V9RRP2FdulULO9Ornxhe37usWw7NRFgY9LBuR5t4wnQOg5aNxRb6jfnfFKGgX
UD5KQjFR8oWNDtF2HMa9K3pKHlV75hG0ftZ5Zc5MFctegM2J3KOxYKPn37z/jAHnQ8z89M
Bj3tB8ZpuNP2dwGDFiQYrzgtIBqwQJZl1Qoe0k8zf9LhZfbRzQONmgHejxBUQOlCD57wfc
Y2hokd3+FwAAA9AML9G0DC/RtAAAAAdzc2gtcnNhAAABAQCxY97oo8/RfxRTgWn0EW//I5
ZiMut8B27AmwY6BZZDK0Ndqa5k00IOtNhpkr/OSsyJBeG+hR1mdVvwCQvccDQOh2sIdk/O
WQrbNmfVLZc5vSLwIar7ykZMTDlLCJwwlXcnXZX1FE/YV26VQs706ufGF7fu6xbDs1EWBj
0sG5Hm3jCdA6Dlo3FFvqN+d8UoaBdQPkpCMVHyhY0O0XYcxr0rekoeVXvmEbR+1nllzkwV
y16AzYnco7Fgo+ffvP+MAedDzPz0wGPe0Hxmm40/Z3AYMWJBivOC0gGrBAlmXVCh7STzN/
0uFl9tHNA42aAd6PEFRA6UIPnvB9xjaGiR3f4XAAAAAwEAAQAAAQAd13A7cLtYQemYdq/t
WDWgFUuKL4i/77wo+KtefWwe1ptZmV72JTf6o1+4uvA7cwffkTa9x0T/5IRX6B2vssx/GT
bfUI/yZbZW1Fs5WJcVJoVHIlLSUt/qm/QTdFpaLfrCi5LbjNQ1z9eRkpCgURg2kezma3QD
7hmY++m0jtrHnJdZ7q0SX6LzDdI0PFfdg+GqMIecbOGEGXhDwis4zQlQnJ2hPsmoMBILOm
zd6tq4+5HEDJEO02iIlpiZUGp5y7O9KhI0Qw2mdv3vT0JmnuJBUXFSgA0AwvCt5Amu6WLd
Vmnfen3BLxM+KmtzZu4TXC5cQMG5N0YC+mzL6859k1n5AAAAgQCI1l8b70M5xKQ0q77dPs
vVq0Z/0d29VBLYSqIxmIkKE4kneeGThoU9Jfcx6+IdwLc/DSkKcGlWvlhGGWSuR4Osa3Kt
6aDzA4IRrE6jlShonrfmn1p0XEF9kt/vs6mAtfOlTDPZl2dZAYaH6M3lvHNisnX/YQdHl/
Hy0dkW1KRMfwAAAIEA5/kUNCskN1steGUzQ1r3sQSc/dYioezfuPWmX3zUwy13iTyx/KDE
fqzKbLOx1EjpDT118XbsLuBWCD/+szOfqv18DjZkxweu4cihuAiJ81OMd+hs4u10BtucS6
ge8USGQ0Mxp2sbFjI2VjwWYRJ6TE43VNBrdZVONL9QazB6wiMAAACBAMPDfZPClZRdfOog
wUP4lm4At82kZpmFurfPpNTAH0C0hW4DOm3bN0kENulS5IQoOX2xEmuqpWPN8t7EVnCz6a
RNnJMcIyTN69cq8JMoBWHUC8nFl6fvfC28R1ATk0sH1HOgpQm5TYVvD2YjcDNbuIkqhRNB
PHdReNR4fu//MbF9AAAAFnJvb3RAaXAtMTAtMTY5LTIzMi0yNDkBAgME
-----END OPENSSH PRIVATE KEY-----
'''
    payload = dict(name="unencrypted open ssh_credentials-%s" % fauxfactory.gen_utf8(),
                   description="machine credential - %s" % fauxfactory.gen_utf8(),
                   kind='ssh',
                   user=admin_user.id,
                   username=fauxfactory.gen_alphanumeric(),
                   ssh_key_data=unencrypted_open_ssh_key_data)

    obj = api_credentials_pg.post(payload)
    request.addfinalizer(obj.silent_delete)
    return obj


#
# Encrypted open ssh key
#
@pytest.fixture(scope="function")
def encrypted_open_ssh_credential(request, authtoken, api_credentials_pg, admin_user):
    '''Create open ssh_credential'''
    encrypted_open_ssh_key_data = '''\
-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAACmFlczI1Ni1jYmMAAAAGYmNyeXB0AAAAGAAAABDU7PneAw
YO3nrhifdfIc6hAAAAEAAAAAEAAAEXAAAAB3NzaC1yc2EAAAADAQABAAABAQC9161iiiLx
Ap5Vd2Cm7DW42Sc6mc8KE5d+nXzS0WGUcfrtRzioBHY40ULKfKD4x6rMXPm5cyYI0KEzsh
Z6mJ4kidj7UcUc7hJE2MHl/zDhiNAcFQDAmF3urlRkX5lRmFYN+aO00U4uBFcQu6fdj3yo
oxtnVR1Fd2vAnNtaTdheTtCVSnMkPYl3ElU14XH6QI5VU2l/wD1iybiGmpNJWwYi+w93mq
LwsQ44gq9ak9I813Jjq5LDC1ahnvTMbSK5XApTeqp8+Bbr1pKtSr5t0W8MYXDwDzBWXLRw
cy00aotA2sy/k9/HGeWSNABvGzEteKQE002TWc76HHgv1KBaf8qhAAAD0G9jFi9CZPtlWr
cxR4y3OPMDp/0ef8zDL+SPVRZONWFhK0tl2Zivi0uqJ9tZU6+39hMQAFdFDTFjYn9TakYd
rXqLtMzJJV2exIanCHRS45Cfp1REgS5eaeT26h6/dAkDz7Tk+HgCyCS0MWu4GWcS3Sx1kA
yFiYyxMI1fY95pS2pfwDHwo9B7cQPEbSyknT4FxMDu6ar27hRU2qXlrUL9z0dS3Wh+UxGh
Smojo6Bia0coDCp20MilA+sKxC5V9HEfwE8L5nUtbMToVua5bhhq2uWpvZ5v1sSB1CE97U
wfNOZ/i5fBUqZ72ZGUmn+ymBtPNimcWuFoqZ1RZpnATjM4TTxFtiry6SHLnKRoOT+RzAlQ
+Uy8CTleSUJ6RgIxHIgI2tSQW4YZcm57pSR9XKfchBjMcaUo+NwKk49Mq7ze+v1Y6Tacsb
0F4k2hntWVOMqofb46fjnqZIOJUDrtEwri66OqhmgvCP53I1t7CpXOBjkYZrgAvt4v+ZMo
3ElFMNpe8lBLb1PX+WO+j7A/NHOZFkDUoy6bI3h23PQ6i/FzzFRq6uwK8z3CrsUafkftUt
RGDOZ6XvjaPWwnT2HokFbSjzIrJyTRycD6opl54eHRadXxAvIhRKjscOt5cnJtBGKBW8UL
ezdl0nJTg/N7z1PyDqW7YPQMWHwYTiv0by+6HXHkLBYFobclUmADQEURbbwGAklEsV+02T
h93CUB/ml1Fu0pMr5EK6L/d0GmdOM7Mc8WrwerwbWY4EqVBur7Mtgph5atN9A8WcTQ9fsh
2LaVKj5518xlkOdquih38TvL/LUzFz7AZV9tbp0dbl1hMotG+JPim4TGTQTSSzsg20wLDv
O5UWpiQ5MlamEIHT5NPUwtOCXmUma/e6IBsSUjqptD34ikvmRl0fXJuY6hq55mSpsxgZqG
pJ316I7qHy0mEcxr7EDDgU480Hs7tpU24oxHgo6Gcr70eMgNCjq8hWsQN7VuWNYTg02FEo
THPn9B+39BcCbAHhGTufKoie62QgQk3OU8v3/d8jUsChIFfuaaPJHwBPtPPpOh8iYqRJ1Q
1f3eCYoywGQ4esQkIcXp9fzSzrouGxzQaPX5KyIEe+S6I8u7pqMaLlNmyVF0lvSEp/HeAD
rovWalsPSeiNDOslTtW0Dlx4h3teyzE7rlSxYOBAybRIv4PMRyG8DiktC3DxoGsJBZXFky
yL0q+MeKE61GhyoZ29qWSc233tYD70X9vhiZcgQo5Ai0oxz0T1utLjUoIOS8OuIL7Mefui
Q/c4BFOysCbZwf4MR74DBqvOV5GLw=
-----END OPENSSH PRIVATE KEY-----
'''
    payload = dict(name="encrypted open ssh_credentials-%s" % fauxfactory.gen_utf8(),
                   description="machine credential - %s" % fauxfactory.gen_utf8(),
                   kind='ssh',
                   user=admin_user.id,
                   username=fauxfactory.gen_alphanumeric(),
                   ssh_key_data=encrypted_open_ssh_key_data,
                   ssh_key_unlock='ASK')

    obj = api_credentials_pg.post(payload)
    request.addfinalizer(obj.silent_delete)
    return obj


#
# Convenience fixture that iterates through ssh credentials
#
@pytest.fixture(scope="function", params=['unencrypted_rsa', 'unencrypted_dsa', 'unencrypted_ecdsa', 'unencrypted_open',
                                          'encrypted_rsa', 'encrypted_dsa', 'encrypted_ecdsa', 'encrypted_open'])
def ssh_credential_with_ssh_key_data(request):
    return request.getfuncargvalue(request.param + '_ssh_credential')


#
# Convenience fixture that iterates through unencrypted ssh credentials
#
@pytest.fixture(scope="function", params=['unencrypted_rsa', 'unencrypted_dsa', 'unencrypted_ecdsa', 'unencrypted_open'])
def unencrypted_ssh_credential_with_ssh_key_data(request):
    return request.getfuncargvalue(request.param + '_ssh_credential')


#
# Convenience fixture that iterates through encrypted ssh credentials
#
@pytest.fixture(scope="function", params=['encrypted_rsa', 'encrypted_dsa', 'encrypted_ecdsa', 'encrypted_open'])
def encrypted_ssh_credential_with_ssh_key_data(request):
    return request.getfuncargvalue(request.param + '_ssh_credential')
