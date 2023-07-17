#tag::baseApplication[]
import json
import math
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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=env.get("PORT", 5000))

def get_logout_url():
    return env.get("ISSUER") + "/oauth2/logout?" + urlencode({"client_id": env.get("CLIENT_ID")},quote_via=quote_plus)
#end::baseApplication[]

#tag::homeRoute[]
@app.route("/")
def home():
    if request.cookies.get(ACCESS_TOKEN_COOKIE_NAME, None) is not None:
      # In a real application, we would validate the token signature and expiration
      return redirect("/account")

    return render_template("home.html")
#end::homeRoute[]


#tag::loginRoute[]
@app.route("/login")
def login():
    return oauth.FusionAuth.authorize_redirect(
        redirect_uri=url_for("callback", _external=True)
    )
#end::loginRoute[]


#tag::callbackRoute[]
@app.route("/callback")
def callback():
    token = oauth.FusionAuth.authorize_access_token()

    resp = make_response(redirect("/"))

    resp.set_cookie(ACCESS_TOKEN_COOKIE_NAME, token["access_token"], max_age=token["expires_in"], httponly=True, samesite="Lax")
    resp.set_cookie(REFRESH_TOKEN_COOKIE_NAME, token["refresh_token"], max_age=token["expires_in"], httponly=True, samesite="Lax")
    resp.set_cookie(USERINFO_COOKIE_NAME, json.dumps(token["userinfo"]), max_age=token["expires_in"], httponly=False, samesite="Lax")
    session["user"] = token["userinfo"]

    return resp
#end::callbackRoute[]


#tag::logoutRoute[]
@app.route("/logout")
def logout():
    session.clear()

    resp = make_response(redirect("/"))
    resp.delete_cookie(ACCESS_TOKEN_COOKIE_NAME)
    resp.delete_cookie(REFRESH_TOKEN_COOKIE_NAME)
    resp.delete_cookie(USERINFO_COOKIE_NAME)

    return resp
#end::logoutRoute[]


#
# This is the logged in Account page.
#
#tag::accountRoute[]
@app.route("/account")
def account():
    access_token = request.cookies.get(ACCESS_TOKEN_COOKIE_NAME, None)
    refresh_token = request.cookies.get(REFRESH_TOKEN_COOKIE_NAME, None)

    if access_token is None:
      return redirect(get_logout_url())

    return render_template(
        "account.html",
        session=json.loads(request.cookies.get(USERINFO_COOKIE_NAME, None)),
        logoutUrl=get_logout_url())
#end::accountRoute[]


#
# Takes a dollar amount and converts it to change
#
#tag::makeChangeRoute[]
@app.route("/make-change", methods=['GET', 'POST'])
def make_change():
    access_token = request.cookies.get(ACCESS_TOKEN_COOKIE_NAME, None)
    refresh_token = request.cookies.get(REFRESH_TOKEN_COOKIE_NAME, None)

    if access_token is None:
      return redirect(get_logout_url())

    change = {
      "error": None
    }

    if request.method == 'POST':
        dollar_amt_param = request.form["amount"]

        try:
            if dollar_amt_param:
                dollar_amt = float(dollar_amt_param)

                nickels = int(dollar_amt / 0.05)
                pennies = math.ceil((dollar_amt - (0.05 * nickels)) / 0.01)

                change["total"] = format(dollar_amt, ",.2f")
                change["nickels"] = format(nickels, ",d")
                change["pennies"] = format(pennies, ",d")

        except ValueError:
            change["error"] = "Please enter a dollar amount"

    return render_template(
        "make-change.html",
        session=json.loads(request.cookies.get(USERINFO_COOKIE_NAME, None)),
        change=change,
        logoutUrl=get_logout_url())
#end::makeChangeRoute[]
