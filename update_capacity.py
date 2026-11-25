
from app import app, db
from sqlalchemy import text

with app.app_context():

    db.session.execute(
        text("""
            ALTER TABLE room
            ADD COLUMN sharing_capacity INTEGER NOT NULL DEFAULT 3
        """)
    )

    db.session.commit()

    print("Room sharing capacity column added successfully.")

    db.session.execute(
        text("""
            UPDATE room
            SET sharing_capacity = 3
            WHERE room_number = 'G01'
        """)
    )

    db.session.commit()

    print("G01 updated as a 3-sharing room.")
