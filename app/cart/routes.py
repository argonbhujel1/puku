from flask import render_template, request, jsonify, session, redirect, url_for, flash
from decimal import Decimal
from app.cart import bp
from app.models import Product, SiteSetting
from app.extensions import csrf


def get_cart():
    return session.get('cart', {})


def save_cart(cart):
    session['cart'] = cart
    session.modified = True


def cart_totals(cart):
    subtotal = Decimal('0')
    items = []
    for pid, data in cart.items():
        product = Product.query.get(int(pid))
        if not product or not product.active:
            continue
        qty = int(data.get('quantity', 0))
        if qty <= 0:
            continue
        # Always use DB price
        price = Decimal(str(product.price))
        line = price * qty
        subtotal += line
        items.append({
            'product': product,
            'quantity': qty,
            'unit_price': price,
            'subtotal': line,
        })
    delivery_charge = Decimal('0')
    delivery_enabled = SiteSetting.get('delivery_enabled', '1') == '1'
    free_threshold = Decimal(SiteSetting.get('free_delivery_threshold', '1000') or '1000')
    base_delivery = Decimal(SiteSetting.get('delivery_charge', '50') or '50')
    # delivery decided at checkout; show estimate
    if delivery_enabled and subtotal > 0 and subtotal < free_threshold:
        delivery_charge = base_delivery
    total = subtotal + delivery_charge
    return {
        'items': items,
        'subtotal': subtotal,
        'delivery_charge': delivery_charge,
        'total': total,
        'free_threshold': free_threshold,
        'base_delivery': base_delivery,
    }


@bp.route('/')
def view_cart():
    cart = get_cart()
    totals = cart_totals(cart)
    return render_template('cart.html', **totals)


@bp.route('/add', methods=['POST'])
@csrf.exempt  # handled via header token in JS; form also works
def add_to_cart():
    product_id = request.form.get('product_id') or (request.json or {}).get('product_id')
    quantity = request.form.get('quantity') or (request.json or {}).get('quantity', 1)
    try:
        product_id = int(product_id)
        quantity = int(quantity)
    except (TypeError, ValueError):
        if request.is_json or request.headers.get('X-Requested-With'):
            return jsonify({'ok': False, 'error': 'अवैध अनुरोध'}), 400
        flash('अवैध अनुरोध।', 'danger')
        return redirect(request.referrer or url_for('main.home'))

    product = Product.query.get(product_id)
    if not product or not product.active:
        if request.is_json or request.headers.get('X-Requested-With'):
            return jsonify({'ok': False, 'error': 'उत्पादन फेला परेन'}), 404
        flash('उत्पादन फेला परेन।', 'danger')
        return redirect(request.referrer or url_for('main.home'))

    if quantity < 1:
        quantity = 1
    if product.stock < quantity:
        if request.is_json or request.headers.get('X-Requested-With'):
            return jsonify({'ok': False, 'error': f'स्टक अपर्याप्त। उपलब्ध: {product.stock}'}), 400
        flash(f'स्टक अपर्याप्त। उपलब्ध: {product.stock}', 'warning')
        return redirect(request.referrer or url_for('main.home'))

    cart = get_cart()
    key = str(product_id)
    current_qty = cart.get(key, {}).get('quantity', 0)
    new_qty = current_qty + quantity
    if new_qty > product.stock:
        new_qty = product.stock
    cart[key] = {'quantity': new_qty}
    save_cart(cart)

    count = sum(i.get('quantity', 0) for i in cart.values())
    if request.is_json or request.headers.get('X-Requested-With'):
        return jsonify({'ok': True, 'cart_count': count, 'message': 'झोलामा थपियो!'})
    flash('उत्पादन झोलामा थपियो!', 'success')
    return redirect(request.referrer or url_for('cart.view_cart'))


@bp.route('/update', methods=['POST'])
def update_cart():
    product_id = request.form.get('product_id') or (request.json or {}).get('product_id')
    quantity = request.form.get('quantity') or (request.json or {}).get('quantity')
    try:
        product_id = int(product_id)
        quantity = int(quantity)
    except (TypeError, ValueError):
        return jsonify({'ok': False, 'error': 'अवैध'}), 400

    cart = get_cart()
    key = str(product_id)
    product = Product.query.get(product_id)
    if quantity <= 0:
        cart.pop(key, None)
    else:
        if product and quantity > product.stock:
            quantity = product.stock
        cart[key] = {'quantity': quantity}
    save_cart(cart)
    totals = cart_totals(cart)
    count = sum(i.get('quantity', 0) for i in cart.values())
    return jsonify({
        'ok': True,
        'cart_count': count,
        'subtotal': float(totals['subtotal']),
        'delivery_charge': float(totals['delivery_charge']),
        'total': float(totals['total']),
    })


@bp.route('/remove', methods=['POST'])
def remove_from_cart():
    product_id = request.form.get('product_id') or (request.json or {}).get('product_id')
    try:
        product_id = str(int(product_id))
    except (TypeError, ValueError):
        return jsonify({'ok': False}), 400
    cart = get_cart()
    cart.pop(product_id, None)
    save_cart(cart)
    totals = cart_totals(cart)
    count = sum(i.get('quantity', 0) for i in cart.values())
    return jsonify({
        'ok': True,
        'cart_count': count,
        'subtotal': float(totals['subtotal']),
        'total': float(totals['total']),
    })


@bp.route('/count')
def cart_count():
    cart = get_cart()
    count = sum(i.get('quantity', 0) for i in cart.values())
    return jsonify({'count': count})
