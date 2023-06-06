# Integrate Your Python Flask Application with FusionAuth
This Quickstart will take you through integrating a Python Flask application with FusionAuth, 
setting up an OAuth authorization code grant flow and allowing users to log into your 
application.

In this Quickstart you'll create an application that has
* A Home Page, which is where a logged-out user goes. It has a login button that allows a user to log in
  using FusionAuth
* An Account Page, which is where a user goes when they're logged in. It has a Logout button that allows
  the user to log out with FusionAuth
* The associated back end routes to accomplish all of this

This quickstart will be referencing the example application in [this Git repo](https://github.com/FusionAuth/fusionauth-example-python-flask-guide).
You can build your Flask application from scratch, or you can start with the stub application that we've provided.

#### Repository Contents
| Item | Description |
| --- | --- |
| /quickstart.md | This file that you're reading |
| /docker-compose.yml | A docker-compose config file for standing up a FusionAuth server, a Postgres database, and an Elastic instance |
| /kickstart/ | A directory containing a `kickstart` file, which is used to configure FusionAuth |
| /stub-application/ | A base application that goes with this Quickstart. It runs, but doesn't integrate with FusionAutn (yet) |
| /complete-application/ | A completed application, with a working integration with FusionAuth |

## Prerequisites
For this Quickstart, you'll need Python3.8 or later.

You'll also need Docker, since that's how we'll be running FusionAuth.

The commands below are for macOS, but are limited to basic *nix commands.

## Run FusionAuth
To start FusionAuth, use docker-compose

```shell
git clone https://github.com/FusionAuth/fusionauth-quickstart-python-flask-web
cd fusionauth-quickstart-python-flask-web
docker-compose up -d
```

This will start three containers, once each for FusionAuth, Postgres, and Elastic. 

The FusionAuth configuration files also make use of a unique feature of FusionAuth, called Kickstart: 
when FusionAuth comes up for the first time, it will look at the Kickstart file and mimic API calls to 
configure FusionAuth for use when it is first run. The Kickstart will set up (among other things):
* An Application and somme associated config including that for OAuth, user registration, and more
* CORS configuration to allow requests from localhost:5000 (your app)
* A couple of users: admin@example.com and richard@example.com

> NOTE: If you ever want to reset the FusionAuth system, delete the volumes created by docker-compose by 
> executing docker-compose down -v.
 
FusionAuth will be configured with these settings
* Your client Id is: `e9fdb985-9173-4e01-9d73-ac2d60d1dc8e`
* Your client secret is: `super-secret-secret-that-should-be-regenerated-for-production`
* Your example username is `richard@example.com` and your password is `password`
* Your admin username is `admin@example.com` and your password is `password`
* The FusionAuth API is hosted at `http://localhost:9011/`

You can log into the [FusionAuth admin UI](http://localhost:9011/admin) and look around if you want, but with Docker/Kickstart you don’t need to.

## Create a Basic Flask Application
If you're using the provided stub application, you can skip this section.

#### Setup Your Environment
We recommend working in a virtual environment for this.

```shell
python3.8 -m venv venv
source venv/bin/activate
```

Next, create a requirements.txt file.

```shell
# requirements.txt
Authlib==1.2.0
Flask==2.3.2
requests==2.31.0
```

And install the dependencies.

```shell
pip install -r requirements.txt
```

#### Create the Application
Now create your Flask app. Create a file named server.py, with the following code in it. 
This application has a single route defined for the application home page at `/`.

You'll add all the imports you need now, and also declare some constants that you'll use later.
Remember that the CLIENT_ID and CLIENT_SECRET values are from FusionAuth.

`server.py`
```python
import json
from os import environ as env
from urllib.parse import quote_plus, urlencode
from authlib.integrations.flask_client import OAuth
from flask import Flask, redirect, render_template, session, url_for, request, make_response

# Names for some cookies
ACCESS_TOKEN_COOKIE_NAME = "cb_access_token"
REFRESH_TOKEN_COOKIE_NAME = "cb_refresh_token"
USERINFO_COOKIE_NAME = "cb_userinfo"

# This is needed by Flask, and can be any string
APP_SECRET_KEY = "0386ffa9-3bff-4c75-932a-48d6a763ce77"

# FusionAuth Information
CLIENT_ID = "e9fdb985-9173-4e01-9d73-ac2d60d1dc8e"
CLIENT_SECRET = "super-secret-secret-that-should-be-regenerated-for-production"
ISSUER = "http://localhost:9011"

app = Flask(__name__)
app.secret_key = APP_SECRET_KEY

@app.route("/")
def home():
    return render_template("home.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
```

#### Create a Home Page
This home page just has a login link, which won't do anything yet. If you want
to see a more complete example, check out the home page in the stub application.

`templates/home.html`
```html
<html>
  <body>
    <div style="font-size: 24px; margin-bottom: 20px;">Welcome to Changebank, please login.</div>
    <a href="/login">Login</a>
  </body>
</html>
```

At this point, you should be able to run your application with the following command, and visit the home page at 
`http://localhost:5000`.

```shell
flask --app server.py --debug run
```

## Configure authlib
We'll be using authlib as an OAuth/OpenID Connect (OIDC) client. Import the OAuth class, create an instance, and
configure it by calling OAuth.register. Add this to the end of `server.py`.

```python
oauth = OAuth(app)

oauth.register(
    "FusionAuth",
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    client_kwargs={
        "scope": "openid offline_access",
        'code_challenge_method': 'S256' # This enables PKCE
    },
    server_metadata_url=f'{ISSUER}/.well-known/openid-configuration'
)
```

## Add OAuth Authentication Routes
Next, you'll add a `/login` route that uses authlib to take the user to FusionAuth's OAuth2 `authorize` endpoint, 
and a `/callback` route that FusionAuth will redirect the user back to after a successful login.

FusionAuth will include an authorization code in the redirect to `/callback`, and the callback function will 
call back to FusionAuth to exchange the authorization code for an access token, refresh token, and userinfo 
object. All of this happens in `oauth.FusionAuth.authorize_access_token()`.

We then write the returned values to HTTP-only cookies, so that they will be returned to the 
Flask application on subsequent requests, but are not readable by code running in the browser.

We also set the userinfo object in the Flask session, to make it easy to use in rendered templates.

```python
@app.route("/login")
def login():
    return oauth.FusionAuth.authorize_redirect(
        redirect_uri=url_for("callback", _external=True)
    )


@app.route("/callback", methods=["GET"])
def callback():
    token = oauth.FusionAuth.authorize_access_token()

    resp = make_response(redirect("/"))

    resp.set_cookie(ACCESS_TOKEN_COOKIE_NAME, token["access_token"], max_age=token["expires_in"], httponly=True, samesite="Lax")
    resp.set_cookie(REFRESH_TOKEN_COOKIE_NAME, token["refresh_token"], max_age=token["expires_in"], httponly=True, samesite="Lax")
    resp.set_cookie(USERINFO_COOKIE_NAME, json.dumps(token["userinfo"]), max_age=token["expires_in"], httponly=True, samesite="Lax")
    session["user"] = token["userinfo"]

    return resp
```

Once this is done, you should be able to successfully log into your application! 

### Secured Page
After logging in, the application redirects the user to `/`, which just shows the initial login
page. Not very useful. Let's make the `/` route more useful, by adding some logic to render a different
page if the user is logged in.

First, let's create the page templage for a logged-in user. All it's going to do is show a personalized
greeting and a logout link. For a richer example, check out the application in the `/complete-application` directory.

Create an `templates/account.html` page, which will represent the view a user would see if they
logged in at their bank.

```shell
cat > templates/account.html <<EOF
<html>
  <body>
    <div style="font-size: 24px; margin-bottom: 20px;">Hello, {{session["email"]}}!</div>
    <a href="{{logoutUrl}}">Logout</a>
  </body>
</html>
```

Next, create a route to get to that page. This checks if an access token is present.
If one isn't, it forces a logout at FusionAuth. If one is, it renders the `/account` page.
In a real application, we would validate the token, check to make sure it isn't expired,
and attempt to refresh it if if were valid but expired. 

```python
@app.route("/account")
def account():
    access_token = request.cookies.get(ACCESS_TOKEN_COOKIE_NAME, None)

    if access_token is None:
      return redirect(get_logout_url())

    return render_template(
        "account.html",
        session=json.loads(request.cookies.get(USERINFO_COOKIE_NAME, None)),
        logoutUrl=ISSUER + "/oauth2/logout?" + urlencode({"client_id": CLIENT_ID},quote_via=quote_plus))
```

Finally, replace the `/` route with a more useful function.
```python
@app.route("/")
def home():
    logout = ISSUER + "/oauth2/logout?" + urlencode({"client_id": CLIENT_ID},quote_via=quote_plus)

    if request.cookies.get(ACCESS_TOKEN_COOKIE_NAME, None) is not None:
      # In a real application, we would validate the token signature and expiration
      return redirect("/account")

    return render_template("home.html")
```

Now when you log in, you should see the `/account` page!

### Logout
The last step is to implement logout. When you log a user out of an application, you take them to 
FusionAuth's `/oauth2/logout` endpoint. After logging the user out, FusionAuth will redirect the user
to the `/login` endpoint, which you'll create now. This endpoint deletes any cookies that your
application created, and clears the Flask session.

```python
@app.route("/logout")
def logout():
    session.clear()

    resp = make_response(redirect("/"))

    response.delete_cookie(ACCESS_TOKEN_COOKIE_NAME)
    response.delete_cookie(REFRESH_TOKEN_COOKIE_NAME)
    response.delete_cookie(USERINFO_COOKIE_NAME)

    return resp
```
Now when you log out, you'll first be taken to FusionAuth, then back to your `/logout` endpoint to clear out the session
and all of the auth cookies, and finally back to the home page.