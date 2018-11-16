from flask_uploads import UploadSet, IMAGES
from flask import json, jsonify, Flask, render_template, flash, redirect, url_for, session, logging, request, send_file
from flask_mysqldb import MySQL
from wtforms import Form, SelectField, FileField, DecimalField, IntegerField, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps
import MySQLdb
from werkzeug.utils import secure_filename
from flask_wtf.file import FileField, FileRequired, FileAllowed
import os
import xlsxwriter
from PIL import Image

app = Flask(__name__, static_folder="photos", instance_path="/Users/home/Project/py/BrotherShip/exceldata")


#config mysql
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'dltkdals'
app.config['MYSQL_DB'] = 'myflaskapp'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
#init mysql
mysql = MySQL(app)

@app.route('/')
def index():
    return render_template('home.html')

class RegisterForm(Form):
    name = StringField('Name', [
        validators.DataRequired(),
        validators.Length(min=1, max=50)
    ])
    username = StringField('Username', [
        validators.DataRequired(),
        validators.Length(min=4, max=25)
    ])
    email = StringField('Email', [
        validators.DataRequired(),
        validators.Length(min=6, max=50)
    ])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])
    confirm = PasswordField('Confirm Password')
    phoneNumber = StringField('Phone Number', [validators.Length(max=10)])
    company = StringField('Name of Company')

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        session['usertype'] = request.form['usertype']
        if session['usertype'] == 'seller':
            name = form.name.data
            email = form.email.data
            username = form.username.data
            password = sha256_crypt.encrypt(str(form.password.data))
            phoneNumber = form.phoneNumber.data
            company = form.company.data
            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO users(name, email, username, password, phone_number, company, usertype) VALUES(%s, %s, %s, %s, %s, %s, %s)",(name, email, username, password, phoneNumber, company, session['usertype']))
        else:
            name = form.name.data
            email = form.email.data
            username = form.username.data
            password = sha256_crypt.encrypt(str(form.password.data))
            phoneNumber = form.phoneNumber.data
            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO users(name, email, username, password, phone_number, usertype) VALUES(%s, %s, %s, %s, %s, %s)",(name, email, username, password, phoneNumber, session['usertype']))
        try:
            #committ to db
            mysql.connection.commit()
            #close connection
            cur.close()
            flash('Welcome %s' % name, 'success')
            return redirect(url_for('index'))
        except MySQLdb.IntegrityError as e:
            flash("Username already exists", 'danger')
            return render_template('register.html', form=form)
    return render_template('register.html', form=form)

#User Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        #get form fields
        username = request.form['username']
        password_candidate = request.form['password']
        #create cursor
        cur = mysql.connection.cursor()
        #get user by username
        result = cur.execute('SELECT * FROM users WHERE username = %s', [username])
        if result > 0:
            data = cur.fetchone()
            password = data['password']
            #compare Passwords
            if sha256_crypt.verify(password_candidate, password):
                #passed
                session['Logged_in'] = True
                session['username'] = username
                session['usertype'] = data['usertype']
                flash('You are now logged in', 'success')
                return redirect(url_for('index'))
            else:
                error = 'Wrong password'
                return render_template('login.html', error=error)
            #close db connection
            cur.close()
        else:
            error = 'Username not found'
            return render_template('login.html', error=error)
    return render_template('login.html')

#logout
@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.clear()
    flash('Logged out', 'success')
    return redirect(url_for('index'))

#make login requirement
def loginFirst(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'Logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, please login first', 'danger')
            return redirect(url_for('login'))
    return wrap

