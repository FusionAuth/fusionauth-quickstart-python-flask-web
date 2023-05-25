import json
from os import environ as env
from urllib.parse import quote_plus, urlencode

from authlib.integrations.flask_client import OAuth
from dotenv import find_dotenv, load_dotenv
from flask import Flask, redirect, render_template, session, url_for, request, make_response

ACCESS_TOKEN_COOKIE_NAME = "cb_access_token"
REFRESH_TOKEN_COOKIE_NAME = "cb_refresh_token"
USERINFO_COOKIE_NAME = "cb_userinfo"

ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

app = Flask(__name__)
app.secret_key = env.get("APP_SECRET_KEY")

oauth = OAuth(app)

oauth.register(
    "FusionAuth",
    client_id=env.get("CLIENT_ID"),
    client_secret=env.get("CLIENT_SECRET"),
    client_kwargs={
        "scope": "openid offline_access",
        'code_challenge_method': 'S256' # This enables PKCE
    },
    server_metadata_url=f'{env.get("ISSUER")}/.well-known/openid-configuration'
)

@app.route("/login")
def login():
    return oauth.FusionAuth.authorize_redirect(
        redirect_uri=url_for("callback", _external=True)
    )


@app.route("/callback", methods=["GET", "POST"])
def callback():
    token = oauth.FusionAuth.authorize_access_token()

    resp = make_response(redirect("/"))

    resp.set_cookie(ACCESS_TOKEN_COOKIE_NAME, token["access_token"], max_age=token["expires_in"], httponly=True, samesite="Lax")
    resp.set_cookie(REFRESH_TOKEN_COOKIE_NAME, token["refresh_token"], max_age=token["expires_in"], httponly=True, samesite="Lax")
    resp.set_cookie(USERINFO_COOKIE_NAME, json.dumps(token["userinfo"]), max_age=token["expires_in"], httponly=True, samesite="Lax")
    session["user"] = token["userinfo"]

    return resp


@app.route("/logout")
def logout():
    session.clear()

    resp = make_response(redirect("/"))
    resp = delete_auth_cookies(resp)

    return resp


@app.route("/")
def home():
    logout = env.get("ISSUER") + "/oauth2/logout?" + urlencode({"client_id": env.get("CLIENT_ID")},quote_via=quote_plus)

    if request.cookies.get(ACCESS_TOKEN_COOKIE_NAME, None) is not None:
      # In a real application, we would validate the token signature and expiration
      return redirect("/account")

    return render_template("home.html")


#
# This is the logged in Account page.
#
@app.route("/account")
def account():
    access_token = request.cookies.get(ACCESS_TOKEN_COOKIE_NAME, None)
    refresh_token = request.cookies.get(REFRESH_TOKEN_COOKIE_NAME, None)

    if validate_access_token(access_token) is False:
      return redirect(get_logout_url())

    return render_template(
        "account.html",
        session=request.cookies.get(USERINFO_COOKIE_NAME, None),
        logoutUrl=get_logout_url())


# Normally you would use a decorator or some other mechanism to validate that the request carried a valid access token,
# and apply that to every protected endpoint.
#
# Validation would typically include
# * JWT signature is valid. Re-authenticate the user if it isn't.
# * The access token is not expired. If it is, attempt to refresh it. If that fails, re-authenticate the user.
#
def validate_access_token(access_token):
  # If the access token is None, that means that either user isn't logged in, or the cookie holding it expired.
  return access_token is not None


def delete_auth_cookies(response):
    response.delete_cookie(ACCESS_TOKEN_COOKIE_NAME)
    response.delete_cookie(REFRESH_TOKEN_COOKIE_NAME)
    response.delete_cookie(USERINFO_COOKIE_NAME)

    return response


def get_logout_url():
    return env.get("ISSUER") + "/oauth2/logout?" + urlencode({"client_id": env.get("CLIENT_ID")},quote_via=quote_plus)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=env.get("PORT", 3000))
