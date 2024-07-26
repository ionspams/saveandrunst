import streamlit as st
from sqlalchemy import create_engine, Column, Integer, String, Boolean, inspect
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.exc import OperationalError
from werkzeug.security import generate_password_hash, check_password_hash
import pandas as pd
import openai

# Configure Database
DATABASE_URL = 'sqlite:///users.db'
Base = declarative_base()
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

# User Model
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(150), unique=True, nullable=False)
    password = Column(String(150), nullable=False)
    role = Column(String(50), nullable=False, default="user")
    assistant = Column(String(150), nullable=True)
    api_key = Column(String(150), nullable=True)
    first_login = Column(Boolean, default=True)

Base.metadata.create_all(engine)

# Update database schema to add new columns if they don't exist
def update_schema():
    inspector = inspect(engine)
    columns = [column['name'] for column in inspector.get_columns('users')]

    with engine.connect() as conn:
        if 'api_key' not in columns:
            conn.execute("ALTER TABLE users ADD COLUMN api_key VARCHAR(150)")
        if 'first_login' not in columns:
            conn.execute("ALTER TABLE users ADD COLUMN first_login BOOLEAN DEFAULT TRUE")

try:
    update_schema()
except OperationalError as e:
    st.warning(f"Schema update failed: {e}")

# User Authentication
def authenticate(username, password):
    user = session.query(User).filter_by(username=username).first()
    if user and check_password_hash(user.password, password):
        return user
    return None

# Register User
def register_user(username, password, role="user"):
    hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
    new_user = User(username=username, password=hashed_password, role=role)
    session.add(new_user)
    session.commit()

# Check if there is a superadmin, if not create one
def create_superadmin():
    superadmin_email = 'superadmin'
    superadmin = session.query(User).filter_by(username=superadmin_email).first()
    if not superadmin:
        register_user(superadmin_email, 'superadminpassword', role="superadmin")
create_superadmin()

# Main App
def main():
    st.title("Assistant Management System")

    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False

    if st.session_state['logged_in']:
        user_role = st.session_state['role']
        if user_role == 'superadmin' and st.session_state.get('first_login', False):
            change_superadmin_password()
        elif user_role == 'superadmin':
            superadmin_dashboard()
        elif user_role == 'admin':
            admin_dashboard()
        else:
            user = session.query(User).filter_by(username=st.session_state['username']).first()
            user_dashboard(user)
    else:
        menu = ["Login", "Register"]
        choice = st.sidebar.selectbox("Menu", menu)

        if choice == "Login":
            st.subheader("Login Section")

            username = st.text_input("Username")
            password = st.text_input("Password", type='password')
            if st.button("Login"):
                user = authenticate(username, password)
                if user:
                    st.session_state['logged_in'] = True
                    st.session_state['username'] = user.username
                    st.session_state['role'] = user.role
                    if user.role == 'superadmin' and user.first_login:
                        st.session_state['first_login'] = True
                        change_superadmin_password()
                    elif user.role == 'superadmin':
                        superadmin_dashboard()
                    elif user.role == 'admin':
                        admin_dashboard()
                    else:
                        user_dashboard(user)
                else:
                    st.warning("Invalid Username/Password")

        elif choice == "Register":
            st.subheader("Create New Account")
            new_username = st.text_input("Username")
            new_password = st.text_input("Password", type='password')
            if st.button("Register"):
                register_user(new_username, new_password)
                st.success("You have successfully created an account.")
                st.info("Go to Login Menu to login.")

def change_superadmin_password():
    st.subheader("Change Superadmin Password")
    new_password = st.text_input("New Password", type='password')
    confirm_password = st.text_input("Confirm Password", type='password')
    if st.button("Change Password"):
        if new_password == confirm_password:
            user = session.query(User).filter_by(username='superadmin').first()
            user.password = generate_password_hash(new_password, method='pbkdf2:sha256')
            user.first_login = False
            session.commit()
            st.session_state['first_login'] = False
            st.success("Password changed successfully")
            superadmin_dashboard()
        else:
            st.error("Passwords do not match")

def logout():
    st.session_state['logged_in'] = False
    st.session_state['username'] = None
    st.session_state['role'] = None

