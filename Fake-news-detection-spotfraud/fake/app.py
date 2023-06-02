#Importing the Libraries
import pathlib
import numpy as np
from requests import Session
from flask import Flask, abort, redirect, request,render_template, session
from flask_cors import CORS
import os
import pickle
import os
from newspaper import Article
import urllib
from google_auth_oauthlib.flow import Flow
from google.oauth2 import id_token
from pip._vendor import cachecontrol
import google.auth.transport.requests


#Loading Flask and assigning the model variable
app = Flask(_name_)
CORS(app)
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

app.secret_key = 'spotfraudsecret'
GOOGLE_CLIENT_ID = "760986431265-2fc7vlhigm545luev27evh2irn3d2cfs.apps.googleusercontent.com"
client_secret_file = os.path.join(pathlib.Path(_file_).parent, "client_secret.json")

flow = Flow.from_client_secrets_file(
     client_secrets_file=client_secret_file,
     scopes=["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email", "openid"],
     redirect_uri="http://127.0.0.1:5000/callback")

#to protect our page with a decorator
def login_required(function):
    def wrapper(*args, **kwargs):
        if "google_id" in session and "name" in session:
            return function(*args, **kwargs)
        else:
            return abort(401)  # Unauthorized
    return wrapper

#To redirect our user
@app.route("/login")
def login():
     authorization_url, state = flow.authorization_url()
     session["state"] = state
     return redirect(authorization_url)

#to receive data from google 
@app.route("/callback")
def callback():
     flow.fetch_token(authorization_response=request.url)
     if not session["state"] == request.args["state"]:
          abort(500) # State does not match!
     credentials = flow.credentials
     token_request = google.auth.transport.requests.Request()
     id_info = id_token.verify_oauth2_token(
        id_token=credentials._id_token,
        request=token_request,
        audience=GOOGLE_CLIENT_ID
    )
     session["google_id"] = id_info.get("sub")
     session["name"] = id_info.get("name")
     return redirect("/home")

@app.route("/logout")
def logout():
     session.clear()
     return redirect("/")

@app.route("/")
def index():
     return render_template('login.html')

#Replace the path with your own path:
with open('C:/Users/Calina/Downloads/Fake-news-detection-spotfraud/fake/model.pickle', 'rb') as handle:
	model = pickle.load(handle)

@app.route('/home')
@login_required
def main():
    return render_template('main.html') 

#Receiving the input url from the user and using Web Scrapping to extract the news content
@app.route('/predict',methods=['GET','POST'])
def predict():
    url =request.get_data(as_text=True)[5:]
    url = urllib.parse.unquote(url)
    article = Article(str(url))
    article.download()
    article.parse()
    article.nlp()
    news = article.summary
    #Passing the news article to the model and returing whether it is Fake or Real
    pred = model.predict([news])
    return render_template('main.html', prediction_text='The news is "{}"'.format(pred[0]))
    
if _name__=="__main_":
    port=int(os.environ.get('PORT',5000))
    app.run(port=port,debug=True,use_reloader=False)
