import requests
from flask import Flask
app = Flask(__name__)

@app.route('/')
def hello_world():
    r = requests.get("https://www.baidu.com/")
    return 'Hello, World!'
