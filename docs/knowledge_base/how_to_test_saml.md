## Quickstarts: SAML Authentication in Tower

The following is a quickstarts guide to getting SAML and Tower working together. This guide is current as of Tower-3.0.2.

#### Step 1: Set Up OneLogin
* We currently can get a SAML server through OneLogin. To get started, you will need an account with OneLogin and [Tim Cramer](mailto:ticramer@redhat.com) currently holds the master account so he is the person to ask. You will need admin permissions with your user so be sure to ask when having your account created.
* We are now going to create a new SAML app. To do this, go [here](https://admin.us.onelogin.com/apps/find). Select “SAML Test Connector (IdP w/attr)”. Hit “Save” to create your app.
* We are now going to configure our SAML server via the OneLogin portal. First, go to the “Configuration” tab. We are going to fill out four fields here. We want the following for our fields:
  * For "Audience" put in the address of your Tower server. So for instance, `https://ec2-something.compute-1.amazonaws.com`.
  * For "Recipient" and "ACS" put in the address of your Tower server too and also shove in `/sso/complete/saml/` at the end. In total, you should have something like `https://ec2-something.compute-1.amazonaws.com/sso/complete/saml/`.
  * "ACS (Consumer) URL Validator" is the trickiest part. Here we want to supply a regex that will validate the value of the "ACS (Consumer) URL" field. So for me, I had `^http:\/\/ec2-54-80-240-189.compute-1.amazonaws.com\/sso\/complete\/saml\/$`.
* Go to the “Parameters” tab next. Click "Add parameter" and call it `username`. For its value, select “Username” from the dropdown.
* Now we want to generate metadata (basically information that we are now going to supply Tower-side). To get this from OneLogin, select “More Actions” => “SAML Metadata”. These buttons should be in the top-right corner.
* You should now have a big blob of XML. You will output these XML values to our `/etc/tower/conf.d/social_auth.py` file. Example XML below:
```
<?xml version="1.0"?>
<EntityDescriptor xmlns="urn:oasis:names:tc:SAML:2.0:metadata" entityID="https://app.onelogin.com/saml/metadata/581465">
  <IDPSSODescriptor xmlns:ds="http://www.w3.org/2000/09/xmldsig#" protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol">
    <KeyDescriptor use="signing">
      <ds:KeyInfo xmlns:ds="http://www.w3.org/2000/09/xmldsig#">
        <ds:X509Data>
          <ds:X509Certificate>MIIEJjCCAw6gAwIBAgIUfuSD54OPSBhndDHh3gZorvrIaoAwDQYJKoZIhvcNAQEF
BQAwXTELMAkGA1UEBhMCVVMxFjAUBgNVBAoMDUFuc2libGUsIEluYy4xFTATBgNV
BAsMDE9uZUxvZ2luIElkUDEfMB0GA1UEAwwWT25lTG9naW4gQWNjb3VudCA2NDEy
NzAeFw0xNTA1MTIxNTU2NTBaFw0yMDA1MTMxNTU2NTBaMF0xCzAJBgNVBAYTAlVT
...
```

#### Step 2: Set Up Tower to talk to OneLogin
* Now hop on to your Tower machine and open `/etc/tower/conf.d/social_auth.py` in your favorite editor.
* For `SOCIAL_AUTH_SAML_SP_ENTITY_ID` put the address of your Tower server. So for instance, `https://ec2-something.compute-1.amazonaws.com`.
* `SOCIAL_AUTH_SAML_SP_PUBLIC_CERT` and `SOCIAL_AUTH_SAML_SP_PRIVATE_KEY` can be any certificate pair. You may use `tower.cert` and `tower.key` under `/etc/tower/`.
* The only other thing to think about is filling out the following section with our metadata from OneLogin:
```
    'onelogin': {
        'entity_id': 'https://app.onelogin.com/saml/metadata/FIXME',
        'url': 'https://example.onelogin.com/trust/saml2/http-post/sso/FIXME',
        'x509cert': '''
         FIXME
         ''',
        'attr_user_permanent_id': 'name_id',
        'attr_first_name': 'User.FirstName',
        'attr_last_name': 'User.LastName',
        'attr_username': 'User.email',
        'attr_email': 'User.email',
    },

```
* Restart Tower with `ansible-tower-service restart` and you should be good to go.

Written by [Christopher Wang](mailto:chrwang@redhat.com) (Github: simfarm) September 1, 2016.
