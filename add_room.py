
from app import app, db, Floor, Room

with app.app_context():

    floor = db.session.execute(
        db.select(Floor).filter_by(floor_name="Ground Floor")
    ).scalar_one_or_none()

    if floor is None:
        print("Ground Floor not found. Add the floor first.")

    else:
        existing_room = db.session.execute(
            db.select(Room).filter_by(room_number="G01")
        ).scalar_one_or_none()

        if existing_room:
            print("Room G01 already exists.")

        else:
            room = Room(
                room_number="G01",
                floor_id=floor.id
            )

            db.session.add(room)
            db.session.commit()

            print("Room saved:", room.room_number, "Floor ID:", room.floor_id)
