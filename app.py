from flask import Flask, render_template, url_for, redirect, flash, session, request
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer
from sqlalchemy.sql.expression import func
from flask_socketio import SocketIO, emit
from flask_cors import CORS


from database import db
from models import Poll, User, Vote, Comment
from forms import SignUpForm, LoginForm, CreatePollForm
import uuid

app = Flask(__name__)
CORS(app, origins=["https://pollrot.com", "https://www.pollrot.com"])

from dotenv import load_dotenv
import os
load_dotenv()

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
#app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pollrot.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


app.config['MAIL_SERVER'] = 'smtp.gmail.com'  # or your SMTP server
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')

mail = Mail(app)

db.init_app(app)

socketio = SocketIO(app)

with app.app_context():
        db.create_all()

from models import Poll





s = URLSafeTimedSerializer(app.config['SECRET_KEY'])

def generate_verification_token(email):
        return s.dumps(email, salt='email-confirm')

def confirm_token(token, expiration=3600):
        try:
                email = s.loads(token, salt='email-confirm', max_age=expiration)
        except:
                return False
        return email

def send_verification_email(user_email):
        token = generate_verification_token(user_email)
        link = url_for('confirm_email', token=token, _external=True)
        msg = Message('Confirm Your Email', recipients=[user_email])
        msg.subject = "PollRot Email Verification"
        msg.body = f"""
        Hello,

        Thanks for signing up for PollRot! Please click the link below to verify your email address:

        {link}

        If you didn't request this, you can ignore this email.

        Thanks,
        The PollRot Team
        """
        try:
                mail.send(msg)
        except Exception as e:
                print("Email failed:", e)

def confirm_token(token, expiration=3600):
        try:
                email = s.loads(token, salt='email-confirm', max_age=expiration)
        except:
                return False
        return email


#HOMEPAGE
@app.route('/',methods=['GET','POST'])
def index():
        poll = Poll.query.order_by(func.random()).first()
        if not poll:
               return render_template("polls.html",poll=None)

        comments = Comment.query.filter_by(poll_id=poll.id).order_by(Comment.id).all()


        votes = Vote.query.filter_by(poll_id=poll.id).all()
        total_votes = len(votes)
        vote_counts = Counter(v.selected_option for v in votes)

        # Calculate percentages or zero if no votes yet
        percentages = {
                'A': (vote_counts.get('A', 0) / total_votes * 100) if total_votes > 0 else 0,
                'B': (vote_counts.get('B', 0) / total_votes * 100) if total_votes > 0 else 0,
                'C': (vote_counts.get('C', 0) / total_votes * 100) if total_votes > 0 else 0,
                'D': (vote_counts.get('D', 0) / total_votes * 100) if total_votes > 0 else 0,
        }


        user_vote = None
        user_id = session.get('user_id')
        if user_id:      
                vote = Vote.query.filter_by(user_id=user_id, poll_id=poll.id).first()
                if vote: 
                        user_vote = vote.selected_option
                        return render_template("polls.html", poll=poll, user_vote=user_vote, vote_percentages=percentages,comments=comments)
        
        
        return render_template("polls.html",poll=poll,comments=comments)



@socketio.on('submit_vote')
def handle_submit_vote(data):
        user_id = session.get('user_id')
        poll_id = data.get('poll_id')
        selected_option = data.get('selected_option')

        existing_vote = Vote.query.filter_by(user_id=user_id, poll_id=poll_id).first()
        if existing_vote:
                existing_vote.selected_option = selected_option
                db.session.commit()
                print("updated")
                emit('vote_response', {'success': True, 'message': 'Vote updated successfully!'})
        else:
                new_vote = Vote(user_id=user_id, poll_id=poll_id, selected_option=selected_option)
                db.session.add(new_vote)
                db.session.commit()
                print("new vote")
                emit('vote_response', {'success': True, 'message': 'Vote submitted successfully!'})

