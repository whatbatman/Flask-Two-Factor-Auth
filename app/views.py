import os
import base64
from io import StringIO
from flask import Flask, render_template, redirect, url_for, flash, session, abort
from werkzeug.security import generate_password_hash, check_password_hash
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager, UserMixin, login_user, logout_user, current_user, UserMixin
from flask.ext.bootstrap import Bootstrap
from flask.ext.wtf import Form
from wtforms.validators import Required, Length, EqualTo
import onetimepass
import pyqrcode
from .forms import LoginForm, SettingsForm, RegisterForm, TwoFactorForm
from .models import User
from app import app, db, lm


@lm.user_loader
def load_user(user_id):
    """User loader callback for Flask-Login."""
    return User.query.get(int(user_id))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    form = SettingsForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=session['username']).first()
        if user.otp_secret is not None:
            flash('2FA already set up')
            return redirect(url_for('index'))
        user.otp_secret = base64.b32encode(os.urandom(10)).decode('utf-8')
        db.session.commit()
        return redirect(url_for('two_factor_setup'))
    return render_template('settings.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated():
        return redirect(url_for('index'))
    form = RegisterForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is not None:
            flash('Username taken')
            return redirect(url_for('register'))
        user = User(username=form.username.data, password=form.password.data)
        db.session.add(user)
        db.session.commit()

        session['username'] = user.username
        return redirect(url_for('index'))
    return render_template('register.html', form=form)

@app.route('/twofactor')
def two_factor_setup():
    if 'username' not in session:
        return redirect(url_for('index'))
    user = User.query.filter_by(username=session['username']).first()
    if user is None:
        return redirect(url_for('index'))
    return render_template('two-factor-setup.html'), 200, {
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0'}

@app.route('/qrcode')
def qrcode():
    if 'username' not in session:
        abort(404)
    user = User.query.filter_by(username=session['username']).first()
    if user is None:
        abort(404)
    
    del session['username']

    url = pyqrcode.create(user.get_totp_uri())
    stream = StringIO()
    url.svg(stream, scale=3)
    return stream.getvalue().encode('utf-8'), 200, {
        'Content-Type': 'image/svg+xml',
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0'}

@app.route('/two-factor-check', methods=['GET', 'POST'])
def two_factor_check():
    form = TwoFactorForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=session['username']).first()
        if user.verify_totp(form.token.data):
            login_user(user)
            flash('Welcome')
            return redirect(url_for('index'))
        flash('Bad Token')
        return redirect(url_for('login'))
    return render_template('two-factor-check.html', form=form, user=session['username'])

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated():
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        print user.otp_secret
        if user.otp_secret:
            print "no" * 15
            if user is not None and user.verify_password(form.password.data):
                print "!!!" * 15
                session['username'] = form.username.data
                return redirect(url_for('two_factor_check'))
            flash('Invalid username or password')
            return redirect(url_for('login'))
        else:
            if user is None or not user.verify_password(form.password.data):
                flash('Invalid username, password')
                return redirect(url_for('login'))

        session['username'] = form.username.data
        login_user(user)
        flash('Welcome')
        return redirect(url_for('index'))
    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


