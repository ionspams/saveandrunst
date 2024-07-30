# app.py
import streamlit as st
from sqlalchemy.orm import Session
from database import SessionLocal, Beneficiary, Case, Referral, ServiceProvider

# Utility function to get a database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Streamlit app
st.title("Dopomoha Case Manager with Referrals")

# Add a new beneficiary
st.header("Add a New Beneficiary")
with st.form("beneficiary_form"):
    name = st.text_input("Name")
    contact_info = st.text_input("Contact Info")
    household_details = st.text_area("Household Details")
    special_needs = st.text_area("Special Needs")
    profile_status = st.selectbox("Profile Status", ["Active", "Inactive"])
    submitted = st.form_submit_button("Add Beneficiary")

    if submitted:
        with next(get_db()) as db:
            new_beneficiary = Beneficiary(
                name=name,
                contact_info=contact_info,
                household_details=household_details,
                special_needs=special_needs,
                profile_status=profile_status
            )
            db.add(new_beneficiary)
            db.commit()
            st.success("Beneficiary added successfully")

# Add a new case
st.header("Add a New Case")
with st.form("case_form"):
    beneficiary_id = st.number_input("Beneficiary ID", min_value=1)
    case_status = st.text_input("Case Status")
    assigned_to = st.text_input("Assigned To")
    submitted = st.form_submit_button("Add Case")

    if submitted:
        with next(get_db()) as db:
            new_case = Case(
                beneficiary_id=beneficiary_id,
                case_status=case_status,
                assigned_to=assigned_to
            )
            db.add(new_case)
            db.commit()
            st.success("Case added successfully")

# Add a new referral
st.header("Add a New Referral")
with st.form("referral_form"):
    case_id = st.number_input("Case ID", min_value=1)
    service_provider = st.text_input("Service Provider")
    status = st.text_input("Status")
    submitted = st.form_submit_button("Add Referral")

    if submitted:
        with next(get_db()) as db:
            new_referral = Referral(
                case_id=case_id,
                service_provider=service_provider,
                status=status
            )
            db.add(new_referral)
            db.commit()
            st.success("Referral added successfully")

# View all beneficiaries
st.header("View Beneficiaries")
with next(get_db()) as db:
    beneficiaries = db.query(Beneficiary).all()
    for beneficiary in beneficiaries:
        st.write(f"ID: {beneficiary.id}, Name: {beneficiary.name}, Contact Info: {beneficiary.contact_info}, Profile Status: {beneficiary.profile_status}")

# View all cases
st.header("View Cases")
with next(get_db()) as db:
    cases = db.query(Case).all()
    for case in cases:
        st.write(f"ID: {case.id}, Beneficiary ID: {case.beneficiary_id}, Case Status: {case.case_status}, Assigned To: {case.assigned_to}")

# View all referrals
st.header("View Referrals")
with next(get_db()) as db:
    referrals = db.query(Referral).all()
    for referral in referrals:
        st.write(f"ID: {referral.id}, Case ID: {referral.case_id}, Service Provider: {referral.service_provider}, Status: {referral.status}")

if __name__ == "__main__":
    st.run()
