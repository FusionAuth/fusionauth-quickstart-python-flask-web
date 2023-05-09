# Example Flask Application 

Flaks application using FusionAuth as the identity server. This application will use an OAuth Authorization Code workflow  to log users in.

## Setup FusionAuth

Start up the FusionAuth docker containers:

```shell
docker compose up
```

Login into [FusionAuth](http://localhost:9011/) and create an API key.

Create a virtual environment to install requirements.

```shell
python -m venv venv && \
source venv/bin/activate && \
pip install -r requirements.txt && \
pip install -r setup-flask/requirements.txt
```

Then run the setup script supplying your `<your API key>`.

```shell
fusionauth_api_key=<your API key> python setup.py
```

## Setup Flask

Navigate to the `setup-flask` directory and execute the following command to run your app:

```shell
python server.py
```

Visit the local webserver at `http://localhost:5001/` and sign in.