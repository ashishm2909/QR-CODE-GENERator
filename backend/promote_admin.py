import os
import sys
from src import create_app
from src.models import db, User

def promote_user(email):
    app = create_app(os.getenv('FLASK_ENV', 'development'))
    with app.app_context():
        user = User.query.filter_by(email=email).first()
        if not user:
            print(f"Error: User with email {email} not found.")
            return
        
        user.is_admin = True
        db.session.commit()
        print(f"Success: User {email} has been promoted to admin.")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python promote_admin.py <email>")
    else:
        promote_user(sys.argv[1])
