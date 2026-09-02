import razorpay
import hmac
import hashlib
import logging
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, redirect, url_for, render_template, current_app
from flask_login import login_required, current_user
from ..models import db, User, Payment

logger = logging.getLogger(__name__)

payment_bp = Blueprint('payment', __name__, url_prefix='/payment')

# Plan pricing in paise (INR) with duration in days
PLAN_PRICES = {
    'trial':    {'amount': 4900,  'label': '7-Day Trial',   'days': 7},
    'monthly':  {'amount': 49900, 'label': '1 Month Pro',  'days': 30},
    'pro':      {'amount': 129900,'label': '3 Months Pro',  'days': 90},
    'business': {'amount': 149900,'label': 'Business',      'days': 30},
}


def _get_razorpay_client():
    """Initialize and return Razorpay client."""
    key_id = current_app.config.get('RAZORPAY_KEY_ID')
    key_secret = current_app.config.get('RAZORPAY_KEY_SECRET')
    if not key_id or not key_secret:
        return None
    return razorpay.Client(auth=(key_id, key_secret))


@payment_bp.route('/create-order/<plan>')
@login_required
def create_order(plan):
    """Create a Razorpay order and return order details for frontend checkout."""
    if plan not in PLAN_PRICES:
        return jsonify({'error': 'Invalid plan'}), 400

    client = _get_razorpay_client()
    if not client:
        logger.error("Razorpay keys not configured")
        return jsonify({'error': 'Payment system not configured'}), 500

    price_info = PLAN_PRICES[plan]

    try:
        # Create Razorpay order
        order = client.order.create({
            'amount': price_info['amount'],
            'currency': 'INR',
            'payment_capture': 1,  # Auto-capture payment
            'notes': {
                'user_id': str(current_user.id),
                'plan': plan,
                'email': current_user.email,
            }
        })

        # Record pending payment
        payment = Payment(
            user_id=current_user.id,
            razorpay_order_id=order['id'],
            plan=plan,
            amount=price_info['amount'],
            currency='INR',
            status='pending'
        )
        db.session.add(payment)
        db.session.commit()

        return jsonify({
            'order_id': order['id'],
            'amount': price_info['amount'],
            'currency': 'INR',
            'plan': plan,
            'plan_label': price_info['label'],
        })

    except Exception as e:
        logger.exception("Error creating Razorpay order")
        return jsonify({'error': 'Failed to create order. Please try again.'}), 500