def superadmin_dashboard():
    st.subheader("Superadmin Dashboard")
    if st.button("Logout"):
        logout()

    st.write("Superadmin-specific controls go here")

    users = session.query(User).all()
    for user in users:
        st.write(f"Username: {user.username}, Role: {user.role}, Assistant: {user.assistant}")
        if st.button(f"Promote to Admin {user.username}", key=f"promote_{user.id}"):
            user.role = 'admin'
            session.commit()
            st.success(f"Promoted {user.username} to Admin")

        if st.button(f"Assign Assistant to {user.username}", key=f"button_{user.id}"):
            assistant_name = st.selectbox(f"Assistant for {user.username}", ["Assistant 1", "Assistant 2"], key=f"select_{user.id}")
            if st.button(f"Submit Assistant for {user.username}", key=f"submit_{user.id}"):
                user.assistant = assistant_name
                session.commit()
                st.success(f"Assigned {assistant_name} to {user.username}")

    col1, col2 = st.columns(2)

    # Add new user
    if col1.button("➕ Add User", use_container_width=True):
        add_user_dialog()

    # Delete user
    if col2.button("➖ Delete User", use_container_width=True):
        delete_user_dialog()

    # Update app view with the modified dataframe
    st.dataframe(pd.DataFrame.from_dict({user.username: {"role": user.role, "assistant": user.assistant} for user in users}, orient="index"), use_container_width=True)

def admin_dashboard():
    st.subheader("Admin Dashboard")
    if st.button("Logout"):
        logout()

    st.subheader("Manage Your Assistants")
    api_key = st.text_input("Enter your OpenAI API key", type='password')
    if st.button("Save API Key"):
        user = session.query(User).filter_by(username=st.session_state['username']).first()
        user.api_key = api_key
        session.commit()
        st.success("API Key saved successfully")

    users = session.query(User).filter_by(role='user').all()
    for user in users:
        st.write(f"Username: {user.username}, Assistant: {user.assistant}")
        if st.button(f"Assign Assistant to {user.username}", key=f"button_{user.id}"):
            assistant_name = st.selectbox(f"Assistant for {user.username}", ["Assistant 1", "Assistant 2"], key=f"select_{user.id}")
            if st.button(f"Submit Assistant for {user.username}", key=f"submit_{user.id}"):
                user.assistant = assistant_name
                session.commit()
                st.success(f"Assigned {assistant_name} to {user.username}")

def add_user_dialog():
    st.subheader("Add a new user")
    name = st.text_input("Name")
    password = st.text_input("Password", type='password')
    role = st.selectbox("Role", ["user", "admin"])

    if st.button("Add User"):
        if name and password and role:
            existing_user = session.query(User).filter_by(username=name).first()
            if existing_user:
                st.error(f"User with name `{name}` already exists.")
            else:
                register_user(name, password, role)
                st.success(f"User `{name}` added successfully.")
        else:
            st.error("Please fill in all fields.")

def delete_user_dialog():
    st.subheader("Delete an existing user")
    name_to_delete = st.text_input("Name")

    if st.button("Delete User"):
        user_to_delete = session.query(User).filter_by(username=name_to_delete).first()
        if user_to_delete:
            session.delete(user_to_delete)
            session.commit()
            st.success(f"User `{name_to_delete}` deleted successfully.")
        else:
            st.error(f"No user found with name `{name_to_delete}`")

def user_dashboard(user):
    st.subheader(f"User Dashboard for {user.username}")
    st.write(f"Your assistant is: {user.assistant}")
    if st.button("Logout"):
        logout()
    
    if user.assistant:
        st.write(f"You are now interacting with {user.assistant}")
        prompt = st.text_input("Ask your assistant:")
        if st.button("Submit"):
            if user.api_key:
                if user.assistant == "Assistant 1":
                    response = assistant_1(prompt, user.api_key)
                elif user.assistant == "Assistant 2":
                    response = assistant_2(prompt, user.api_key)
                else:
                    response = "Assistant not recognized"
                st.write(response)
            else:
                st.error("No API key provided.")
    else:
        st.write("No assistant assigned. You can use the general assistant.")
        prompt = st.text_input("Ask the general assistant:")
        if st.button("Submit"):
            user_api_key = user.api_key if user.api_key else "your_default_openai_key"
            response = get_openai_response(prompt, user_api_key, "General Assistant")
            st.write(response)

def get_openai_response(prompt, api_key, assistant_name):
    openai.api_key = api_key
    try:
        response = openai.Completion.create(
            engine="davinci",  # or another model you use for the assistant
            prompt=f"{assistant_name}: {prompt}",
            max_tokens=150
        )
        return response.choices[0].text.strip()
    except Exception as e:
        return f"Error: {e}"

def assistant_1(prompt, api_key):
    return get_openai_response(prompt, api_key, "Assistant 1")

def assistant_2(prompt, api_key):
    return get_openai_response(prompt, api_key, "Assistant 2")

if __name__ == '__main__':
    main()
