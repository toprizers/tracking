import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'server'))

from app import create_app, db
from models import User, Employee
import secrets


def setup_database():
    app = create_app()

    with app.app_context():
        db.create_all()

        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', role='admin')
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("[OK] Admin user created (admin/admin123)")
        else:
            print("[OK] Admin user already exists")

        print("\nDatabase setup complete!")
        print("You can now start the server with: python app.py")


def add_employee(name, email, department=None):
    app = create_app()

    with app.app_context():
        if Employee.query.filter_by(email=email).first():
            print(f"[ERROR] Employee with email {email} already exists!")
            return

        agent_key = secrets.token_hex(32)

        emp = Employee(
            name=name,
            email=email,
            department=department,
            agent_key=agent_key
        )
        db.session.add(emp)
        db.session.commit()

        print(f"\n[OK] Employee added successfully!")
        print(f"Name: {name}")
        print(f"Email: {email}")
        print(f"Agent Key: {agent_key}")
        print(f"\nGive this key to the employee to configure their agent.")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python setup.py init          - Initialize database")
        print("  python setup.py add <name> <email> [department]")
        sys.exit(1)

    command = sys.argv[1]

    if command == 'init':
        setup_database()
    elif command == 'add':
        if len(sys.argv) < 4:
            print("Usage: python setup.py add <name> <email> [department]")
            sys.exit(1)
        name = sys.argv[2]
        email = sys.argv[3]
        dept = sys.argv[4] if len(sys.argv) > 4 else None
        add_employee(name, email, dept)
    else:
        print(f"Unknown command: {command}")
