
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import date
import calendar

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///pg_manager.db"

db = SQLAlchemy(app)


# -------------------- DATABASE MODELS --------------------

class Floor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    floor_name = db.Column(db.String(50), unique=True, nullable=False)


class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_number = db.Column(db.String(20), unique=True, nullable=False)
    floor_id = db.Column(db.Integer, db.ForeignKey("floor.id"), nullable=False)
    sharing_capacity = db.Column(db.Integer, nullable=False)


class Bed(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bed_number = db.Column(db.String(20), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey("room.id"), nullable=False)
    status = db.Column(db.String(20), default="Vacant", nullable=False)


class Tenant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    bed_id = db.Column(db.Integer, db.ForeignKey("bed.id"), nullable=False)
    join_date = db.Column(db.Date, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    checkout_date = db.Column(db.Date, nullable=True)


class Fee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey("tenant.id"), nullable=False)
    billing_month = db.Column(db.String(7), nullable=False)
    amount_due = db.Column(db.Numeric(10, 2), nullable=False)
    amount_paid = db.Column(db.Numeric(10, 2), default=0, nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    paid_on = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(20), default="Pending", nullable=False)

    __table_args__ = (
        db.UniqueConstraint(
            "tenant_id",
            "billing_month",
            name="unique_tenant_month_fee"
        ),
    )


class JoiningCharge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(
        db.Integer,
        db.ForeignKey("tenant.id"),
        nullable=False,
        unique=True
    )
    total_amount = db.Column(db.Numeric(10, 2), default=3000)
    refundable_amount = db.Column(db.Numeric(10, 2), default=1500)
    maintenance_amount = db.Column(db.Numeric(10, 2), default=1500)
    paid = db.Column(db.Boolean, default=False, nullable=False)


# -------------------- RENT CALCULATIONS --------------------

RENT_BY_SHARING = {
    2: 9000,
    3: 8000,
    4: 7000
}


def calculate_monthly_rent(tenant):
    bed = db.session.get(Bed, tenant.bed_id)
    room = db.session.get(Room, bed.room_id)

    return RENT_BY_SHARING.get(room.sharing_capacity)


def get_monthly_due_date(join_date, months_after_joining):
    total_months = (
        join_date.year * 12
        + join_date.month - 1
        + months_after_joining
    )

    year = total_months // 12
    month = total_months % 12 + 1

    last_day = calendar.monthrange(year, month)[1]
    due_day = min(join_date.day, last_day)

    return date(year, month, due_day)


# -------------------- DASHBOARD --------------------

@app.route("/")
def home():
    today = date.today()

    tenants = db.session.execute(
        db.select(Tenant).where(Tenant.is_active == True)
    ).scalars().all()

    for tenant in tenants:

        months_passed = (
            (today.year - tenant.join_date.year) * 12
            + today.month - tenant.join_date.month
        )

        months_after_joining = max(1, months_passed)

        due_date = get_monthly_due_date(
            tenant.join_date,
            months_after_joining
        )

        # Billing month is based on the rent due date
        billing_month = due_date.strftime("%Y-%m")

        existing_fee = db.session.execute(
            db.select(Fee).where(
                Fee.tenant_id == tenant.id,
                Fee.billing_month == billing_month
            )
        ).scalar_one_or_none()

        if not existing_fee:
            rent = calculate_monthly_rent(tenant)

            new_fee = Fee(
                tenant_id=tenant.id,
                billing_month=billing_month,
                amount_due=rent,
                amount_paid=0,
                due_date=due_date,
                status="Pending"
            )

            db.session.add(new_fee)

    db.session.commit()

    # Find all unpaid rent whose due date has arrived
    pending_fees = db.session.execute(
        db.select(Fee, Tenant)
        .join(Tenant, Fee.tenant_id == Tenant.id)
        .where(
            Tenant.is_active == True,
            Fee.due_date <= today,
            Fee.amount_paid < Fee.amount_due
        )
    ).all()

    total_tenants = len(tenants)
    total_rooms = db.session.query(Room).count()
    total_beds = db.session.query(Bed).count()

    occupied_beds = db.session.query(Bed).filter_by(
        status="Occupied"
    ).count()

    vacant_beds = total_beds - occupied_beds

    pending_amount = sum(
        float(fee.amount_due - fee.amount_paid)
        for fee, tenant in pending_fees
    )

    return render_template(
        "dashboard.html",
        pending_fees=pending_fees,
        today=today,
        total_tenants=total_tenants,
        total_rooms=total_rooms,
        total_beds=total_beds,
        occupied_beds=occupied_beds,
        vacant_beds=vacant_beds,
        pending_amount=pending_amount
    )


# -------------------- TENANT REPORT --------------------

@app.route("/tenants")
def tenant_report():

    active_results = db.session.execute(
        db.select(Tenant, Bed, Room, Floor)
        .join(Bed, Tenant.bed_id == Bed.id)
        .join(Room, Bed.room_id == Room.id)
        .join(Floor, Room.floor_id == Floor.id)
        .where(Tenant.is_active == True)
    ).all()

    previous_results = db.session.execute(
        db.select(Tenant, Bed, Room, Floor)
        .join(Bed, Tenant.bed_id == Bed.id)
        .join(Room, Bed.room_id == Room.id)
        .join(Floor, Room.floor_id == Floor.id)
        .where(Tenant.is_active == False)
    ).all()

    return render_template(
        "tenants.html",
        active_results=active_results,
        previous_results=previous_results
    )


# -------------------- ADD TENANT --------------------

@app.route("/add-tenant", methods=["GET", "POST"])
def add_tenant_page():

    if request.method == "POST":

        name = request.form.get("name")
        phone = request.form.get("phone")
        bed_id = request.form.get("bed_id")
        join_date = request.form.get("join_date")

        bed = db.session.get(Bed, int(bed_id)) if bed_id else None

        if not name or not phone or not bed or not join_date:
            return "Please enter all tenant details."

        if bed.status != "Vacant":
            return "This bed is not available. Please select another bed."

        new_tenant = Tenant(
            name=name,
            phone=phone,
            bed_id=bed.id,
            join_date=date.fromisoformat(join_date)
        )

        bed.status = "Occupied"

        db.session.add(new_tenant)
        db.session.commit()

        return redirect(url_for("tenant_report"))

    beds = db.session.execute(
        db.select(Bed).where(Bed.status == "Vacant")
    ).scalars().all()

    return render_template("add_tenant.html", beds=beds)


# -------------------- EDIT TENANT --------------------

@app.route("/edit-tenant/<int:tenant_id>", methods=["GET", "POST"])
def edit_tenant(tenant_id):

    tenant = db.session.get(Tenant, tenant_id)

    if tenant is None:
        return "Tenant not found."

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        phone = request.form.get("phone", "").strip()

        if not name or not phone:
            return "Name and phone number are required."

        tenant.name = name
        tenant.phone = phone

        db.session.commit()

        return redirect(url_for("tenant_report"))

    return render_template("edit_tenant.html", tenant=tenant)


# -------------------- CHECKOUT TENANT --------------------

@app.route("/checkout-tenant/<int:tenant_id>", methods=["POST"])
def checkout_tenant(tenant_id):

    tenant = db.session.get(Tenant, tenant_id)

    if tenant is None:
        return "Tenant not found."

    if not tenant.is_active:
        return "Tenant has already checked out."

    bed = db.session.get(Bed, tenant.bed_id)

    if bed:
        bed.status = "Vacant"

    tenant.is_active = False
    tenant.checkout_date = date.today()

    db.session.commit()

    return redirect(url_for("tenant_report"))

# -------------------- PAYMENTS --------------------

@app.route("/payments", methods=["GET", "POST"])
def payments():

    tenants = db.session.execute(
        db.select(Tenant)
    ).scalars().all()

    for tenant in tenants:

        charge = db.session.execute(
            db.select(JoiningCharge).where(
                JoiningCharge.tenant_id == tenant.id
            )
        ).scalar_one_or_none()

        if not charge:
            db.session.add(JoiningCharge(tenant_id=tenant.id))

    db.session.commit()

    if request.method == "POST":

        payment_type = request.form.get("payment_type")
        record_id = request.form.get("record_id")
        action = request.form.get("action")

        if not record_id or action not in ["paid", "due"]:
            return "Invalid payment action."

        if payment_type == "joining":

            charge = db.session.get(JoiningCharge, int(record_id))

            if charge:
                charge.paid = (action == "paid")

        elif payment_type == "rent":

            fee = db.session.get(Fee, int(record_id))

            if fee:
                if action == "paid":
                    fee.amount_paid = fee.amount_due
                    fee.status = "Paid"
                    fee.paid_on = date.today()
                else:
                    fee.amount_paid = 0
                    fee.status = "Pending"
                    fee.paid_on = None

        else:
            return "Invalid payment type."

        db.session.commit()
        return redirect(url_for("payments"))

    joining_charges = db.session.execute(
        db.select(JoiningCharge, Tenant)
        .join(Tenant, JoiningCharge.tenant_id == Tenant.id)
    ).all()

    rent_records = db.session.execute(
        db.select(Fee, Tenant)
        .join(Tenant, Fee.tenant_id == Tenant.id)
        .order_by(Fee.due_date.desc())
    ).all()

    return render_template(
        "payments.html",
        joining_charges=joining_charges,
        rent_records=rent_records
    )


# -------------------- OCCUPANCY REPORT --------------------

@app.route("/occupancy")
def occupancy():

    floors = db.session.execute(
        db.select(Floor).order_by(Floor.floor_name)
    ).scalars().all()

    report = []

    for floor in floors:

        rooms = db.session.execute(
            db.select(Room).where(Room.floor_id == floor.id)
        ).scalars().all()

        room_details = []

        for room in rooms:

            beds = db.session.execute(
                db.select(Bed).where(Bed.room_id == room.id)
            ).scalars().all()

            bed_details = []

            for bed in beds:

                tenant = db.session.execute(
                    db.select(Tenant).where(
                        Tenant.bed_id == bed.id,
                        Tenant.is_active == True
                    )
                ).scalar_one_or_none()

                bed_details.append({
                    "bed": bed,
                    "tenant": tenant
                })

            occupied = sum(
                1 for item in bed_details if item["tenant"]
            )

            room_details.append({
                "room": room,
                "beds": bed_details,
                "occupied": occupied,
                "vacant": len(beds) - occupied
            })

        report.append({
            "floor": floor,
            "rooms": room_details
        })

    return render_template("occupancy.html", report=report)


# -------------------- MANAGE FLOORS, ROOMS AND BEDS --------------------

@app.route("/manage-rooms", methods=["GET", "POST"])
def manage_rooms():

    message = ""

    if request.method == "POST":

        action = request.form.get("action")

        # Add floor
        if action == "add_floor":

            floor_name = request.form.get("floor_name", "").strip()

            existing = db.session.execute(
                db.select(Floor).where(Floor.floor_name == floor_name)
            ).scalar_one_or_none()

            if not floor_name:
                message = "Please enter a floor name."

            elif existing:
                message = "This floor already exists."

            else:
                db.session.add(Floor(floor_name=floor_name))
                db.session.commit()
                return redirect(url_for("manage_rooms"))

        # Add room and automatically create beds
        elif action == "add_room":

            room_number = request.form.get("room_number", "").strip()
            floor_id = request.form.get("floor_id")
            capacity = request.form.get("capacity")

            try:
                floor = db.session.get(Floor, int(floor_id))
                capacity = int(capacity)
            except (ValueError, TypeError):
                floor = None
                capacity = 0

            existing = db.session.execute(
                db.select(Room).where(Room.room_number == room_number)
            ).scalar_one_or_none()

            if not room_number or not floor:
                message = "Enter a room number and select a valid floor."

            elif existing:
                message = "This room number already exists."

            elif capacity not in [2, 3, 4]:
                message = "Sharing capacity must be 2, 3 or 4."

            else:
                room = Room(
                    room_number=room_number,
                    floor_id=floor.id,
                    sharing_capacity=capacity
                )

                db.session.add(room)
                db.session.flush()

                for number in range(1, capacity + 1):
                    db.session.add(
                        Bed(
                            bed_number=f"B{number}",
                            room_id=room.id,
                            status="Vacant"
                        )
                    )

                db.session.commit()
                return redirect(url_for("manage_rooms"))

        # Add missing beds
        elif action == "add_beds":

            try:
                room = db.session.get(
                    Room, int(request.form.get("room_id"))
                )
            except (ValueError, TypeError):
                room = None

            if not room:
                message = "Room not found."

            else:
                existing_count = db.session.query(Bed).filter_by(
                    room_id=room.id
                ).count()

                if existing_count >= room.sharing_capacity:
                    message = "This room already has all its beds."

                else:
                    for number in range(
                        existing_count + 1,
                        room.sharing_capacity + 1
                    ):
                        db.session.add(
                            Bed(
                                bed_number=f"B{number}",
                                room_id=room.id,
                                status="Vacant"
                            )
                        )

                    db.session.commit()
                    return redirect(url_for("manage_rooms"))

    floors = db.session.execute(
        db.select(Floor).order_by(Floor.id)
    ).scalars().all()

    rooms = db.session.execute(
        db.select(Room).order_by(Room.id)
    ).scalars().all()

    room_rows = []

    for room in rooms:

        floor = db.session.get(Floor, room.floor_id)

        bed_count = db.session.query(Bed).filter_by(
            room_id=room.id
        ).count()

        room_rows.append({
            "room": room,
            "floor": floor,
            "bed_count": bed_count
        })

    return render_template(
        "manage_rooms.html",
        floors=floors,
        room_rows=room_rows,
        message=message
    )


# -------------------- DELETE ROOM --------------------

@app.route("/delete-room/<int:room_id>", methods=["POST"])
def delete_room(room_id):

    room = db.session.get(Room, room_id)

    if room is None:
        return "Room not found."

    beds = db.session.execute(
        db.select(Bed).where(Bed.room_id == room.id)
    ).scalars().all()

    for bed in beds:

        tenant_exists = db.session.execute(
            db.select(Tenant.id)
            .where(Tenant.bed_id == bed.id)
            .limit(1)
        ).scalar_one_or_none()

        if tenant_exists:
            return "Cannot delete: tenant history exists for this room."

    for bed in beds:
        db.session.delete(bed)

    db.session.delete(room)
    db.session.commit()

    return redirect(url_for("manage_rooms"))


# -------------------- RUN APPLICATION --------------------

if __name__ == "__main__":

    with app.app_context():
        db.create_all()

    app.run(debug=True)
