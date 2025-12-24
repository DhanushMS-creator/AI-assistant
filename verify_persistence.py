from server.database import SessionLocal, Base, engine
from server.models import User, Session as ChatSession, Message
from datetime import datetime

# Ensure tables exist
Base.metadata.create_all(bind=engine)

def verify_persistence():
    db = SessionLocal()
    try:
        # 1. Create User
        email = f"test_{int(datetime.now().timestamp())}@example.com"
        user = User(email=email, google_id=f"gid_{int(datetime.now().timestamp())}", name="Test User")
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"Created User: {user.id}")

        # 2. Create Session
        session = ChatSession(user_id=user.id, title="Test Session")
        db.add(session)
        db.commit()
        db.refresh(session)
        print(f"Created Session: {session.id}")

        # 3. Add Messages
        msg1 = Message(session_id=session.id, role="user", content="Hello")
        msg2 = Message(session_id=session.id, role="model", content="Hi there")
        db.add(msg1)
        db.add(msg2)
        db.commit()
        print("Added Messages")

        # 4. Query
        sObj = db.query(ChatSession).filter(ChatSession.id == session.id).first()
        assert sObj is not None
        assert len(sObj.messages) == 2
        print("Verification Successful: Session and Messages persisted.")

    except Exception as e:
        print(f"Verification Failed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    verify_persistence()
