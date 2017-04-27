from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
import os
import PIL   #pip install Pillow
from PIL import Image
import string
import random

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://alan:songthao@localhost/cookpad'
# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://zgzufrzhgimzwd:0a1552a24673b8998db6be5df4655a18f6fb3e8fdffe2f7e9098765da1e5368f@ec2-54-221-244-196.compute-1.amazonaws.com:5432/dak000ootl4vot?sslmode=require'
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['ALLOWED_EXTENSIONS'] = set(['png', 'jpg', 'jpeg'])
db = SQLAlchemy(app)

def id_generator(size=8, chars=string.ascii_lowercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']


@app.route('/upload/', methods=['POST', 'GET'])
def upload():
    # Get the name of the uploaded file
    username = request.form["username"]
    file = request.files["file"]
    user = db.session.query(Data).filter(Data.username == username).first()
    # Check if the file is one of the allowed types/extensions
    if file and allowed_file(file.filename):

        filename = file.filename
        if len(filename) > 20:
            filename = filename[-20:]
        filename = username + id_generator() + ".jpg"
        user = db.session.query(Data).filter(Data.username == username).first()
        if os.path.exists("uploads/" + user.image) and user.image != "default.jpg":
            os.remove("uploads/" + user.image)
        user.image = filename
        db.session.commit()

        base_height = 400
        img = Image.open(file)
        wpercent = (base_height/float(img.size[1]))
        wsize = int(float(img.size[0]) * wpercent)
        img = img.resize((wsize, base_height), Image.ANTIALIAS)
        # Move the file form the temporal folder to
        # the upload folder we setup
        img.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        # Redirect the user to the uploaded_file route, which
        # will basicaly show on the browser the uploaded file

        src_image = "/uploads/" + user.image
        return render_template("user.html", upload_button = "Replace", text_username=username, src_image = src_image)
        # return redirect(url_for('uploaded_file', filename=filename))
    src_image = "/uploads/" + user.image
    return render_template("user.html", upload_button = "Replace", src_image = src_image, text_username = username, text_upload_error = "Error! Only accept PNG, JPG, JPEG files.")

# This route is expecting a parameter containing the name
# of a file. Then it will locate that file on the upload
# directory and show it on the browser, so if the user uploads
# an image, that image is going to be show after the upload
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/delete/', methods=['POST', 'GET'])
def delete():
    username = request.form["username"]
    user = db.session.query(Data).filter(Data.username == username).first()
    if user.image == "default.jpg":
        return render_template('user.html', upload_button = "Upload", src_image = "/uploads/default.jpg",
                               text_username=username, text_delete_error = "Opps! There is not image to delete.")
    user.image = "default.jpg"
    db.session.commit()
    src_image = "/uploads/" + user.image
    return render_template("user.html", upload_button="Upload", text_username=username, src_image=src_image)

class Data(db.Model):
    __tablename__ = "data"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(40), unique=True)
    password = db.Column(db.String(40))
    image = db.Column(db.String(40))

    def __init__(self, username, password, image):
        self.username = username
        self.password = password
        self.image = image

@app.route('/', methods=["GET","POST"])
def homepage():
    return render_template("main.html")

@app.route('/login/')
def login():
    return render_template("login.html")


@app.route('/login_result/', methods=["POST", "GET"])
def login_result():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if len(username) < 1:
            return render_template("login.html", text="Something is wrong. Try again!")

        if db.session.query(Data).filter(Data.username == username).count() == 0:
            return render_template("login.html")

        user = db.session.query(Data).filter(Data.username == username).first()

        if user.password != password:
            return render_template("login.html", text = "Wrong password. Try again!")


        if user.image == "default.jpg":
            upload_button = "Upload"
        else:
            upload_button = "Replace"
        src_image = "/uploads/" + user.image


        return render_template("user.html", upload_button = upload_button, text_username = username, src_image = src_image)

    return render_template("login.html", text="Something is wrong. Try again!")






@app.route('/signup/')
def signup():
    return render_template("signup.html")


@app.route('/signup_result/', methods=["POST", 'GET'])
def signup_result():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        psw_repeat = request.form["psw_repeat"]
        if password != psw_repeat:
            return render_template("signup.html", text="Oops!!! Two passwords do not match.")

        if db.session.query(Data).filter(Data.username == username).count() == 0:
            data = Data(username, password, "default.jpg")
            db.session.add(data)
            db.session.commit()
            return render_template("user.html", upload_button = "Upload", text_username = username, src_image = "/uploads/default.jpg")

    return render_template("signup.html", text="This username has taken. Please try another!")




if __name__ == "__main__":
    app.run(debug=True)