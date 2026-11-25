
from app import app, db, Tenant, Bed

with app.app_context():
    tenants = db.session.execute(
        db.select(Tenant)
    ).scalars().all()

    for tenant in tenants:
        bed = db.session.get(Bed, tenant.bed_id)

        print("Tenant ID:", tenant.id)
        print("Name:", tenant.name)
        print("Phone:", tenant.phone)

        if bed:
            print("Bed:", bed.bed_number)
            print("Bed status:", bed.status)

        print("--------------------")
