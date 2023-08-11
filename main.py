import cv2
import numpy as np
import os
from skimage import io
import requests
from PIL import Image
import matplotlib.pyplot as plt
from flask import Flask,send_from_directory, render_template, request, session,url_for
from flask_mysqldb import MySQL
from flask_uploads import UploadSet,IMAGES,configure_uploads
from flask_wtf import FlaskForm
from flask_wtf.file import FileField,FileRequired,FileAllowed
from sqlalchemy import true
from wtforms import SubmitField
import MySQLdb.cursors
import re
from keras.models import load_model
app = Flask(__name__)
saved_model = load_model("model_ver1 .h5")
app.secret_key = 'your secret key'
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'gp'
mysql = MySQL(app)

app.config['UPLOADED_PHOTOS_DEST']='GPP'
photos=UploadSet('photos',IMAGES)
configure_uploads(app,photos)
class UploadForm(FlaskForm):
    photo=FileField(
        validators=[
            FileAllowed(photos,'Only images are allowed'),
            FileRequired('File field should not be empty')
        ]
    )
    submit=SubmitField('Upload')

@app.route("/")
@app.route('/login', methods =['GET', 'POST'])
def login():
    # Output message if something goes wrong...
    msg = ''
    # Check if "username" and "password" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
    # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE username = %s AND password = %s', (username, password,))
        # Fetch one record and return result
        account = cursor.fetchone()
            # If account exists in accounts table in out database
        if account:
            # Create session data, we can access this data in other routes
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']
            # Redirect to home page
            return render_template('index.html')
        else:
            # Account doesn't exist or username/password incorrect
            msg = 'Incorrect username/password!'
    return render_template('Login.html', msg = msg)

@app.route('/Home')
def home():
        return render_template("index.html")

@app.route('/Login.html')
def homes():
        return render_template("Login.html")

@app.route("/Register.html",methods=['GET', 'POST'])
def register():
    # Output message if something goes wrong...
    msg = ''
    # Check if "username", "password" and "email" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
                # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        account = cursor.fetchone()
        # If account exists show error and validation checks
        if account:
            msg = 'Account already exists!'
        elif not re.match(r'[^@]+@[^@]+.[^@]+', email):
            msg = 'Invalid email address!'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers!'
        elif not username or not password or not email:
            msg = 'Please fill out the form!'
        else:
            # Account doesn't exist and the form data is valid, now insert new account into accounts table
            cursor.execute('INSERT INTO users VALUES (NULL, %s, %s, %s)', (username, email,password,))
            mysql.connection.commit()
            msg = 'You have successfully registered!... You Can Login Now'
            return render_template('Login.html',msg=msg)
    elif request.method == 'POST':
        # Form is empty... (no POST data)
        msg = 'Please fill out the form!'
    # Show registration form with message (if any)
    return render_template('Register.html', msg=msg)
@app.route('/GPP/<filename>')
def get_file(filename):
    return send_from_directory(app.config['UPLOADED_PHOTOS_DEST'],filename)
@app.route('/Services', methods =['GET', 'POST'])
def upload_image():
    form = UploadForm()
    if form.validate_on_submit():
        filename=photos.save(form.photo.data)
        file_url=url_for('get_file',filename=filename)
    else:
        file_url=None
    return render_template('services.html',form=form,file_url=file_url)

@app.route("/result", methods=["POST"])
def Model():
    img = request.files['img']
    img.save("img.jpg")
    image = cv2.imread("img.jpg")
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    plt.imshow(image)
    plt.show()
    image = cv2.resize(image, (150, 150))
    image = np.reshape(image, (1, 150, 150, 3))
    Prediction = saved_model.predict(image)
    # Normal (N),Diabetes (D),Glaucoma (G),Cataract (C),Age related Macular Degeneration (A),Hypertension (H),Pathological Myopia (M)
    out_list = ['Cataract (C)', 'Glaucoma (G)', 'Pathological Myopia (M)', 'Age related Macular Degeneration (A)',
				'Hypertension (H)', 'Normal (N)']
    var = np.argmax(Prediction[0])
    d_name = out_list[var]
    return render_template("result.html", data=d_name)

@app.route('/Homes', methods=["POST"])
def index():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)