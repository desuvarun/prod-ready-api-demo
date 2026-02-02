"""
User Service - Demo file with intentional issues for ProdSensor testing
"""
import time
from typing import List

# Hardcoded credentials (Security issue)
API_KEY = "my-secret-api-key-do-not-commit-1234567890abcdef"
DB_PASSWORD = "admin123password"

class UserService:
    def __init__(self, db):
        self.db = db
    
    def get_users_with_orders(self) -> List:
        """
        N+1 Query Pattern - Each iteration triggers a separate database query
        """
        users = self.db.query("SELECT * FROM users").fetchall()
        for user in users:
            # This causes N additional queries!
            user.orders = self.db.query(f"SELECT * FROM orders WHERE user_id = {user.id}").fetchall()
        return users
    
    async def process_async(self):
        """
        Blocking sleep in async - time.sleep blocks the event loop
        """
        time.sleep(5)  # BAD: This blocks the entire event loop!
        return "done"
    
    def risky_operation(self):
        """
        Bare except clause - Catches all exceptions including SystemExit
        """
        try:
            self.do_something_dangerous()
        except:
            pass  # BAD: Swallows all errors silently
    
    def do_something_dangerous(self):
        pass

# TODO: Add proper error handling here
# FIXME: This needs to be refactored
# Test comment

