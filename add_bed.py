
from app import app, db, Room, Bed

with app.app_context():
    room = db.session.execute(
        db.select(Room).filter_by(room_number="G01")
    ).scalar_one_or_none()

    if room is None:
        print("Room G01 not found.")

    else:
        existing_bed = db.session.execute(
            db.select(Bed).filter_by(
                bed_number="B2",
                room_id=room.id
            )
        ).scalar_one_or_none()

        if existing_bed:
            print("Bed B2 already exists in G01.")

        else:
            bed = Bed(
                bed_number="B2",
                room_id=room.id
            )

            db.session.add(bed)
            db.session.commit()

            print("Bed saved:", bed.bed_number)
            print("Room ID:", bed.room_id)
            print("Status:", bed.status)
