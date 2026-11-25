
from app import app, db, Room

with app.app_context():
    rooms = db.session.execute(
        db.select(Room)
    ).scalars().all()

    for room in rooms:
        print(
            "Room ID:", room.id,
            "| Room Number:", room.room_number,
            "| Floor ID:", room.floor_id,
            "| Sharing Capacity:", room.sharing_capacity
        )
