import json
from os import environ as env
from urllib.parse import quote_plus, urlencode

from authlib.integrations.flask_client import OAuth
from dotenv import find_dotenv, load_dotenv
from flask import Flask, redirect, render_template, session, url_for

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
        "scope": "openid profile email",
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
    session["user"] = token
    return redirect("/")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/")
def home():
    logout = env.get("ISSUER") + "/oauth2/logout?" + urlencode({"client_id": env.get("CLIENT_ID")},quote_via=quote_plus)

    return render_template(
        "home.html",
        session=session.get('user'),
        profile=json.dumps(session.get('user'), indent=2),
        logoutUrl=logout)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=env.get("PORT", 3000))