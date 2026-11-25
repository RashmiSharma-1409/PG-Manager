from app import app, db, Tenant, calculate_monthly_rent

with app.app_context():
    tenant = db.session.get(Tenant, 1)

    if tenant:
        rent = calculate_monthly_rent(tenant)
        print("Monthly Rent: ₹", rent)
    else:
        print("Tenant not found.")