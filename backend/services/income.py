from sqlalchemy.orm import Session

from backend.models import IncomeRecord


def get_income_history(worker_id: str, db: Session) -> list[dict]:
    records = (
        db.query(IncomeRecord)
        .filter(IncomeRecord.worker_id == worker_id)
        .order_by(IncomeRecord.date.asc())
        .all()
    )

    return [
        {
            "date": record.date,
            "income": record.amount,
        }
        for record in records
    ]