@payment_bp.route('/verify', methods=['POST'])
@login_required
def verify_payment():
    """Verify Razorpay payment signature and upgrade user plan."""
    data = request.get_json()
    razorpay_order_id = data.get('razorpay_order_id')
    razorpay_payment_id = data.get('razorpay_payment_id')
    razorpay_signature = data.get('razorpay_signature')

    if not all([razorpay_order_id, razorpay_payment_id, razorpay_signature]):
        return jsonify({'error': 'Missing payment details'}), 400

    key_secret = current_app.config.get('RAZORPAY_KEY_SECRET')

    try:
        # Verify signature
        generated_signature = hmac.new(
            key_secret.encode('utf-8'),
            f'{razorpay_order_id}|{razorpay_payment_id}'.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        if generated_signature != razorpay_signature:
            logger.warning("Invalid payment signature for order %s", razorpay_order_id)
            # Mark payment as failed
            payment = Payment.query.filter_by(razorpay_order_id=razorpay_order_id).first()
            if payment:
                payment.status = 'failed'
                db.session.commit()
            return jsonify({'error': 'Payment verification failed'}), 400

        # Signature is valid — upgrade the user
        payment = Payment.query.filter_by(razorpay_order_id=razorpay_order_id, user_id=current_user.id).first()
        if not payment:
            return jsonify({'error': 'Payment record not found'}), 404

        if payment.status == 'completed':
            return jsonify({'success': True, 'plan': current_user.plan, 'message': 'Payment already processed'})

        # Update payment record
        payment.razorpay_payment_id = razorpay_payment_id
        payment.status = 'completed'

        # Upgrade user plan with plan-specific duration
        plan_days = PLAN_PRICES.get(payment.plan, {}).get('days', 30)
        current_user.plan = payment.plan
        current_user.subscription_status = 'active'
        current_user.plan_expires_at = datetime.utcnow() + timedelta(days=plan_days)

        db.session.commit()
        logger.info("User %s upgraded to %s plan for %d days", current_user.email, payment.plan, plan_days)

        return jsonify({
            'success': True,
            'plan': current_user.plan,
            'message': f'Successfully upgraded to {payment.plan} plan!'
        })

    except Exception as e:
        logger.exception("Error verifying payment")
        db.session.rollback()
        return jsonify({'error': 'Payment verification failed'}), 500


@payment_bp.route('/success')
@login_required
def payment_success():
    """Payment success page."""
    plan = request.args.get('plan', current_user.plan)
    return render_template('payment/success.html', plan=plan)


@payment_bp.route('/cancel')
@login_required
def payment_cancel():
    """Payment cancelled page."""
    return render_template('payment/cancel.html')


@payment_bp.route('/webhook', methods=['POST'])
def razorpay_webhook():
    """Handle Razorpay webhooks for payment events."""
    webhook_secret = current_app.config.get('RAZORPAY_KEY_SECRET')
    payload = request.get_data(as_text=True)
    signature = request.headers.get('X-Razorpay-Signature')

    if webhook_secret and signature:
        # Verify webhook signature
        expected = hmac.new(
            webhook_secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        if expected != signature:
            logger.warning("Invalid webhook signature")
            return jsonify({'error': 'Invalid signature'}), 400

    try:
        event = request.get_json()
        event_type = event.get('event')
        logger.info("Received Razorpay webhook: %s", event_type)

        if event_type == 'payment.captured':
            _handle_payment_captured(event['payload']['payment']['entity'])
        elif event_type == 'payment.failed':
            _handle_payment_failed(event['payload']['payment']['entity'])
        elif event_type == 'refund.created':
            _handle_refund(event['payload']['refund']['entity'])

    except Exception as e:
        logger.exception("Error processing webhook")

    return jsonify({'status': 'ok'}), 200


def _handle_payment_captured(payment_entity):
    """When payment is captured, ensure user is upgraded."""
    order_id = payment_entity.get('order_id')
    payment_id = payment_entity.get('id')

    if not order_id:
        return

    try:
        payment = Payment.query.filter_by(razorpay_order_id=order_id).first()
        if payment and payment.status != 'completed':
            payment.razorpay_payment_id = payment_id
            payment.status = 'completed'

            user = db.session.get(User, payment.user_id)
            if user:
                plan_days = PLAN_PRICES.get(payment.plan, {}).get('days', 30)
                user.plan = payment.plan
                user.subscription_status = 'active'
                user.plan_expires_at = datetime.utcnow() + timedelta(days=plan_days)

            db.session.commit()
            logger.info("Payment captured for order %s — user upgraded to %s", order_id, payment.plan)
    except Exception as e:
        logger.exception("Error handling payment captured")
        db.session.rollback()


def _handle_payment_failed(payment_entity):
    """When payment fails, mark as failed."""
    order_id = payment_entity.get('order_id')
    if not order_id:
        return

    try:
        payment = Payment.query.filter_by(razorpay_order_id=order_id).first()
        if payment:
            payment.status = 'failed'
            db.session.commit()
            logger.info("Payment failed for order %s", order_id)
    except Exception as e:
        logger.exception("Error handling payment failed")
        db.session.rollback()


def _handle_refund(refund_entity):
    """When refund is created, downgrade user."""
    payment_id = refund_entity.get('payment_id')
    if not payment_id:
        return

    try:
        payment = Payment.query.filter_by(razorpay_payment_id=payment_id).first()
        if payment:
            payment.status = 'refunded'
            user = db.session.get(User, payment.user_id)
            if user:
                user.plan = 'free'
                user.subscription_status = 'canceled'
            db.session.commit()
            logger.info("Refund processed for payment %s — user downgraded", payment_id)
    except Exception as e:
        logger.exception("Error handling refund")
        db.session.rollback()
