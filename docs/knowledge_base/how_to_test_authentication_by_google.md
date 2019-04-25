## Quickstarts: Google Authentication in Tower

The following guide will show you how to create a test app in Google and to use it to authenticate to a running Tower instance. This guide is current as of Tower-3.5.0

Reference product documentation: https://docs.ansible.com/ansible-tower/latest/html/administration/social_auth.html#google-oauth2-settings

### Step One: Create An Application in Google
* First we want to go to the Google Developer's Console and create a project. The GDC is located [here](https://console.developers.google.com/).
* Ensure you are logged into your redhat google account
* Select the Ansible Tower Engineering project (this effects what you see in rest of views)
* Now you want to enable [Google Sign-In](https://developers.google.com/identity/). Do this by search for "Cloud Identity API" under the "Library" section. Click "Enable."
* Exit the Library section. Now go to the "Credentials" screen (on left navigation bar).
* We want to create or use existing OAuth 2.0 client credentials.
* We can create new credentials by selecting "CREATE CREDENTIAL". We want to use the "Cloud Idenity API", we will be calling the API from a "Web Browser", and we want access to "User Data". These repsonses in the wizard will point you to create OAuth 2.0 Client Credentials, but first it will suggest you use an existing set if there is one present.
* Once you have your OAuth 2.0 client credentials, select the credential to get to an editable view.
* You need to add the address of your Tower instance to "Authorized redirect URIs" with `/sso/complete/google-oauth2/` at the end. So for instance, something like `https://tower.redhat.com/sso/complete/google-oauth2/`.
* In order to add the URI, you must have the base domain added to authorized domains. As of this writing, ec2 urls do not work for some reason. The Openshift URL works having added `redhat.com` as an authorized domain. Also, `localhost` or `127.0.0.1` work. This means we can test local docker deployments as well as ec2 via ssh port forwarding.
* To test against a tower deployed on ec2 then, we can set up ssh port forwarding from our local machine with a command like `ssh -L 8081:ec2-3-87-197-66.compute-1.amazonaws.com:443 localhost`. To break that down, it is `ssh -L <arbitrary available port on local machine>:<ec2-base-url>:443 localhost`. Then the "Authorized redirect URI will be `https://localhost:8081/sso/complete/google-oauth2/`. [Additional docs on ssh port forwarding](https://www.ssh.com/ssh/tunneling/example).
* Save and return to the main "Credentials" veiw.
* On the "OAuth Consent Screen," tab we need to fill in the following fields:
  * For "Product name shown to users," you can put whatever you want. I had `Testing - Ansible Tower` just as an example.


### Step Two: Set Up Tower to Talk to Google
The settings that enable the google oauth authentication are named:
```
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = 'This is the Client ID'
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = 'This is the Client Secret'
```
The Client ID and Client Secret are visible in the editible view of the OAuth 2.0 client IDs.

They can be set in several ways.

Trad cluster:
  * Open `/etc/tower/conf.d/social_auth.py` and supply values.

Local docker:
  * Edit `awx/settings/default.py` and edit settings with correct values.

Openshift:
  * TBD: Probably need to edit secrets or deployment config. Where ever settings are normally found.

Alternatively, you can do this through the web UI under Settings -> Authentication as outlined in the [product docs](https://docs.ansible.com/ansible-tower/latest/html/administration/social_auth.html#google-oauth2-settings).

If you set the settings manually in a settings file, it may be necessary to restart the tower services to pick up change. Once set manually in settings file, it is not editable from web UI.

* You are now ready to authenticate via Google. You may need to force-refresh your browser several times to get the Google icon to appear in the login modal.

### Step Three: Sanity Test
Use the google log in and notice that a user is created. Log back out and log in as the admin. Grand this user access to an organization and then log out again. Log back in as user via google auth. Confirm that you have access to all expected resources.

Take note of name, username, and email. Log out and log back in as admin. Delete the user account created by the google sign in. Create a new account with same name, email, and username as the one created by google. Assign distinct privledges from original account. Log out and log back in via google. Confirm that you log in as created user with appropriate permissions and that a new "duplicate" account is not created.
