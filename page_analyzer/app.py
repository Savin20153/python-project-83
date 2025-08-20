import os
from flask import Flask
from dotenv import load_dotenv

load_dotenv()  # загружает переменные из .env

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')


@app.route("/")
def index():
    return "<a href='/ci'>Main</a>"