@socketio.on('submit_comment')
def handle_submit_comment(data):
        user_id = session.get('user_id')
        if not user_id:
                emit('comment_response', {'success': False, 'message': 'User not logged in to comment.'})
                return

        poll_id = data.get('poll_id')
        comment_text = data.get('comment_text')

        if not poll_id or not comment_text:
                emit('comment_response', {'success': False, 'message': 'Invalid comment data.'})
                return

        user = User.query.get(user_id)
        if not user:
                emit('comment_response', {'success': False, 'message': 'User not found.'})
                return

        poll = Poll.query.get(poll_id)
        if not poll:
                emit('comment_response', {'success': False, 'message': 'Poll not found.'})
                return

        new_comment = Comment(
                user_id=user_id,
                poll_id=poll_id,
                the_comment=comment_text
        )
        db.session.add(new_comment)
        db.session.commit()

        # Get the display_name from the user relationship
        comment_data = {
                'display_name': user.display_name, # Access display_name from the user object
                'the_comment': new_comment.the_comment
        }

        print(f"User {user.display_name} commented on poll {poll_id}: {comment_text}")

        # Emit the new comment to all clients (or to a specific room if implemented)
        emit('new_comment', comment_data, broadcast=True) 





@app.route('/account')
def account():
        user = User.query.get(session['user_id'])
        polls = Poll.query.filter_by(created_by=user.id).all() 
        return render_template("account.html",polls=polls)



@app.route('/account/createpoll', methods=['GET', 'POST'])
def create_poll():
        form = CreatePollForm()
        if form.validate_on_submit():
                new_poll = Poll(
                        question=form.question.data,
                        option_a=form.option_a.data,
                        option_b=form.option_b.data,
                        option_c=form.option_c.data if form.option_c.data else None,
                        option_d=form.option_d.data if form.option_d.data else None,
                        created_by=session['user_id'] # Assuming created_by is the user_id
                )
                db.session.add(new_poll)
                db.session.commit()
                flash("Poll created successfully!", "success")
                return redirect(url_for("account"))
        
        return render_template("createpoll.html",form=form)



@app.route('/login', methods=['GET', 'POST'])
def log_in():
        form = LoginForm()
        if form.validate_on_submit():
                user = User.query.filter_by(email=form.email.data).first()
                
                if user and check_password_hash(user.password, form.password.data):
                        if not user.is_verified: 
                                flash("Email not verified, another verification email has been send.","danger")
                                send_verification_email(user.email)
                                return redirect(url_for("log_in"))

                        new_token = str(uuid.uuid4())
                        user.session_token = new_token
                        db.session.commit()

                        session['user_id']=user.id
                        session['session_token']=new_token

                        flash("Successfully logged in!","success")
                        return redirect(url_for("index"))
                else:
                        flash("Invalid email or password.", "danger")

        return render_template("login.html", form=form)



@app.route('/signup', methods=['GET', 'POST'])
def sign_up():
        form = SignUpForm()
        if form.validate_on_submit():
                existing_user = User.query.filter_by(email=form.email.data).first()
                if existing_user:
                        flash("Email already exists","danger")
                        return redirect(url_for("sign_up"))
                
                hashed_password = generate_password_hash(form.password.data)
                new_user = User(
                        display_name = form.display_name.data,
                        email = form.email.data,
                        password = hashed_password,
                        is_verified = False
                )
                db.session.add(new_user)
                db.session.commit()
                send_verification_email(new_user.email)
                flash("Account created and is awaiting email verification","success")
                return redirect(url_for("log_in"))

        return render_template("signup.html",form=form)


@app.route('/confirm/<token>')
def confirm_email(token):
        email = confirm_token(token)
        if not email:
                return 'The confirmation link is invalid or has expired.'

        user = User.query.filter_by(email=email).first_or_404()
        if user.is_verified:
                return 'Account already verified.'

        user.is_verified = True
        db.session.commit()
        return 'Email verified! You can now log in.'



@app.route('/logout')
def log_out():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('log_in'))

@app.before_request
def check_session():
        if request.endpoint in ['static']:
                return

        user_id = session.get('user_id')
        token = session.get('session_token')

        if user_id:
                user = User.query.get(user_id)
                if not user or user.session_token != token:
                        session.clear()
                        flash("You were logged out due to another login or invalid session.", "warning")
                        return redirect(url_for('log_in'))

                if request.endpoint in ['log_in', 'sign_up']:
                        return redirect(url_for("index"))

@app.context_processor
def inject_logged_in():
        return {'logged_in': 'user_id' in session}

@app.context_processor
def inject_user():
    user_id = session.get('user_id')
    user = User.query.get(user_id) if user_id else None
    return dict(current_user=user)


if __name__ == '__main__':
        socketio.run(app,host='0.0.0.0',port=8000)