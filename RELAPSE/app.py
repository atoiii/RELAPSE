from flask import Flask, render_template, request, redirect, url_for, flash, session, make_response
from datetime import timedelta
import shelve
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)
app.secret_key = "your_secret_key"
app.config['SESSION_COOKIE_NAME'] = 'relapse_session'
app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevent JavaScript from accessing cookies
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True if using HTTPS
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Prevent cross-site request issues
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=3)  # For "Remember Me"

PRODUCTS = [
    {"id": 1, "name": "RELAPSE Winx Club Tee", "price": 50, "category": "shirts", "image": "shirt.jpg"},
    {"id": 2, "name": "Casual Hoodie", "price": 70, "category": "hoodies", "image": "hoodie.jpg"},
]


@app.route('/')
def home():
    return render_template("home.html", products=PRODUCTS)


@app.route('/new')
def new():
    return render_template("new.html")


@app.route('/sales')
def sales():
    return render_template("sales.html")


@app.route('/about')
def about():
    return render_template("about.html")


@app.route('/clothing/<category>')
def clothing(category):
    filtered_products = [product for product in PRODUCTS if product["category"] == category]
    return render_template("clothing.html", category=category, products=filtered_products)


@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        remember = "remember" in request.form  # Check "Remember Me"

        with shelve.open("users.db") as db:
            user = db.get(email)
            if user and user["password"] == password:
                session["user"] = user
                session["cart"] = session.get("cart", [])
                if remember:
                    session.permanent = True  # Persistent session for "Remember Me"
                else:
                    session.permanent = False  # Temporary session
                flash(f"Welcome back, {user['first_name']}!", "success")
                return redirect(url_for("profile"))
            else:
                flash("Invalid email or password.", "danger")

    return render_template("login.html")




@app.route('/profile')
def profile():
    if "user" not in session:
        flash("Please log in to view your profile.", "warning")
        return redirect(url_for("login"))

    return render_template("profile.html", user=session["user"])


@app.route('/signup', methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        first_name = request.form["first_name"]
        last_name = request.form["last_name"]
        email = request.form["email"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if password != confirm_password:
            flash("Passwords do not match!", "danger")
            return render_template("signup.html")

        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            flash("Invalid email address!", "danger")
            return render_template("signup.html")

        with shelve.open("users.db") as db:
            if email in db:
                flash("Account already exists!", "danger")
            else:
                db[email] = {
                    "first_name": first_name,
                    "last_name": last_name,
                    "email": email,
                    "password": password,
                    "membership_status": "Regular"
                }
                flash("Account created successfully!", "success")
                return redirect(url_for("login"))

    return render_template("signup.html")


@app.route('/cart', methods=["GET", "POST"])
def cart():
    if "user" not in session:
        flash("Please log in to access your cart.", "danger")
        return redirect(url_for("login"))

    if "cart" not in session:
        session["cart"] = []

    if request.method == "POST":
        if "product_id" in request.form:
            # Add product to the cart
            product_id = int(request.form["product_id"])
            size = request.form["size"]
            quantity = int(request.form["quantity"])
            product = next((p for p in PRODUCTS if p["id"] == product_id), None)

            if product:
                # Check if the product with the same size is already in the cart
                for item in session["cart"]:
                    if item["id"] == product_id and item["size"] == size:
                        item["quantity"] += quantity
                        break
                else:
                    session["cart"].append({
                        "id": product_id,
                        "name": product["name"],
                        "price": product["price"],
                        "size": size,
                        "quantity": quantity
                    })
                session.modified = True
                flash(f"{quantity} {size.upper()} {product['name']} added to cart!", "success")

        elif "remove_product_id" in request.form:
            # Remove specific quantity of a product from the cart
            product_id = int(request.form["remove_product_id"])
            size = request.form["size"]
            quantity_to_remove = int(request.form["quantity_to_remove"])

            for item in session["cart"]:
                if item["id"] == product_id and item["size"] == size:
                    if item["quantity"] > quantity_to_remove:
                        item["quantity"] -= quantity_to_remove
                    else:
                        session["cart"].remove(item)
                    break

            session.modified = True
            flash("Item(s) removed from cart.", "success")

    return render_template("cart.html", cart=session["cart"])


@app.route('/add_to_cart/<int:product_id>', methods=["GET", "POST"])
def add_to_cart(product_id):
    if "user" not in session:
        flash("Please log in to add items to your cart.", "danger")
        return redirect(url_for("login"))

    product = next((p for p in PRODUCTS if p["id"] == product_id), None)
    if not product:
        flash("Product not found.", "danger")
        return redirect(url_for("home"))

    if request.method == "POST":
        size = request.form["size"]
        quantity = int(request.form["quantity"])

        if "cart" not in session:
            session["cart"] = []

        # Check if the product with the same size is already in the cart
        for item in session["cart"]:
            if item["id"] == product_id and item["size"] == size:
                item["quantity"] += quantity
                break
        else:
            session["cart"].append({
                "id": product_id,
                "name": product["name"],
                "price": product["price"],
                "size": size,
                "quantity": quantity
            })
        session.modified = True
        flash(f"{quantity} {size.upper()} {product['name']} added to cart!", "success")
        return redirect(url_for("cart"))

    return render_template("add_to_cart.html", product=product)



@app.route('/checkout', methods=["GET", "POST"])
def checkout():
    if "cart" not in session or len(session["cart"]) == 0:
        flash("Your cart is empty.", "danger")
        return redirect(url_for("cart"))

    if request.method == "POST":
        session["cart"] = []  # Clear cart after payment
        session.modified = True
        flash("Payment successful! Your order has been placed.", "success")
        return redirect(url_for("order_confirmation"))
    return render_template("checkout.html")


@app.route('/order_confirmation')
def order_confirmation():
    return render_template("order_confirmation.html")


@app.route('/forgot_password', methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form["email"]

        with shelve.open("users.db") as db:
            if email in db:
                send_password_reset_email(email)
                flash("A password reset email has been sent to your email address.", "success")
                return redirect(url_for("login"))
            else:
                flash("Email not found!", "danger")

    return render_template("forgot_password.html")


@app.route('/reset_password', methods=["GET", "POST"])
def reset_password():
    if request.method == "POST":
        email = request.form["email"]
        new_password = request.form["new_password"]
        new_password_confirm = request.form["new_password_confirm"]

        if new_password != new_password_confirm:
            flash("Passwords do not match!", "danger")
            return render_template("reset_password.html")

        with shelve.open("users.db") as db:
            if email in db:
                db[email]["password"] = new_password
                flash("Password reset successfully!", "success")
                return redirect(url_for("login"))
            else:
                flash("Email not found!", "danger")

    return render_template("reset_password.html")


@app.route('/logout')
def logout():
    session.pop("user", None)
    session.pop("cart", None)
    flash("Logged out successfully.", "success")
    return redirect(url_for("home"))


def send_password_reset_email(to_email):
    sender_email = "your_email@example.com"  # Replace with your email
    sender_password = "your_email_password"  # Replace with your email password
    subject = "Password Reset Request"
    body = f"""
    Hi,

    You requested a password reset. Please click the link below to reset your password:
    {url_for('reset_password', _external=True)}

    If you did not request this, please ignore this email.
    """
    try:
        msg = MIMEMultipart()
        msg["From"] = sender_email
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, to_email, msg.as_string())
        server.quit()
    except Exception as e:
        print(f"Error sending email: {e}")


if __name__ == "__main__":
    app.run(debug=True)
