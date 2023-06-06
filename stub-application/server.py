import json
from os import environ as env
from urllib.parse import quote_plus, urlencode
from authlib.integrations.flask_client import OAuth
from flask import Flask, redirect, render_template, session, url_for, request, make_response

# This is needed by Flask, and can be any string
APP_SECRET_KEY = "0386ffa9-3bff-4c75-932a-48d6a763ce77"

app = Flask(__name__)
app.secret_key = APP_SECRET_KEY

@app.route("/")
def home():
    return render_template("home.html")


@app.route("/login")
def login():
    return redirect("/")


@app.route("/callback")
def callback():
    return redirect("/")


@app.route("/logout")
def logout():
    return redirect("/")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
