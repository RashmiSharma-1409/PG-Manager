
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
        bed.status = "Vacant"
        db.session.commit()
        print("Bed B1 is now Vacant.")
