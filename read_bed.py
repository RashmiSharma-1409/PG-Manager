
from app import app, db, Bed

with app.app_context():
    beds = db.session.execute(
        db.select(Bed)
    ).scalars().all()

    for bed in beds:
        print(
            "Bed ID:", bed.id,
            "| Bed Number:", bed.bed_number,
            "| Room ID:", bed.room_id,
            "| Status:", bed.status
        )
