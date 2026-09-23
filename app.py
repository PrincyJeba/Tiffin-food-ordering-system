import logging
import random
import string
from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, session

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------
app = Flask(__name__)
app.secret_key = "dev-secret-key-change-in-production"  # fine for a demo project

APP_VERSION = "2.0.0"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = app.logger

# ---------------------------------------------------------------------------
# In-memory "database" - no external DB, per project requirements
# ---------------------------------------------------------------------------
FOOD_ITEMS = [
    {"id": 1, "name": "Chicken Burger", "category": "Burgers", "price": 189, "description": "Grilled chicken patty, lettuce, and house sauce in a toasted bun.", "emoji": "🍔"},
    {"id": 2, "name": "Veg Burger", "category": "Burgers", "price": 149, "description": "Crispy vegetable patty with fresh greens and mayo.", "emoji": "🍔"},
    {"id": 3, "name": "Pizza", "category": "Mains", "price": 299, "description": "Wood-fired pizza with mozzarella and garden vegetables.", "emoji": "🍕"},
    {"id": 4, "name": "French Fries", "category": "Sides", "price": 99, "description": "Golden, salted fries served hot and crisp.", "emoji": "🍟"},
    {"id": 5, "name": "Chicken Biryani", "category": "Mains", "price": 259, "description": "Slow-cooked basmati rice layered with spiced chicken.", "emoji": "🍛"},
    {"id": 6, "name": "Pasta", "category": "Mains", "price": 219, "description": "Penne tossed in a rich tomato and herb sauce.", "emoji": "🍝"},
    {"id": 7, "name": "Sandwich", "category": "Sides", "price": 129, "description": "Toasted sandwich with fresh vegetables and cheese.", "emoji": "🥪"},
    {"id": 8, "name": "Coke", "category": "Beverages", "price": 59, "description": "Chilled 300ml soft drink.", "emoji": "🥤"},
]

ORDERS = {}  # order_id -> order dict, kept in memory only

logger.info("Application started")
logger.info("Food items loaded: %d items", len(FOOD_ITEMS))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def get_food_by_id(food_id):
    return next((item for item in FOOD_ITEMS if item["id"] == food_id), None)


def get_cart():
    return session.get("cart", {})


def save_cart(cart):
    session["cart"] = cart


def build_cart_view():
    cart = get_cart()
    items = []
    total = 0
    for food_id_str, qty in cart.items():
        food = get_food_by_id(int(food_id_str))
        if not food:
            continue
        subtotal = food["price"] * qty
        total += subtotal
        items.append({**food, "quantity": qty, "subtotal": subtotal})
    return items, total


def generate_order_id():
    suffix = "".join(random.choices(string.digits, k=4))
    return f"ORD-{suffix}"


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.route("/")
def home():
    categories = sorted(set(item["category"] for item in FOOD_ITEMS))
    cart_count = sum(get_cart().values())
    return render_template(
        "index.html",
        items=FOOD_ITEMS,
        categories=categories,
        cart_count=cart_count,
        version=APP_VERSION,
    )


@app.route("/add-to-cart", methods=["POST"])
def add_to_cart():
    food_id = request.form.get("food_id")
    food = get_food_by_id(int(food_id)) if food_id else None
    if food:
        cart = get_cart()
        cart[food_id] = cart.get(food_id, 0) + 1
        save_cart(cart)
        logger.info("User added item to cart: %s", food["name"])
    return redirect(request.referrer or url_for("home"))


@app.route("/cart")
def cart():
    items, total = build_cart_view()
    return render_template("cart.html", items=items, total=total, version=APP_VERSION)


@app.route("/update-cart", methods=["POST"])
def update_cart():
    food_id = request.form.get("food_id")
    action = request.form.get("action")
    cart = get_cart()
    if food_id in cart:
        if action == "increase":
            cart[food_id] += 1
        elif action == "decrease":
            cart[food_id] -= 1
            if cart[food_id] <= 0:
                del cart[food_id]
        save_cart(cart)
    return redirect(url_for("cart"))


@app.route("/remove-from-cart", methods=["POST"])
def remove_from_cart():
    food_id = request.form.get("food_id")
    cart = get_cart()
    if food_id in cart:
        del cart[food_id]
        save_cart(cart)
    return redirect(url_for("cart"))


@app.route("/order")
def order():
    items, total = build_cart_view()
    if not items:
        return redirect(url_for("home"))
    return render_template("order.html", items=items, total=total, version=APP_VERSION)


@app.route("/place-order", methods=["POST"])
def place_order():
    items, total = build_cart_view()
    if not items:
        return redirect(url_for("home"))

    order_id = generate_order_id()
    ORDERS[order_id] = {
        "order_id": order_id,
        "customer_name": request.form.get("customer_name", "").strip(),
        "phone_number": request.form.get("phone_number", "").strip(),
        "address": request.form.get("address", "").strip(),
        "items": items,
        "total": total,
        "placed_at": datetime.utcnow().isoformat(),
    }
    save_cart({})  # empty the cart after placing the order
    logger.info("Order placed: %s", order_id)
    return render_template("success.html", order_id=order_id, version=APP_VERSION)


@app.route("/health")
def health():
    logger.info("Health check requested")
    return {"status": "healthy"}, 200


@app.route("/version")
def version():
    return {"version": APP_VERSION}, 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)
