
from app import app, db, Room

with app.app_context():
    room = db.session.execute(
        db.select(Room).filter_by(room_number="G01")
    ).scalar_one_or_none()

    if room is None:
        print("Room G01 not found.")

    else:
        room.room_number = "G001"

        db.session.commit()

        print("Room updated successfully:", room.room_number)
