from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = 'secret_key'

deliveries = []
selected_delivery = {}

@app.route('/')
def index():
    return render_template('website.html', deliveries=deliveries, selected_delivery=selected_delivery)

@app.route('/add_delivery', methods=['POST'])
def add_delivery():
    country = request.form.get('country')
    address = request.form.get('address')
    city = request.form.get('city')
    state = request.form.get('state')
    postcode = request.form.get('postcode')

    if country and address and city:
        deliveries.append({
            'country': country,
            'address': address,
            'city': city,
            'state': state,
            'postcode': postcode
        })
        flash('Delivery added successfully!', 'success')
    else:
        flash('All fields are required to add a delivery!', 'danger')
    return redirect(url_for('index'))

@app.route('/edit_delivery/<int:index>', methods=['GET', 'POST'])
def edit_delivery(index):
    if request.method == 'POST':
        deliveries[index] = {
            'country': request.form.get('country'),
            'address': request.form.get('address'),
            'city': request.form.get('city'),
            'state': request.form.get('state'),
            'postcode': request.form.get('postcode')
        }
        flash('Delivery updated successfully!', 'success')
        return redirect(url_for('index'))
    return render_template('edit_delivery.html', delivery=deliveries[index], index=index)

@app.route('/delete_delivery/<int:index>', methods=['POST'])
def delete_delivery(index):
    global selected_delivery
    if 0 <= index < len(deliveries):
        if deliveries[index] == selected_delivery:
            selected_delivery = {}
        deliveries.pop(index)
        flash('Delivery deleted successfully!', 'success')
    else:
        flash('Invalid delivery index for deletion!', 'danger')
    return redirect(url_for('index'))

@app.route('/select_delivery/<int:index>', methods=['POST'])
def select_delivery(index):
    global selected_delivery
    if 0 <= index < len(deliveries):
        selected_delivery = deliveries[index]
        flash('Delivery selected successfully!', 'success')
    else:
        flash('Invalid delivery selection!', 'danger')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
