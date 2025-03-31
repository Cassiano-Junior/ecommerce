# Importação
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user


app = Flask(__name__)
app.config['SECRET_KEY'] = "minha_chave_123"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'

login_manager = LoginManager()

db = SQLAlchemy(app)
login_manager.init_app(app)
login_manager.login_view = 'login'
# Modelagem
# User (id, username, password)
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)
    cart = db.relationship('CartItem', backref='user', lazy=True)

# Produto (id, name, price, decription)
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, nullable=True)

# Carrinho
class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)


# Autenticação
@login_manager.user_loader
def user_loader(user_id):
    return User.query.get(int(user_id))

@app.route('/login', methods=["POST"])
def login():
    data = request.json

    user = User.query.filter_by(username=data.get("username")).first()

    if user and data.get('password') == user.password:
        login_user(user)
        return jsonify({"message": "Logged in sucessfully!"})
    return jsonify({"message" : "Unauthorized. Invalid credentials."}), 401


@app.route('/logout', methods=["POST"])
@login_required
def logout():
    logout_user()
    return jsonify({"message": "Logout successfully!"})


@app.route('/api/products/add', methods=["POST"])
@login_required
def add_product():
    data = request.json
    if 'name' in data and 'price' in data:
        product = Product(name=data["name"], price=data["price"], description=data.get('description', ""))
        db.session.add(product)
        db.session.commit()
        return jsonify({"message": "Product added successfully!"})
    return jsonify({'message': "Invalid product data"}), 400

@app.route('/api/products/delete/<int:product_id>', methods=["DELETE"])
@login_required
def delete_product(product_id):
    product = Product.query.get(product_id)
    if product: 
        db.session.delete(product)
        db.session.commit()
        return jsonify({"message" : "Product deleted successfully!"})
    return jsonify({"message" : "Product Not Found"}), 404

@app.route('/api/products/<int:product_id>', methods=["GET"])
def get_product_details(product_id):
    product = Product.query.get(product_id)
    if product:
        return jsonify({
            "id": product.id,
            "name": product.name,
            "price": product.price,
            "description": product.description
        })
    return jsonify({"message" : "Product Not Found"}), 404

@app.route('/api/products/update/<int:product_id>', methods=["PUT"])
@login_required
def update_product(product_id):
    product = Product.query.get(product_id)
    if not product:
        return jsonify({"message" : "Product Not Found"}), 404
    
    data = request.json
    if 'name' in data:
        product.name = data['name']
    
    if 'price' in data:
        product.price = data['price']

    if 'description' in data:
        product.price = data['description']

    db.session.commit()
    return jsonify({'message': 'Product updated successfully!'})

@app.route('/api/products', methods=["GET"])
def get_products():
    products = Product.query.all()
    product_list = []

    for product in products:
        product_data = {
            "id": product.id,
            "name": product.name,
            "price": product.price,
        }
        product_list.append(product_data)
    return jsonify(product_list)

# Checkout
@app.route('/api/cart/add/<int:product_id>', methods=["POST"])
@login_required
def add_to_cart(product_id):
    user = User.query.get(int(current_user.id))
    product = Product.query.get(product_id)

    if user and product:
        cart_item = CartItem(user_id=user.id, product_id=product.id)
        db.session.add(cart_item)
        db.session.commit()
        return jsonify({"messagem" : "Item added to the cart successfully!"})
    return jsonify({"message" : "Failed to add item to the cart!"}), 400


@app.route('/api/cart/remove/<int:product_id>', methods=["Delete"])
@login_required
def remove_from_cart(product_id):
    cart_item = CartItem.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    if cart_item:
        db.session.delete(cart_item)
        db.session.commit()
        return jsonify({"message" : "Item removed from the cart successfully!"})
    return jsonify({"message" : "Failed to remove item from the cart!"}), 400


if __name__ == '__main__':
    app.run(debug=True)