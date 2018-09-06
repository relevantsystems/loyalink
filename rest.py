import os
from flask import Flask, abort, request, jsonify, g, url_for,render_template
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from flask_httpauth import HTTPBasicAuth
# from auth import *
from itsdangerous import (TimedJSONWebSignatureSerializer
                          as Serializer, BadSignature, SignatureExpired)
from passlib.apps import custom_app_context as pwd_context

from flask_restful import Api, Resource
from webargs import fields, validate
from webargs.flaskparser import use_args, use_kwargs, parser, abort
from datetime import date

# initialization
app = Flask(__name__)
api = Api(app)
app.config['SECRET_KEY'] = 'the quick brown fox jumps over the lazy dog'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

# extensions
db = SQLAlchemy(app)
auth = HTTPBasicAuth()
# engine = create_engine('sqlite:///db.sqlite')
# Session=sessionmaker()
# Session.configure(bind=engine)
#
# session = Session()


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

# class Calendar(db.Model):
#     __tablename__ = 'calendar';
#     year = db.Column(db.Integer)
#     month = db.Column(db.Integer)
#     day = db.Column(db.Integer)


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


####################################################################################

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


#end point for calendar booking
@app.route('/api/bookappointment/', methods=['POST'])
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

# when pressed next month on calendar  # AJAX request
@app.route('/api/getappointment/<int:artist_id>')
#@auth.login_required
def new_date(artist_id):
    #try:
        args = request.args
        print(args)  # For debugging
        #booking_date = request.json.get('date')  # date in iso format
        booking_date = '3/21/2018 10:00'
        # month = request.json.get('month)')
        #artist_id =  request.json.get('artist_id')
        # booking_date = date(year=year,)
        # exists = Appointment.query.(db.exists().where(year==year and month==month and artist))
    #http://www.leeladharan.com/sqlalchemy-query-with-or-and-like-common-filters
        lAppointments = db.session.query(Appointment).filter(Appointment.booking_time.like('3/21/2018 10%'))

        for appointment in lAppointments:
            print (appointment.booking_time)

        available_appointments = []
        if exists == False:
            month_end = days_in_month(month,year)
            for i in range(1,month_end):
                available_appointments.append(8);
        return jsonify(available_appointments)
    #except Exception as e:
    #    print(e)


# A function to determine if a year is a leap year.
# Do not change this function.
def is_leap_year(year):
    return (year % 4 == 0) and (year % 100 != 0) or (year % 400 == 0)

# You should complete the definition of this function:

def days_in_month(month, year):

    if month in ['September', 'April', 'June', 'November']:
        return 30

    elif month in ['January', 'March', 'May', 'July', 'August','October','December']:
        return 31

    elif month == 'February' and is_leap_year(year) == True:
        return 29

    elif month == 'February' and is_leap_year(year) == False:
        return 28
    else:
        return None


# class GetAppointmentsResource(Resource):
#
#     dateadd_args = {
#         "artist_id": fields.Int(required=True, validate=validate.Range(min=1)),
#         "date": fields.Str(
#             missing="days", validate=validate.OneOf(["minutes", "days"])
#         ),
#     }
#
#     @use_args(dateadd_args)
#     def get(self, args):
#         return {"message": "Welcome, {}!".format(args["name"])}
#     @use_kwargs(dateadd_args)
#     # def post(self, value, addend, unit):
#     #     """A date adder endpoint."""
#     #     value = value or dt.datetime.utcnow()
#     #     if unit == "minutes":
#     #         delta = dt.timedelta(minutes=addend)
#     #     else:
#     #         delta = dt.timedelta(days=addend)
#     #     result = value + delta
#     #     return {"result": result.isoformat()}
#
#
# # This error handler is necessary for usage with Flask-RESTful
# @parser.error_handler
# def handle_request_parsing_error(err, req):
#     """webargs error handler that uses Flask-RESTful's abort function to return
#     a JSON error response to the client.
#     """
#     abort(422, errors=err.messages)

if __name__ == '__main__':
    if not os.path.exists('db.sqlite'):
        db.create_all()

    # api.add_resource(GetAppointmentsResource, "/api/getappointment")
    app.run(debug=True)