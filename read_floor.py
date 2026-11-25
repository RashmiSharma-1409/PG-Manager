
from app import app, db, Floor

with app.app_context():
    floors = db.session.execute(
        db.select(Floor)
    ).scalars().all()

    for floor in floors:
        print(floor.id, floor.floor_name)
