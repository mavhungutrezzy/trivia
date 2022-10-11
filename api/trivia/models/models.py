from database.database import db


class Category(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    questions = db.relationship("Question", backref="category", lazy=True)

    def add(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def update(self):
        db.session.commit()

    def __repr__(self):
        return f"Category {self.name}"

    def format(self):
        return {"id": self.id, "name": self.name}


class Question(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(), unique=True, nullable=False)
    answer = db.Column(db.String(), nullable=False)
    difficulty = db.Column(db.Integer, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"), nullable=False)

    def __init__(self, question, answer, difficulty, category_id):
        self.question = question
        self.answer = answer
        self.category_id = category_id
        self.difficulty = difficulty

    def add(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def update(self):
        db.session.commit()

    def __repr__(self):
        return f"Question {self.question}"

    def format(self):
        return {
            "id": self.id,
            "question": self.question,
            "answer": self.answer,
            "difficulty": self.difficulty,
            "category": self.category_id,
        }
