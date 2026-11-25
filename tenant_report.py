
from app import app, db, Tenant, Bed, Room, Floor

with app.app_context():
    results = db.session.execute(
        db.select(Tenant, Bed, Room, Floor)
        .join(Bed, Tenant.bed_id == Bed.id)
        .join(Room, Bed.room_id == Room.id)
        .join(Floor, Room.floor_id == Floor.id)
    ).all()

    for tenant, bed, room, floor in results:
        print("Tenant:", tenant.name)
        print("Phone:", tenant.phone)
        print("Floor:", floor.floor_name)
        print("Room:", room.room_number)
        print("Bed:", bed.bed_number)
        print("Status:", bed.status)
        print("--------------------")
