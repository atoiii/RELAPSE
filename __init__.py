import shelve
import os
import re
from flask import Flask, render_template, request, redirect, url_for
from PIL import Image

import Product
from createproduct import CreateProduct

app = Flask(__name__)

# folder for product images
base_directory = os.path.abspath(os.path.dirname(__file__))
upload_folder = os.path.join(base_directory, 'uploads_products')
extensions = {'png', 'jpg', 'jpeg'}
width = 300
height = 300

app.config['UPLOAD_FOLDER'] = upload_folder


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in extensions


def secure_filename(filename):
    filename = re.sub(r'[^a-zA-Z0-9_.-]', '_', filename)
    return filename


def resize_image(image, max_width, max_height):
    img = Image.open(image)
    img.thumbnail((max_width, max_height))
    return img


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/createProduct', methods=['GET', 'POST'])
def create_product():
    create_product_form = CreateProduct(request.form)
    if request.method == 'POST' and create_product_form.validate():
        file = request.files['product_image']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            img = resize_image(file, width, height)
            img.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            products_dict = {}
            db = shelve.open('product.db', 'c')

            try:
                products_dict = db['Products']
            except:
                print("Error !!")

            product = Product.Product(create_product_form.product_image.data, create_product_form.product_name.data,
                                      create_product_form.description.data, create_product_form.price.data)
            products_dict[product.get_product_id()] = product
            db['Products'] = products_dict

            db.close()
            return redirect(url_for('product_info'))
    return render_template('createProduct.html', form=create_product_form)


@app.route('/ProductInfo')
def product_info():
    products_dict = {}
    db = shelve.open('product.db', 'c')
    try:
        products_dict = db['Products']
    except KeyError:
        db['Products'] = {}
        products_dict = db['Products']

    db.close()

    products_list = []
    for key in products_dict:
        product = products_dict.get(key)
        products_list.append(product)

    return render_template('productInfo.html', products_list=products_list, count=len(products_list))


@app.route('/editProduct/<int:id>/', methods=['GET', 'POST'])
def edit_product(id):
    edit_product_form = CreateProduct(request.form)
    db = shelve.open('product.db')
    products_dict = db.get('Products', {})
    product = products_dict.get(id)

    if request.method == 'POST':
        print("Form data:", request.form)
        print("File data:", request.files)

        if edit_product_form.validate():
            file = request.files['product_image']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                img = resize_image(file, width, height)
                img.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))


            product.set_product_name(edit_product_form.product_name.data)
            product.set_description(edit_product_form.description.data)
            product.set_price(edit_product_form.price.data)

            products_dict[id] = product
            db['Products'] = products_dict
            db.close()

            return redirect(url_for('product_info'))
    else:
        edit_product_form.product_image.data = product.get_product_image()
        edit_product_form.product_name.data = product.get_product_name()
        edit_product_form.description.data = product.get_description()
        edit_product_form.price.data = product.get_price()

    db.close()
    return render_template('editProduct.html', form=edit_product_form)


@app.route('/deleteProduct/<int:id>', methods=['POST'])
def delete_product(id):
    products_dict = {}
    db = shelve.open('product.db', 'w')
    products_dict = db['Products']

    products_dict.pop(id)

    db['Products'] = products_dict
    db.close()

    return redirect(url_for('product_info'))


if __name__ == '__main__':
    app.run()
