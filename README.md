# Example Flask Application 

Flaks application using FusionAuth as the identity server. This application will use an OAuth Authorization Code workflow  to log users in.

First create a virtual environment 

```shell
python -m venv venv && \
source venv/bin/activate && \
pip install -r requirements.txt && \
pip install -r setup-flask/requirements.txt
```

Navigate to the `setup-flask` directory and execute `flask run` to run the app.

```shell
flask --app server.py run
```

Visit the local webserver at `http://localhost:5000/` and sign in.