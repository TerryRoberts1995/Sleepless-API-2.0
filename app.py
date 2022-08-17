from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_cors import CORS
from flask_bcrypt import Bcrypt

import os

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(basedir, "app.sqlite")
db = SQLAlchemy(app)
ma = Marshmallow(app)
bcrypt = Bcrypt(app)
CORS(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), unique=True, nullable=False)
    password = db.Column(db.String(30), nullable=False)
    images = db.relationship('Image', backref='user', cascade='all, delete, delete-orphan')

    def __init__(self, username, password):
        self.username = username
        self.password = password


class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String, nullable=False)
    name = db.Column(db.String, nullable=False)
    user_fk = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    def __init__(self, url, name, user_fk):
        self.url = url 
        self.name = name
        self.user_fk = user_fk

class ImageSchema(ma.Schema):
    class Meta:
        fields = ("id", "url", "name", "user_fk")

image_schema = ImageSchema()
multiple_image_schema = ImageSchema(many=True)

class UserSchema(ma.Schema):
    class Meta:
        fields = ('id', 'username', 'password', 'images')
    images = ma.Nested(multiple_image_schema)

user_schema = UserSchema()
multiple_user_schema = UserSchema(many=True)

# Food Endpoints

@app.route("/image/add", methods=["POST"])
def add_images():
    post_data = request.get_json()
    url = post_data.get("url")
    name = post_data.get("name")
    user_fk = post_data.get("user_fk")

    new_record = Image(url, name, user_fk)
    db.session.add(new_record)
    db.session.commit()

    return jsonify("image item added successfully")

@app.route("/images", methods=["GET"])
def get_all_images():
    records = db.session.query(Image).all()
    return jsonify(multiple_image_schema.dump(records))

@app.route("/image/<id>", methods=['GET'])
def get_image_by_id(id):
    record = db.session.query(Image).filter(Image.id == id).first()
    return jsonify(image_schema.dump(record))

# User Endpoints

@app.route('/user/add', methods=['POST'])
def add_user():
    post_data = request.get_json()
    username = post_data.get('username')
    password = post_data.get('password')
    user = db.session.query(User).filter(User.username == username).first()

    if user is not None:
        return jsonify('Error: You must use another name. That one is taken!')

    encrypted_password = bcrypt.generate_password_hash(password).decode('utf-8')
    new_user = User(username, encrypted_password)
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify('You have created a user! Welcome to our site!')

@app.route('/user/get/<id>', methods=['GET'])
def get_user(id):
    user = db.session.query(User).filter(User.id == id).first()
    return jsonify(user_schema.dump(user))

if __name__ == "__main__":
    app.run(debug=True)