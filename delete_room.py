
from app import app, db, Room

with app.app_context():
    room = db.session.execute(
        db.select(Room).filter_by(room_number="G01")
    ).scalar_one_or_none()

    if room is None:
        print("Room not found.")

    else:
        db.session.delete(room)
        db.session.commit()

        print("Room deleted.")
