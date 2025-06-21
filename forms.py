from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, RadioField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional



class SignUpForm(FlaskForm):
    display_name = StringField('Display Name', validators=[DataRequired(), Length(min=3, max=15)], render_kw={"placeholder":"Display Name"})
    email = StringField('Email', validators=[DataRequired(), Email(message="Please enter a valid email address.")], render_kw={"placeholder":"Valid Email"})
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)], render_kw={"placeholder":"Password"})
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(), EqualTo('password', message='Passwords must match')], render_kw={"placeholder":"Confirm Password"})
    submit = SubmitField('Register')



class LoginForm(FlaskForm):
    email = StringField('Email', validators=[
        DataRequired(), Email(message="Please enter a valid email address.")
    ], render_kw={"placeholder": "Email"})
    
    password = PasswordField('Password', validators=[
        DataRequired(), Length(min=8)
    ], render_kw={"placeholder": "Password"})
    
    submit = SubmitField('Log In')



class CreatePollForm(FlaskForm):
    question = StringField('Question', validators=[
        DataRequired()], render_kw={"placeholder": "Question"})
    option_a = StringField('Option A', validators=[
        DataRequired()], render_kw={"placeholder": "Option A"})

    option_b = StringField('Option B', validators=[
        DataRequired()], render_kw={"placeholder": "Option B"})

    option_c = StringField('Option C', validators=[
        Optional()], render_kw={"placeholder": "Option C (optional)"})

    option_d = StringField('Option D', validators=[
        Optional()], render_kw={"placeholder": "Option D (optional)"})

    submit = SubmitField('Create Poll')



class VoteForm(FlaskForm):
    answer = RadioField('Answer', choices=[], validators=[DataRequired()])
    submit = SubmitField('Submit Vote')