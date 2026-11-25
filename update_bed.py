
from app import app, db, Bed

with app.app_context():
    bed = db.session.execute(
        db.select(Bed).filter_by(
            bed_number="B1",
            room_id=1
        )
    ).scalar_one_or_none()

    if bed is None:
        print("Bed B1 not found.")

    else:
        bed.status = "Occupied"

        db.session.commit()

        print("Bed updated successfully!")
        print("Bed:", bed.bed_number)
        print("New status:", bed.status)
