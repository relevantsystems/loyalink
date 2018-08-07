import os
from flask import Flask, abort, request, jsonify, g, url_for,render_template
from flask_sqlalchemy import SQLAlchemy
from flask_httpauth import HTTPBasicAuth
# from auth import *
from itsdangerous import (TimedJSONWebSignatureSerializer
                          as Serializer, BadSignature, SignatureExpired)
from passlib.apps import custom_app_context as pwd_context

# initialization
app = Flask(__name__)
app.config['SECRET_KEY'] = 'the quick brown fox jumps over the lazy dog'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True

# extensions
db = SQLAlchemy(app)
auth = HTTPBasicAuth()


class User(db.Model):
    __tablename__ = 'users_new'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, index=True)
    password_hash = db.Column(db.String(128))
    usertype = db.Column(db.Integer, index=True)

    def hash_password(self, password):
        self.password_hash = pwd_context.encrypt(password)

    def verify_password(self, password):
        return pwd_context.verify(password, self.password_hash)

    def generate_auth_token(self, expiration = 600):
        s = Serializer(app.config['SECRET_KEY'], expires_in = expiration)
        return s.dumps({'id': self.id})

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except SignatureExpired:
            return None
        except BadSignature:
            return None
        user = User.query.get(data['id'])
        return user


class Artist(db.Model):
    __tablename__ = 'artists'
    id = db.Column(db.Integer,primary_key=True)  # unique  id for artists
    artist_name = db.Column(db.String, index= True) # artist name
    about = db.Column(db.String)        # about artist


class Appointment(db.Model):
    __tablename__ = 'appointments'
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.String, index=True)
    artist_id = db.Column(db.Integer, index= True)
    booking_time = db.Column(db.String)

# webpage routes


@app.route('/')
def home():
    return render_template('/index.html')


@app.route('/artists')
def artists():
    return render_template('/artists.html')


@app.route('/aboutus')
def aboutus():
    return render_template('/aboutus.html')


@app.route('/faq')
def faq():
    return render_template('/faq.html')


@app.route('/staff')
def staff():
    return render_template('/staff.html')


# api end points
# end point for new user i.e register
@app.route('/api/users', methods=['POST'])
def new_user():
    print(request.json)
    username = request.json.get('username')
    password = request.json.get('password')
    usertype = 1
    if username is None or password is None:
        abort(400)    # missing arguments
    if User.query.filter_by(username=username).first() is not None:
        abort(400)    # existing user
    user = User(username=username,usertype=usertype)
    user.hash_password(password)
    db.session.add(user)
    db.session.commit()
    return (jsonify({'username': user.username}), 201,
            {'Location': url_for('get_user', id=user.id, _external=True)})


# end point to get user name by the id
@app.route('/api/users/<int:id>')
def get_user(id):
    user = User.query.get(id)
    if not user:
        abort(400)
    return jsonify({'username': user.username})


# end point for login
@app.route('/api/existing_user', methods=["POST"])
def existing_user():
    print(request.json)
    username = request.json.get('username')
    password = request.json.get('password')
    if username is None or password is None:
        abort(400)    # missing arguments
    if User.query.filter_by(username=username).first() is None:
        abort(400)  # need to go to register
    user = User.query.filter_by(username=username).first()
    if not user or not user.verify_password(password):
        return False
    g.user = user
    return (jsonify({'username': user.username}), 201,
            {'Location': url_for('get_user', id=user.id, _external=True)})


@app.route('/api/resource')
@auth.login_required
def get_resource():
    return jsonify({'data':'Hello, %s!' % g.user.username})


@auth.verify_password
def verify_password(username_or_token, password):
    user = User.verify_auth_token(username_or_token)
    if not user:
        user = User.query.filter_by(username=username_or_token).first()
        if not user or not user.verify_password(password):
            return False
    g.user = user
    return True


# end point for token based authentication
@app.route('/api/token')
@auth.login_required
def get_auth_token():
    token = g.user.generate_auth_token()
    return jsonify({'token' : token.decode('ascii')})


@app.route('/api/bookappointment', methods=['POST'])
@auth.login_required
def new_appointment():
    customer_id = request.json.get('customer_id')
    artist_id = request.json.get('artist_id')
    booking_time = request.json.get('booking_time')
    if customer_id is None or artist_id is None or booking_time is None:
        abort(400)  # missing arguments
    # if User.query.filter_by(id=user_ id).first() is not None:
    #     abort(400)  # time slot already taken
    appointment = Appointment(customer_id = customer_id, artist_id=artist_id,booking_time=booking_time)
    db.session.add(appointment)
    db.session.commit()
    return (jsonify({'username': g.user.username}), 201,
            {'Location': url_for('get_user', id=g.user.id, _external=True)})


if __name__ == '__main__':
    if not os.path.exists('db.sqlite'):
        db.create_all()

    app.run(debug=True)