def isSeller(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if session['usertype'] == 'seller':
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, must be a seller to perform action', 'danger')
            return redirect(url_for('index'))
    return wrap

@app.route('/packagename', methods=['GET','POST'])
@loginFirst
@isSeller
def fileChus():
    cur = mysql.connection.cursor()
    cur.execute('SELECT DISTINCT package FROM products WHERE username=%s', [session['username']])
    datas = cur.fetchall()
    cur.close()
    if request.method == 'POST':
        if request.form['dropdown'] == 'Other':
            seasonFilename = request.form['packagename']
            if(seasonFilename == ""):
                flash("Cannot submit an empty form", "danger")
                return render_template("season.html", datas=datas)
            session['seasonF'] = seasonFilename
            return redirect(url_for('upload'))
        elif request.form['dropdown'] == "none":
            flash("Error in Selection, Try again", "danger")
            return render_template("season.html", datas=datas)
        else:
            seasonFilename = request.form['dropdown']
            session['seasonF'] = seasonFilename
            return redirect(url_for('upload'))
    return render_template("season.html", datas=datas)

class ProductForm(Form):
    productId = StringField('Product ID', [
        validators.DataRequired(),
        validators.Length(min=1)
    ])
    productName = StringField('Name')
    category = StringField('Category')
    color = StringField('Color')
    material = StringField('Material')
    origin = StringField('Origin')
    price = DecimalField('Price', places=2, default=0)
    quantity = IntegerField('Quantity', default=0)
    photo = FileField('Photo', validators=[
        FileAllowed(['jpg', 'png', 'jpeg', 'gif'], 'Images only!')
    ])

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowedExtensions
#product registration
@app.route('/upload', methods=['GET', 'POST'])
@loginFirst
@isSeller
def upload():
    form = ProductForm(request.form)
    if request.method == 'POST' and form.validate():
        filename = request.files.getlist('file')
        for f in filename:
            file_name = secure_filename(f.filename)
            image_file = os.path.join('/Users/home/Project/py/BrotherShip/photos/', file_name)
            f.save(image_file)
        productId = form.productId.data
        productName = form.productName.data
        category = form.category.data
        color = form.color.data
        material = form.material.data
        origin = form.origin.data
        price = form.price.data
        quantity = form.quantity.data
        totalamount = price * quantity
        username = session['username']
        packagename = session['seasonF']
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO products(productID, productName, category, color, material, origin, price, quantity, totalamount, username, picture, package) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",(productId, productName, category, color, material, origin, price, quantity, totalamount, username, file_name, packagename))
        #committ to db
        mysql.connection.commit()
        #close connection
        cur.close()
        session['productID'] = productId
        if request.form['submit'] == 'Continue Registering':
            flash('upload succesful', 'success')
            return redirect(url_for('upload'))
        else:
            flash('upload succesful', 'success')
            return redirect(url_for('index'))
    return render_template('upload.html', form=form)

@app.route('/upload/complete', methods=['GET','POST'])
@loginFirst
@isSeller
def complete():
    cur = mysql.connection.cursor()
    cur.execute("SELECT DISTINCT package FROM products WHERE username=%s",[session['username']])
    packages = list(cur.fetchall())
    if request.method == 'POST':
        editFile = "%s_%s.xlsx" % (session['username'], request.form['dropdown'])
        print(request.form['dropdown'])
        if os.path.exists('exceldata/%s' % editFile):
            os.remove('exceldata/%s' % editFile)
        workbook = xlsxwriter.Workbook('exceldata/%s' % editFile)
        worksheet = workbook.add_worksheet()
        if request.form['dropdown'] != 'All':
            cur.execute("SELECT * FROM products WHERE username=%s AND package=%s",(session['username'], request.form['dropdown']))
            datas = list(cur.fetchall())
            cur.close()
        else:
            cur.execute("SELECT * FROM products WHERE username=%s",[session['username']])
            datas = list(cur.fetchall())
            cur.close()
        row = 0
        col = 0
        titlelist = ['picture', 'productID', 'productName', 'category', 'color', 'material', 'origin', 'price', 'quantity', 'totalamount']
        while row == 0:
            worksheet.write(row, col, titlelist[col])
            col = col + 1
            if col == len(titlelist):
                row = row + 1
                col = 0
        worksheet.set_column(col, col, 80)
        for data in datas:
            col = 0
            image = 'photos/%s' % data['picture']
            with Image.open(image) as img:
                width, height = img.size
                worksheet.set_row(row, int(height*0.5))
                worksheet.insert_image(row, col, '%s' % image, {'x_scale': 0.5, 'y_scale': 0.5})
            col += 1
            for i in range(1,len(titlelist)):
                worksheet.write(row, col, data[titlelist[i]])
                col += 1
            row += 1
        workbook.close()
        session['filename'] = editFile
        return redirect(url_for('download'))
    return render_template('complete.html', packages=packages)

@app.route('/download', methods=['GET', 'POST'])
@loginFirst
@isSeller
def download():
    datefile = session['filename']
    return send_file(os.path.join(app.instance_path, datefile), attachment_filename='%s' % datefile, as_attachment=True)

@app.route('/list', methods=['GET', 'POST'])
@loginFirst
def plist():
    cur = mysql.connection.cursor()

    #list to be used for sellers
    cur.execute("SELECT DISTINCT package FROM products WHERE username=%s",[session['username']])
    seasons = cur.fetchall()
    cur.execute("SELECT DISTINCT category FROM products WHERE username=%s",[session['username']])
    sellCat = cur.fetchall()
    cur.execute("SELECT * FROM products WHERE username=%s",[session['username']])
    datas = cur.fetchall()

    #list to be used for buyers
    cur.execute("SELECT DISTINCT company FROM users WHERE usertype='seller'")
    users = cur.fetchall()
    cur.execute("SELECT DISTINCT category FROM products")
    categories = cur.fetchall()
    cur.execute("SELECT products.picture, users.company, products.username, products.package, products.productID, products.category, products.color, products.price, products.quantity FROM products JOIN users ON products.username=users.username")
    allDatas = cur.fetchall()

    if request.method == 'POST':
        styleToDelete = request.form['styleToDelete']
        cur.execute("DELETE FROM products WHERE productID=%s",[styleToDelete])
        mysql.connection.commit()
        cur.close()
        flash('Delete Successful', 'success')
        return redirect(url_for('plist'))
    return render_template("productlist.html", sellCat = sellCat, categories=categories, allDatas = allDatas, users = users, datas = datas, seasons = seasons)

@app.route('/modify/edit/<string:productID>', methods=['GET', 'POST'])
@loginFirst
@isSeller
def change(productID):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM products WHERE productID=%s",[productID])
    data = cur.fetchone()
    form = ProductForm()
    form.productId.data= data['productID']
    form.productName.data = data['productName']
    form.category.data = data['category']
    form.color.data = data['color']
    form.material.data = data['material']
    form.origin.data = data['origin']
    form.price.data = data['price']
    form.quantity.data = data['quantity']
    if request.method == 'POST' and form.validate():
        if request.form['submit'] == 'Yes':
            filename = request.files.getlist('photo')
            for f in filename:
                file_name = secure_filename(f.filename)
                image_file = os.path.join('/Users/home/Project/py/myflaskapp/photos/', file_name)
                f.save(image_file)
            productId = request.form['productId']
            productName = request.form['productName']
            category = request.form['category']
            color = request.form['color']
            material = request.form['material']
            origin = request.form['origin']
            price = float(request.form['price'])
            quantity = int(request.form['quantity'])
            totalamount = price * quantity
            username = session['username']
            cur.execute("DELETE FROM products WHERE productID=%s", [productId])
            filename = request.files.getlist('file')
            for f in filename:
                file_name = secure_filename(f.filename)
                image_file = os.path.join('/Users/home/Project/py/myflaskapp/photos/', file_name)
                f.save(image_file)
            cur.execute("INSERT INTO products(productID, productName, category, color, material, origin, price, quantity, totalamount, username, picture, package) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",(productId, productName, category, color, material, origin, price, quantity, totalamount, username, file_name, data['package']))
            mysql.connection.commit()
            cur.close()
            flash('Changes Saved', 'success')
            return redirect(url_for('plist'))
        else:
            return redirect(url_for('plist'))
    return render_template("editing.html", form=form)

@app.route('/profile/<string:username>', methods=['GET','POST'])
@loginFirst
def publicProfile(username):
    cur = mysql.connection.cursor()
    cur.execute("SELECT name, email, phone_number, company FROM users WHERE username=%s", [username])
    information = cur.fetchone()
    return render_template("profile.html", information = information)


if __name__ == "__main__":
    app.secret_key='secret123'
    app.run(debug=True)
