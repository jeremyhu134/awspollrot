from database import db


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    display_name = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    polls_created = db.relationship('Poll', backref='creator', lazy=True)

    votes = db.relationship('Vote', backref='voter', lazy=True)

    session_token = db.Column(db.String(36), nullable=True)

    is_verified = db.Column(db.Boolean, default=False)

    comments = db.relationship('Comment', backref='commenter', lazy=True)


class Poll(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(255), nullable=False)
    option_a = db.Column(db.String(100), nullable=False)
    option_b = db.Column(db.String(100), nullable=False)
    option_c = db.Column(db.String(100), nullable=True)
    option_d = db.Column(db.String(100), nullable=True)

    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    votes = db.relationship('Vote', backref='poll', lazy=True, cascade="all, delete-orphan")

    comments = db.relationship('Comment', backref='poll', lazy=True, cascade="all, delete-orphan")



class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    poll_id = db.Column(db.Integer, db.ForeignKey('poll.id'), nullable=False)

    selected_option = db.Column(db.String(1), nullable=False)



class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    poll_id = db.Column(db.Integer, db.ForeignKey('poll.id'), nullable=False)

    # Store selected option as string (e.g., "A", "B", etc.)
    the_comment = db.Column(db.String(250), nullable=False)