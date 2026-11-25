
from app import app, db, Floor

with app.app_context():
    floor = Floor(floor_name="Ground Floor")

    db.session.add(floor)
    db.session.commit()

    print("Floor saved:", floor.id, floor.floor_name)
