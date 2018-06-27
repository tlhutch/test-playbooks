## Quickstarts: SAML Authentication in Tower

The following is a quickstarts guide to getting SAML and Tower working together. This guide is current as of Tower-3.0.2.

#### Step 1: Set Up OneLogin
* We currently can get a SAML server through OneLogin. To get started, you will need an account with OneLogin and [Graham Mainwarning](mailto:gmainwar@redhat.com) can assist with this. You will need admin permissions with your user so be sure to ask when having your account created.
* We are now going to create a new SAML app. To do this, go [here](https://admin.us.onelogin.com/apps/find). Select “SAML Test Connector (IdP w/attr)”. Hit “Save” to create your app.
* We are now going to configure our SAML server via the OneLogin portal. First, go to the “Configuration” tab. We are going to fill out four fields here. We want the following for our fields:
  * For "Audience" put in the address of your Tower server. So for instance, `https://ec2-something.compute-1.amazonaws.com`.
  * For "Recipient" and "ACS" put in the address of your Tower server too and also shove in `/sso/complete/saml/` at the end. In total, you should have something like `https://ec2-something.compute-1.amazonaws.com/sso/complete/saml/`.
  * "ACS (Consumer) URL Validator" is the trickiest part. Here we want to supply a regex that will validate the value of the "ACS (Consumer) URL" field. So for me, I had `^https:\/\/ec2-something.compute-1.amazonaws.com\/sso\/complete\/saml\/$`.
  * In total, I had the following for these four fields:
  ```
  Audience: https://hostname.amazonaws.com
  Recipient: https://hostname.amazonaws.com/sso/complete/saml/
  ACS URL Validator: ^https:\/\/hostname.amazonaws.com\/sso\/complete\/saml\/$
  ACS URL: https://hostname.amazonaws.com/sso/complete/saml/
  ```
* Go to the “Parameters” tab next. Click "Add parameter" and call it `User.username`. For its value, select “Username” from the dropdown.  Check the "Include in SAML assertion" box.
* Now we want to generate metadata (basically information that we are now going to supply Tower-side). To get this from OneLogin, select “More Actions” => “SAML Metadata”. These buttons should be in the top-right corner.
* You should now have a big blob of XML. You will output these XML values to our `/api/v1/settings/saml/` endpoint. Example XML below:
```
<?xml version="1.0"?>
<EntityDescriptor xmlns="urn:oasis:names:tc:SAML:2.0:metadata" entityID="https://app.onelogin.com/saml/metadata/xxxxxx">
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
* Navigate to `/api/v1/settings/saml/`.
* For `SOCIAL_AUTH_SAML_SP_ENTITY_ID` put the address of your Tower server. So for instance, `http://ec2-something.compute-1.amazonaws.com`.
* `SOCIAL_AUTH_SAML_SP_PUBLIC_CERT` and `SOCIAL_AUTH_SAML_SP_PRIVATE_KEY` can be any certificate pair with an unencrypted key.  Feel free to generate one via

```
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes
```
* The only other thing to think about is filling out the following section with our metadata from OneLogin:
```
    "SOCIAL_AUTH_SAML_ENABLED_IDPS": {
        "onelogin": {
            "attr_last_name": "User.LastName",
            "attr_username": "User.username",
            "entity_id": "https://app.onelogin.com/saml/metadata/FIXME",
            "attr_user_permanent_id": "name_id",
            "url": "https://ansible.onelogin.com/trust/saml2/http-post/sso/FIXME",
            "attr_email": "User.email",
            "x509cert": "FIXME",
            "attr_first_name": "User.FirstName"
        }
    },
```
* In total, I had the following:
```
{
    "SOCIAL_AUTH_SAML_CALLBACK_URL": "http://hostname.amazonaws.com/sso/complete/saml/",
    "SOCIAL_AUTH_SAML_METADATA_URL": "http://hostname.amazonaws.com/sso/metadata/saml/",
    "SOCIAL_AUTH_SAML_SP_ENTITY_ID": "http://hostname.amazonaws.com",
    "SOCIAL_AUTH_SAML_SP_PUBLIC_CERT": your X.509 cert,
    "SOCIAL_AUTH_SAML_SP_PRIVATE_KEY": your X.509 key,
    "SOCIAL_AUTH_SAML_ORG_INFO": {
        "en-US": {
            "url": "http://www.example.com",
            "displayname": "Example",
            "name": "example"
        }
    },
    "SOCIAL_AUTH_SAML_TECHNICAL_CONTACT": {
        "givenName": "Some User",
        "emailAddress": "suser@example.com"
    },
    "SOCIAL_AUTH_SAML_SUPPORT_CONTACT": {
        "givenName": "Some User",
        "emailAddress": "suser@example.com"
    },
    "SOCIAL_AUTH_SAML_ENABLED_IDPS": {
        "onelogin": {
            "attr_last_name": "User.LastName",
            "attr_username": "User.username",
            "entity_id": "https://app.onelogin.com/saml/metadata/xxxxxx",
            "attr_user_permanent_id": "name_id",
            "url": "https://ansible.onelogin.com/trust/saml2/http-post/sso/xxxxxx",
            "attr_email": "User.email",
            "x509cert": onelogin provided X.509 cert,
            "attr_first_name": "User.FirstName"
        }
    },
    "SOCIAL_AUTH_SAML_ORGANIZATION_MAP": null,
    "SOCIAL_AUTH_SAML_TEAM_MAP": null
}
```
* Install an enterprise license since SAML is an enterprise-only feature.

Written by [Christopher Wang](mailto:chrwang@redhat.com) (Github: simfarm) September 1, 2016.
