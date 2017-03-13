from flask.ext.wtf import Form
from wtforms.validators import Required, Length, EqualTo
from wtforms import StringField, PasswordField, SubmitField, RadioField

class RegisterForm(Form):
    username = StringField('Username', validators=[Required(), Length(1, 64)])
    password = PasswordField('Password', validators=[Required()])
    password_again = PasswordField('Password again',
                                    validators=[Required(), EqualTo('password')])
    submit = SubmitField('Register')

class SettingsForm(Form):
    password = PasswordField('Password', validators=[Required()])
    two_factor = RadioField('two_factor', choices=[('On', 'Enable 2 factor auth'),
                                                ('off', 'turn off two factor auth')])
    submit = SubmitField('Enable 2FA')

class LoginForm(Form):
    username = StringField('Username', validators=[Required(), Length(1, 64)])
    password = PasswordField('Password', validators=[Required()])
    submit = SubmitField('Login')

class TwoFactorForm(Form):
    token = StringField('Token', validators=[Required(), Length(6, 6)])
    submit = SubmitField('Login')
