from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from datetime import timedelta
from flask import session, app

app = Flask(__name__)
app.config['SECRET_KEY'] = '82d4a58e933d7ae2463b9fc1486a15e5'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hms.db'

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'


@app.before_request
def make_session_permanent():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=60)


from HMS import routes
