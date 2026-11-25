
from app import app, db, Bed, Tenant

with app.app_context():
    bed = db.session.get(Bed, 1)

    if bed is None:
        print("Bed ID 1 not found.")

    elif bed.status != "Vacant":
        print("Bed is not vacant. Cannot assign tenant.")

    else:
        existing_tenant = db.session.execute(
            db.select(Tenant).filter_by(bed_id=bed.id)
        ).scalar_one_or_none()

        if existing_tenant:
            print("This bed already has a tenant.")

        else:
            tenant = Tenant(
                name="Priya",
                phone="9876543210",
                bed_id=bed.id
            )

            db.session.add(tenant)
            bed.status = "Occupied"
            db.session.commit()

            print("Tenant saved:", tenant.name)
            print("Assigned bed:", bed.bed_number)
            print("Bed status:", bed.status)
