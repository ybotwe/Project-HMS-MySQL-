from datetime import datetime
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from HMS import db, login_manager, app
from flask_login import UserMixin


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    firstname = db.Column(db.String(20), nullable=False)
    lastname = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    number = db.Column(db.String(10), unique=True, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    role = db.Column(db.String(10), nullable=False, default="student")
    password = db.Column(db.String(60), nullable=False)
    hostel_id = db.Column(db.Integer, db.ForeignKey('hostels.hostel_id'))
    room_id = db.Column(db.String, db.ForeignKey('rooms.room_num'))
    images = db.relationship('Images', backref='user')
    announcements = db.relationship('Announcement', backref='user')

    def __repr__(self):
        return f"Student('{self.firstname}', '{self.lastname}', '{self.email}')"


class Room(db.Model):
    __tablename__ = "rooms"
    room_num = db.Column(db.String, primary_key=True)
    beds = db.Column(db.String, db.ForeignKey('beds.beds_id'))
    price = db.Column(db.Integer)
    hostel_id = db.Column(db.Integer, db.ForeignKey('hostels.hostel_id'))
    occupants = db.relationship('User', backref='room')
    room_gen = db.Column(db.String, nullable= False)

    def __repr__(self):
        return f"Room('{self.room_num}', '{self.hostel_id}')"


class Beds(db.Model):
    __tablename__ = "beds"
    beds_id = db.Column(db.String, nullable=False, primary_key=True)
    bednum = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Integer, nullable=False)
    hostel_id = db.Column(db.Integer, db.ForeignKey('hostels.hostel_id'))

    def __repr__(self):
        return f"Beds('{self.bednum}', '{self.price}', '{self.hostel_id}')"


class Hostel(db.Model):
    __tablename__ = "hostels"
    hostel_id = db.Column(db.Integer, primary_key=True)
    hostel_name = db.Column(db.String(30), unique=True)
    occupants = db.relationship('User', backref='hostel')
    rooms = db.relationship('Room', backref='hostel')
    beds = db.relationship('Beds', backref='hostel')
    desc = db.Column(db.Text, nullable=False)
    img = db.Column(db.String, nullable=False)

    def __repr__(self):
        return f"Hostel('{self.hostel_id}', '{self.hostel_name}')"


class Payment(db.Model):
    __tablename__ = "payments"
    payment_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    amount_paid = db.Column(db.Integer, nullable=False)
    amount_remaining = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f"Payments('{self.payment_id}', '{self.user_id}', '{self.amount_paid}')"


class Images(db.Model):
    __tablename__ = "images"
    image_id = db.Column(db.Integer, primary_key=True)
    image_file = db.Column(db.String, nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    processed = db.Column(db.String(10), nullable=False, default="False")
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    def __repr__(self):
        return f"Images('{self.image_id}', '{self.date_posted}', '{self.processed}')"


class Announcement(db.Model):
    __tablename__ = "announcements"
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(100), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    message = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    def __repr__(self):
        return f"Announcements('{self.subject}', '{self.date_posted}')"
