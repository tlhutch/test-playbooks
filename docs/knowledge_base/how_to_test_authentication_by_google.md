## Quickstarts: Google Authentication in Tower

The following guide will show you how to create a test app in Google and to use it to authenticate to a running Tower instance. This guide is current as of Tower-3.0.2.

### Step One: Create An Application in Google
* First we want to go to the Google Developer's Console and create a project. The GDC is located [here](https://console.developers.google.com/).
* Now you want to enable the Google+ API. Do this by selecting "Google+ API" under the "Library" section. Click "Enable."
* Now go to the "Credentials" screen and under "Create credentials," select "OAuth client ID." Now select "Web application."
* Before you hit "Create," fill put the address of your Tower instance in for "Authorized redirect URIs" with `/sso/complete/google-oauth2/` at the end. So for instance, something like `https://ec2-something.compute-1.amazonaws.com/sso/complete/google-oauth2/`.
* On the "OAuth Consent Screen," we need to fill in the following fields:
  * For "Product name shown to users," you can put whatever you want. I had `Testing - Ansible Tower` just as an example.
  * For "Product logo URL," put your Tower host address. So for me, I had: `https://ec2-something.compute-1.amazonaws.com`.
* On the resulting modal, select "Web Application." Your screen should now look as follows. The values here will be used Tower-side.

### Step Two: Set Up Tower to Talk to Google
* Open `/etc/tower/conf.d/social_auth.py` in your favorite editor.
* Edit the following two fields with the values supplied by Google:
```
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = 'FIXME'
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = 'FIXME'
```
* Restart Tower services with `ansible-tower-service restart`.
* You are now ready to authenticate via Google. You may need to force-refresh your browser several times to get the Github to appear in the login modal.

Written by [Christopher Wang](mailto:chrwang@redhat.com) (Github: simfarm) September 1, 2016.
