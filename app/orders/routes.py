from flask import render_template, request, redirect, url_for, flash, session
from decimal import Decimal
from app.orders import bp
from app.models import Product, Order, OrderItem, SiteSetting
from app.extensions import db
from app.cart.routes import get_cart, cart_totals, save_cart


@bp.route('/checkout', methods=['GET', 'POST'])
def checkout():
    cart = get_cart()
    totals = cart_totals(cart)
    if not totals['items']:
        flash('तपाईंको झोला खाली छ।', 'warning')
        return redirect(url_for('products.list_products'))

    settings = SiteSetting.get_all_dict()
    delivery_enabled = settings.get('delivery_enabled', '1') == '1'
    pickup_enabled = settings.get('pickup_enabled', '1') == '1'
    payment_cod = settings.get('payment_cod', '1') == '1'
    payment_bank = settings.get('payment_bank', '0') == '1'
    payment_qr = settings.get('payment_qr', '0') == '1'

    if request.method == 'POST':
        name = request.form.get('customer_name', '').strip()
        phone = request.form.get('phone', '').strip()
        address = request.form.get('address', '').strip()
        ward = request.form.get('ward', '').strip()
        locality = request.form.get('locality', '').strip()
        city = request.form.get('city', 'Urlabari').strip()
        delivery_method = request.form.get('delivery_method', 'delivery')
        payment_method = request.form.get('payment_method', 'cod')
        notes = request.form.get('notes', '').strip()

        errors = []
        if not name:
            errors.append('पूरा नाम आवश्यक छ।')
        if not phone or len(phone) < 10:
            errors.append('सही मोबाइल नम्बर दिनुहोस्।')
        if delivery_method == 'delivery' and not address:
            errors.append('ठेगाना आवश्यक छ।')
        if delivery_method == 'delivery' and not delivery_enabled:
            errors.append('डेलिभरी उपलब्ध छैन।')
        if delivery_method == 'pickup' and not pickup_enabled:
            errors.append('पिकअप उपलब्ध छैन।')

        # Re-validate stock and prices from DB
        order_items_data = []
        subtotal = Decimal('0')
        for item in totals['items']:
            product = Product.query.get(item['product'].id)
            if not product or not product.active:
                errors.append(f'{item["product"].name} उपलब्ध छैन।')
                continue
            qty = item['quantity']
            if product.stock < qty:
                errors.append(f'{product.name} को स्टक अपर्याप्त (उपलब्ध: {product.stock})।')
                continue
            price = Decimal(str(product.price))
            line = price * qty
            subtotal += line
            order_items_data.append({
                'product': product,
                'quantity': qty,
                'unit_price': price,
                'subtotal': line,
            })

        min_order = Decimal(settings.get('min_order_amount', '0') or '0')
        if subtotal < min_order:
            errors.append(f'न्यूनतम अर्डर रकम रु. {min_order} हो।')

        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template(
                'checkout.html',
                **totals,
                delivery_enabled=delivery_enabled,
                pickup_enabled=pickup_enabled,
                payment_cod=payment_cod,
                payment_bank=payment_bank,
                payment_qr=payment_qr,
                settings=settings,
                form=request.form,
            )

        # Delivery charge
        delivery_charge = Decimal('0')
        if delivery_method == 'delivery':
            free_th = Decimal(settings.get('free_delivery_threshold', '1000') or '1000')
            base = Decimal(settings.get('delivery_charge', '50') or '50')
            if subtotal < free_th:
                delivery_charge = base

        total = subtotal + delivery_charge

        try:
            order = Order(
                order_number=Order.generate_order_number(),
                customer_name=name,
                phone=phone,
                address=address,
                ward=ward,
                locality=locality,
                city=city or 'Urlabari',
                delivery_method=delivery_method,
                payment_method=payment_method,
                subtotal=subtotal,
                delivery_charge=delivery_charge,
                total=total,
                status='pending',
                notes=notes,
            )
            db.session.add(order)
            db.session.flush()

            for d in order_items_data:
                oi = OrderItem(
                    order_id=order.id,
                    product_id=d['product'].id,
                    product_name=d['product'].name,
                    quantity=d['quantity'],
                    unit_price=d['unit_price'],
                    subtotal=d['subtotal'],
                )
                db.session.add(oi)
                # Decrease stock
                d['product'].stock = max(0, d['product'].stock - d['quantity'])

            db.session.commit()
            save_cart({})
            return redirect(url_for('orders.success', order_number=order.order_number))
        except Exception as e:
            db.session.rollback()
            flash('अर्डर राख्न समस्या भयो। फेरि प्रयास गर्नुहोस्।', 'danger')
            print(f'Order error: {e}')

    return render_template(
        'checkout.html',
        **totals,
        delivery_enabled=delivery_enabled,
        pickup_enabled=pickup_enabled,
        payment_cod=payment_cod,
        payment_bank=payment_bank,
        payment_qr=payment_qr,
        settings=settings,
        form={},
    )


@bp.route('/order-success/<order_number>')
def success(order_number):
    order = Order.query.filter_by(order_number=order_number).first_or_404()
    return render_template('order_success.html', order=order)
