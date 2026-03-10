import sys
sys.path.insert(0, '..')
sys.path.insert(0, '.')

# Set up proper module path
import os
os.chdir('..')
sys.path.insert(0, 'api')

from db.database import get_db_session
from db.models import User

try:
    db = get_db_session()
    users = db.query(User).all()
    print("Users in database:")
    for user in users:
        print(f"  ID: {user.id}, Email: {user.email}, Name: {user.name}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
