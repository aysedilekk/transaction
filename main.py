from fastapi import FastAPI, Depends, HTTPException, Form, Path, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from db import SessionLocal, engine
from models import Base, User, Card, StatusEnum, Transaction
from utils import hash_password

app = FastAPI()

# Create db tables
Base.metadata.create_all(bind=engine)


# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
def index():
    return {"Welcome": "!!"}


@app.post("/register")
async def register(email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    # Check user exist or not
    user = db.query(User).filter(User.email == email).first()
    if user:
        raise HTTPException(status_code=404, detail="User already exist with this email address")
    else:
        # Create user
        new_user = User(email=email, password=hash_password(password))
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        # Create card for that user and set it as ACTIVE
        new_card = Card(label="Default Card", user_id=new_user.id, status='ACTIVE')
        db.add(new_card)
        db.commit()
        db.refresh(new_card)

        return {"user_id": new_user.id, "card_id": new_card.id}


@app.get("/users/{user_id}/cards")
async def list_cards(user_id: int, db: Session = Depends(get_db)):
    # Check if the user exists
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    # Retrieve cards for the user
    cards = (
        db.query(Card)
        .filter(Card.user_id == user_id, Card.status != StatusEnum.DELETED)
        .order_by(Card.date_modified.desc())
        .all()
    )

    return {"user_id": user_id,
            "cards": [{"id": card.id, "label": card.label, "card_no": card.card_no, "status": card.status} for card in
                      cards]}


@app.post("/users/{user_id}/cards")
async def create_card(
        user_id: int,
        label: str = Form(...),
        card_no: str = Form(None),
        db: Session = Depends(get_db)
):
    # Check if the user exists
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    # Check if the card number is unique
    if card_no and db.query(Card).filter(Card.card_no == card_no).first():
        raise HTTPException(status_code=400, detail="Card number already exists")

    # Create a new card
    new_card = Card(label=label, card_no=card_no, user_id=user_id, status=StatusEnum.ACTIVE)
    db.add(new_card)
    db.commit()
    db.refresh(new_card)

    return {"message": "Card created successfully", "card_id": new_card.id}


@app.delete("/users/{user_id}/cards/{card_id}")
async def delete_card(
        user_id: int,
        card_id: int = Path(..., title="The ID of the card to delete"),
        db: Session = Depends(get_db)
):

    # Check if the card exists
    card = db.query(Card).filter(Card.user_id == user_id, Card.id == card_id).first()
    if card is None:
        raise HTTPException(status_code=404, detail="Card not found")

    # Check if the user has at least one active card
    active_cards_count = db.query(Card).filter(Card.user_id == card.user_id, Card.status == StatusEnum.ACTIVE).count()
    if active_cards_count <= 1:
        raise HTTPException(status_code=400, detail="Cannot delete the last active card")

    # Soft-delete the card by updating its status to 'DELETED'
    card.status = StatusEnum.DELETED
    db.commit()

    return {"message": "Card deleted successfully"}


@app.put("/users/{user_id}/cards/{card_id}")
async def update_card(
        user_id: int,
        card_id: int = Path(..., title="The ID of the card to update"),
        label: str = Form(...),
        status: str = Form(None),
        card_no: str = Form(None),  # Allow card_no to be optional
        db: Session = Depends(get_db)
):
    # Check if the card exists
    card = db.query(Card).filter(Card.user_id == user_id, Card.id == card_id).first()
    if card is None:
        raise HTTPException(status_code=404, detail="Card not found")

    # Check if the card number already exists if provided
    if card_no and card_no != card.card_no:
        existing_card = db.query(Card).filter(Card.card_no == card_no).first()
        if existing_card:
            raise HTTPException(status_code=400, detail="Card number already exists")

    # Update the card
    card.label = label
    card.card_no = card_no
    card.status = status
    db.commit()

    return {"message": "Card updated successfully"}


@app.post("/users/{user_id}/transactions/perform-transaction")
async def perform_transaction(
        user_id: int,
        card_id: int = Form(...),
        amount: float = Form(...),
        description: str = Form(...),
        db: Session = Depends(get_db)
):
    # Check if the user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check if the card belongs to the user and is active
    card = db.query(Card).filter(Card.id == card_id, Card.user_id == user_id, Card.status == 'ACTIVE').first()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found or not active")

    # Create a new transaction
    new_transaction = Transaction(amount=amount, description=description, card_id=card.id)
    db.add(new_transaction)
    db.commit()
    db.refresh(new_transaction)

    return {
        "user_id": user_id,
        "card_id": card_id,
        "transaction_id": new_transaction.id,
        "amount": amount,
        "description": description,
    }


@app.get("/users/{user_id}/transactions/search")
async def search_transaction(
        user_id: int,
        label: str = Query(None, title="Label to filter by"),
        card_number: str = Query(None, title="Card number to filter by"),
        db: Session = Depends(get_db)
):
    # Check if the user exists
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    # Retrieve transactions with optional label and card number filtering
    transactions_query = db.query(Transaction).join(Card).filter(Card.user_id == user.id)
    if label:
        transactions_query = transactions_query.filter(Card.label.ilike(f"%{label}%"))
    if card_number:
        transactions_query = transactions_query.filter(Card.card_no.ilike(f"%{card_number}%"))

    transactions = transactions_query.all()

    return {"user_id": user.id, "transactions": transactions}


@app.get("/users/{user_id}/transactions/search/spending-statistics")
async def spending_statistics(user_id: int, db: Session = Depends(get_db)):

    # Check if the user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Retrieve spending statistics
    active_cards_count = db.query(Card).filter(Card.user_id == user.id, Card.status == 'ACTIVE').count()

    total_active_spending = (
            db.query(func.sum(Transaction.amount))
            .join(Card)
            .filter(Card.user_id == user.id, Card.status == 'ACTIVE')
            .scalar() or 0
    )

    total_passive_spending = (
            db.query(func.sum(Transaction.amount))
            .join(Card)
            .filter(Card.user_id == user.id, Card.status == 'PASSIVE')
            .scalar() or 0
    )

    return {
        "user_id": user.id,
        "active_cards_count": active_cards_count,
        "total_active_spending": total_active_spending,
        "total_passive_spending": total_passive_spending,
    }


# Run FastAPI
def run_fastapi():
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)


if __name__ == "__main__":
    run_fastapi()
