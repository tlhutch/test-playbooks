## Quickstarts: SAML Authentication in Tower

The following is a quickstarts guide to getting SAML and Tower working together. This guide is current as of Tower-3.0.2.

#### Step 1: Set Up OneLogin
* We currently can get a SAML server through OneLogin. To get started, you will need an account with OneLogin and [Tim Cramer](mailto:ticramer@redhat.com) currently holds the master account so he is the person to ask. You will need admin permissions with your user so be sure to ask when having your account created.
* We are now going to create a new SAML app. To do this, go [here](https://admin.us.onelogin.com/apps/find). Select “SAML Test Connector (IdP w/attr)”. Hit “Save” to create your app.
* We are now going to configure our SAML server via the OneLogin portal. First, go to the “Configuration” tab. We are going to fill out four fields here. We want the following for our fields:
  * For "Audience" put in the address of your Tower server. So for instance, `http://ec2-something.compute-1.amazonaws.com`.
  * For "Recipient" and "ACS" put in the address of your Tower server too and also shove in `/sso/complete/saml/` at the end. In total, you should have something like `http://ec2-something.compute-1.amazonaws.com/sso/complete/saml/`.
  * "ACS (Consumer) URL Validator" is the trickiest part. Here we want to supply a regex that will validate the value of the "ACS (Consumer) URL" field. So for me, I had `^http:\/\/ec2-54-80-240-189.compute-1.amazonaws.com\/sso\/complete\/saml\/$`.
  * In total, I had the following for these four fields:
  ```
  Audience: http://ec2-54-91-32-226.compute-1.amazonaws.com
  Recipient: http://ec2-54-91-32-226.compute-1.amazonaws.com/sso/complete/saml/
  ACS URL Validator: ^http:\/\/http://ec2-54-91-32-226.compute-1.amazonaws.com\/sso\/complete\/saml\/$
  ACS URL: http://ec2-54-91-32-226.compute-1.amazonaws.com/sso/complete/saml/
  ```
* Go to the “Parameters” tab next. Click "Add parameter" and call it `username`. For its value, select “Username” from the dropdown.
* Now we want to generate metadata (basically information that we are now going to supply Tower-side). To get this from OneLogin, select “More Actions” => “SAML Metadata”. These buttons should be in the top-right corner.
* You should now have a big blob of XML. You will output these XML values to our `/api/v1/settings/saml/` endpoint. Example XML below:
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
* Navigate to `/api/v1/settings/saml/`.
* For `SOCIAL_AUTH_SAML_SP_ENTITY_ID` put the address of your Tower server. So for instance, `http://ec2-something.compute-1.amazonaws.com`.
* `SOCIAL_AUTH_SAML_SP_PUBLIC_CERT` and `SOCIAL_AUTH_SAML_SP_PRIVATE_KEY` can be any certificate pair. You may use `tower.cert` and `tower.key` under `/etc/tower/`.
* The only other thing to think about is filling out the following section with our metadata from OneLogin:
```
    "SOCIAL_AUTH_SAML_ENABLED_IDPS": {
        "onelogin": {
            "attr_last_name": "User.LastName",
            "attr_username": "User.email",
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
    "SOCIAL_AUTH_SAML_CALLBACK_URL": "http://ec2-54-91-32-226.compute-1.amazonaws.com/sso/complete/saml/",
    "SOCIAL_AUTH_SAML_METADATA_URL": "http://ec2-54-91-32-226.compute-1.amazonaws.com/sso/metadata/saml/",
    "SOCIAL_AUTH_SAML_SP_ENTITY_ID": "http://ec2-54-91-32-226.compute-1.amazonaws.com",
    "SOCIAL_AUTH_SAML_SP_PUBLIC_CERT": "-----BEGIN CERTIFICATE-----\nMIIDhTCCAm2gAwIBAgIJALcibc1rHc2aMA0GCSqGSIb3DQEBCwUAMFgxCzAJBgNV\nBAYTAlVTMQswCQYDVQQIDAJOQzEQMA4GA1UEBwwHUmFsZWlnaDEQMA4GA1UECgwH\nQW5zaWJsZTEYMBYGA1UEAwwPd3d3LmFuc2libGUuY29tMCAXDTE2MTAyNDE0MTUy\nOVoYDzIyOTAwODA4MTQxNTI5WjBYMQswCQYDVQQGEwJVUzELMAkGA1UECAwCTkMx\nEDAOBgNVBAcMB1JhbGVpZ2gxEDAOBgNVBAoMB0Fuc2libGUxGDAWBgNVBAMMD3d3\ndy5hbnNpYmxlLmNvbTCCASIwDQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEBAMDM\njUBaLfdoOcms9QxmGkQvyFc6WqJ4lv5pgoi+nP9rCeIWCytiDDnFwIHPZ1+1m7An\nQ3jmWuPbVdq0lEipYKMB3iH3x6F6CLPAZK6Rnys2Gkk7dXAgw8e3vStpiMKeMKO9\ntG8Rnpf1jsN0lBKlRfQokcVpdDLCUEtXyK0volnFhfHT/ANJrX2gmkIjff5WY5wi\nkCLP2TCwWSoVKU1pp3nhWU3CU+1mWMCAgLh+aEVmCp5QAqVqRIP7/D86JopA+87p\nK1+JJhi385pjAlxLxujYP+jesN8hbuai3rXUTan3L4Yti/VrVXguv8QQPmXg77MH\ngHLtnWA2+bqIhUSThmMCAwEAAaNQME4wHQYDVR0OBBYEFKUCO3ghm0TG7n5KMB0p\ninsuywAbMB8GA1UdIwQYMBaAFKUCO3ghm0TG7n5KMB0pinsuywAbMAwGA1UdEwQF\nMAMBAf8wDQYJKoZIhvcNAQELBQADggEBAJDbEkMzpXOEW5Uv/AuMQYHsNPa6z4Jr\nEzI075jjHRGnrqXV2mtq6EuqZTIFhz/aCJg9eUHkmA0OLMlJWNM9WO0dDmVW4nn0\ni506ccTb60F+3s0uNyA7JCCyEodRIhWYPjj9Z/JnGNKgP0MLL7GNSWoA0wKJX859\nAnSgndm08IwONMOpZ/W7RRMFqEkZAaynOpRk+F1dSqTqSinAYIiDsGwfRZK2fWX+\nQH5T0MGjlE6uDDEIuJyBBVXX9vmXqVoMwiInOS1EFYXv48ElP4y0yPAhjESqCxTd\npXkYUDRoTSQvJntsr1P0KAFURzDYNI8fsvx0MsapSEHQi2dbhPHvjfs=\n-----END CERTIFICATE-----",
    "SOCIAL_AUTH_SAML_SP_PRIVATE_KEY": "-----BEGIN PRIVATE KEY-----\nMIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQDAzI1AWi33aDnJ\nrPUMZhpEL8hXOlqieJb+aYKIvpz/awniFgsrYgw5xcCBz2dftZuwJ0N45lrj21Xa\ntJRIqWCjAd4h98ehegizwGSukZ8rNhpJO3VwIMPHt70raYjCnjCjvbRvEZ6X9Y7D\ndJQSpUX0KJHFaXQywlBLV8itL6JZxYXx0/wDSa19oJpCI33+VmOcIpAiz9kwsFkq\nFSlNaad54VlNwlPtZljAgIC4fmhFZgqeUAKlakSD+/w/OiaKQPvO6StfiSYYt/Oa\nYwJcS8bo2D/o3rDfIW7mot611E2p9y+GLYv1a1V4Lr/EED5l4O+zB4By7Z1gNvm6\niIVEk4ZjAgMBAAECggEATBBnqfvqJrH4GpkiFMIzmrM/Vyqul2r8J2N5HHoXdq3E\nOG55+aO1LxXV3WD2Z8w+oEDdXdWEBmGCfcbAueoZNjaGbOBU4mBDDqfZEQZixamS\ntVHAA3zpwOG8wGPikOXYSsGNbkSFTW6T5IkZ4kFSWAGpgTkZnu0KwK7hfXJNmxyi\nKPjwpJqiY1sinDm+26s+btj6C82U76aEOIzXMrH2Ue0LyWfkuq1ianuhqa47YERH\nEEM5hZiRtxtb2r89gqdM61SRcV10o6BXoo2H5AmZlV19HHSSj9yIkE9jz7022K1M\nQC0xi3xHJvsVlbd4zegfVCEHbGSACN8A0Sus7RTwAQKBgQD6mGLcI3YFCX1CSWhu\nRlzNJlTYX1mxnYF9QQvjfaMKUNfjKbcZiuUPSNjkZXbSUrQoJy34r6c3sL8IBu9C\noqw1TBKVTROQ4W4oB+TuPUvVmnpG1DFuMZN0lrgRiRJJ8kBcg+MHGsIT6uT2N1km\nKpmJkF1/aYKP1fih4NMGilHweQKBgQDE9Q4E98tZ5jjUQVI9IWFABgwLrTUyX+a9\n0g4vo1Ql/js6CY1OUdm2OJ/i7No6jpRYwc2qMINz9QJ4Hq2AZpVBQd99TOz4Doas\nfnsfq3/3Vg83PV987lsK+iKuc2azqMgzglsitXR6O4YE8psR13e+QHFV0JZV9krr\nppNLyhROuwKBgEbtHIX8D2pLjkVVq5YSmi+CWt9G1Ycc8kp2P5wqshu4V/I2m1lC\nY6SY1LKIOUI8IDuBI1TQun5bqyXleJCepCkNl/Dj+Na3x0rTOSto8+7IIzWq1za+\nF2MXSY/FAQUm6KqGtZoMK8QhZp59eeEAi6ZQ0vW98jMtt4pxrKicO6bZAoGAbEfF\nQ1nvxCbby2V2DwGQ85/fc3PwMRekRWt8PRhwJMsWSJwDwbEiHhoXXKyWdWb5i6pQ\npWYyfseOafeDr3m2SMAsXDi0dtOVmrOWgRzKJ3J6vwXQv2BTUT+fXYU4S0FZf2gF\nLpnPxXt//KxcMHzi6geHx4P7gpr7KX7Ur/ATJg0CgYB7LQ5fZmj2XCb00fUeavpW\nAq2yNtn2ZHAaBvTcUhOXvL6nEqmFfYVHaI7lK4R/Hul/qi1SX7fMJzi9md/BuGgD\nEFx/Ib3ejNxZbIukYm3KRN8ByBk/ZLgfD0ppq581pXBTrt4EtIRqo3jvw3XMjdqr\n38g3BcVyILlxyDhFYqSqAg==\n-----END PRIVATE KEY-----",
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
            "attr_username": "User.email",
            "entity_id": "https://app.onelogin.com/saml/metadata/605388",
            "attr_user_permanent_id": "name_id",
            "url": "https://ansible.onelogin.com/trust/saml2/http-post/sso/605388",
            "attr_email": "User.email",
            "x509cert": "MIIEJjCCAw6gAwIBAgIUfuSD54OPSBhndDHh3gZorvrIaoAwDQYJKoZIhvcNAQEF\nBQAwXTELMAkGA1UEBhMCVVMxFjAUBgNVBAoMDUFuc2libGUsIEluYy4xFTATBgNV\nBAsMDE9uZUxvZ2luIElkUDEfMB0GA1UEAwwWT25lTG9naW4gQWNjb3VudCA2NDEy\nNzAeFw0xNTA1MTIxNTU2NTBaFw0yMDA1MTMxNTU2NTBaMF0xCzAJBgNVBAYTAlVT\nMRYwFAYDVQQKDA1BbnNpYmxlLCBJbmMuMRUwEwYDVQQLDAxPbmVMb2dpbiBJZFAx\nHzAdBgNVBAMMFk9uZUxvZ2luIEFjY291bnQgNjQxMjcwggEiMA0GCSqGSIb3DQEB\nAQUAA4IBDwAwggEKAoIBAQC2YfKbJZSssbtotYrOD35OLIqQBIrxVK7G7tRno5pg\nh1ZLJSCitqCuauEi4xYCV9Rd2RisJN0gwqg5VqBeRgtwQIDe4pNljxAkSS/UChl6\nmMnA0OT46iBWD2fiTIx2W82BrCSN+f3oNvJcigbp3IdS1Njr23HCS9K6zQ7Oby2F\nTbIEoKW0I+8V7dRPLyEtNoyf7GUQvf4sLGTbK3Bh1QBK4wFGMjOcigLu1OE8+F+o\nemVMTVTlky3veSGbqX8IPReVtqqYx2e55pdAs1Fo75M2OqOZArSlzQBaK+1WP5gr\nz1VQMywc+S+kma5ES3xetw94kLoTbknyt23BKeUVqCrtAgMBAAGjgd0wgdowDAYD\nVR0TAQH/BAIwADAdBgNVHQ4EFgQUG6dSxZkCptzLshpJU3222h57ra4wgZoGA1Ud\nIwSBkjCBj4AUG6dSxZkCptzLshpJU3222h57ra6hYaRfMF0xCzAJBgNVBAYTAlVT\nMRYwFAYDVQQKDA1BbnNpYmxlLCBJbmMuMRUwEwYDVQQLDAxPbmVMb2dpbiBJZFAx\nHzAdBgNVBAMMFk9uZUxvZ2luIEFjY291bnQgNjQxMjeCFH7kg+eDj0gYZ3Qx4d4G\naK76yGqAMA4GA1UdDwEB/wQEAwIHgDANBgkqhkiG9w0BAQUFAAOCAQEAGGN/SgN7\npbwquue4HhoFx2ssMTZUfdswlB6rdq81gc03Jxum38B+WrUpNcJgQtkg7N++0/q6\nzXlfSROPBnLYq1pmwcMvZ+puySgRrtxNpavvUZjdfEkYrXxmEXdnwlxitsL1Lmry\nvM/lPxBxWYzrR4Cz51f44bKvTnYUa0lEi73K+4H/nb5F+P+GD4F4Fv4267eLMbj8\n83j7Zw3iEVMOtF7O7coS+fwVym5KuBafzCzfiYdbAK9ceCb80TP2M9As03B9rhCi\nQeqc9lAtMmx1L1umCyBkX8aA1OLZ1gnFt0jYGmpWzXMUECrPWfuADB750lJuR5Tf\n+0Kk+xrlgUe7zA==",
            "attr_first_name": "User.FirstName"
        }
    },
    "SOCIAL_AUTH_SAML_ORGANIZATION_MAP": null,
    "SOCIAL_AUTH_SAML_TEAM_MAP": null
}
```
* Install an enterprise license since SAML is an enterprise-only feature.

Written by [Christopher Wang](mailto:chrwang@redhat.com) (Github: simfarm) September 1, 2016.
