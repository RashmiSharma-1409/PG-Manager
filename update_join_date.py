from app import app, db
from sqlalchemy import text

with app.app_context():

    db.session.execute(
        text("ALTER TABLE tenant ADD COLUMN join_date DATE")
    )

    db.session.execute(
        text("UPDATE tenant SET join_date = '2026-11-16'")
    )

    db.session.commit()

    print("Joining date updated successfully!")