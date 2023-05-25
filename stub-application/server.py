import json
from os import environ as env
from urllib.parse import quote_plus, urlencode

from dotenv import find_dotenv, load_dotenv
from flask import Flask, redirect, render_template, session, url_for, request, make_response

ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

app = Flask(__name__)
app.secret_key = env.get("APP_SECRET_KEY")

@app.route("/login")
def login():
    return redirect("/")


@app.route("/callback", methods=["GET", "POST"])
def callback():
    return redirect("/")


@app.route("/logout")
def logout():
    return redirect("/")


@app.route("/")
def home():
    return render_template("home.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=env.get("PORT", 3000))
