from fusionauth.fusionauth_client import FusionAuthClient
import os
import sys

APPLICATION_ID = "e9fdb985-9173-4e01-9d73-ac2d60d1dc8e";

#  You must supply your API key
api_key_name = 'fusionauth_api_key'
api_key = os.getenv(api_key_name)
if not api_key:
  sys.exit("please set api key in the '" + api_key_name + "' environment variable")

client = FusionAuthClient(api_key, 'http://localhost:9011')

# set the issuer up correctly
client_response = client.retrieve_tenants()
if client_response.was_successful():
  tenant = client_response.success_response["tenants"][0]
else:
  sys.exit("couldn't find tenants " + str(client_response.error_response))

client_response = client.patch_tenant(tenant["id"], {"tenant": {"issuer":"http://localhost:9011"}})
if not client_response.was_successful():
  sys.exit("couldn't update tenant "+ str(client_response.error_response))

# generate RSA keypair for signing
rsa_key_id = "356a6624-b33c-471a-b707-48bbfcfbc593"

client_response = client.generate_key({"key": {"algorithm":"RS256", "name":"For PythonExampleApp", "length": 2048}}, rsa_key_id)
if not client_response.was_successful():
  sys.exit("couldn't create RSA key "+ str(client_response.error_response))

# create application
# too much to inline it

application = {}
application["name"] = "PythonExampleApp"

# configure oauth
application["oauthConfiguration"] = {}
application["oauthConfiguration"]["authorizedRedirectURLs"] = ["http://localhost:5000/callback/"]
application["oauthConfiguration"]["requireRegistration"] = True
application["oauthConfiguration"]["enabledGrants"] = ["authorization_code", "refresh_token"]
application["oauthConfiguration"]["logoutURL"] = "http://localhost:5000/logout"
application["oauthConfiguration"]["clientSecret"] = "change-this-in-production-to-be-a-real-secret"

# some libraries don't support pkce, notably mozilla-django-oidc: https://github.com/mozilla/mozilla-django-oidc/issues/397
# since we are server side and have a solid client secret, we're okay turning pkce off
application["oauthConfiguration"]["proofKeyForCodeExchangePolicy"] = "NotRequiredWhenUsingClientAuthentication"

# assign key from above to sign tokens. This needs to be asymmetric
application["jwtConfiguration"] = {}
application["jwtConfiguration"]["enabled"] = True
application["jwtConfiguration"]["accessTokenKeyId"] = rsa_key_id
application["jwtConfiguration"]["idTokenKeyId"] = rsa_key_id

client_response = client.create_application({"application": application}, APPLICATION_ID)
if not client_response.was_successful():
  sys.exit("couldn't create application "+ str(client_response.error_response))

# register user, there should be only one, so grab the first
client_response = client.search_users_by_query({"search": {"queryString":"*"}})
if not client_response.was_successful():
  sys.exit("couldn't find users "+ str(client_response.error_response))

user = client_response.success_response["users"][0]

# patch the user to make sure they have a full name, otherwise OIDC has issues
client_response = client.patch_user(user["id"], {"user": {"fullName": user["firstName"]+" "+user["lastName"]}})
if not client_response.was_successful():
  sys.exit("couldn't patch user "+ str(client_response.error_response))

# now register the user
client_response = client.register({"registration":{"applicationId":APPLICATION_ID}}, user["id"])
if not client_response.was_successful():
  sys.exit("couldn't register user "+ str(client_response.error_response))