from sqlalchemy.orm import Session
from model.employment import Employment

# 多条件查询
def query_employment(
    db: Session,
    emp_id: int = None,
    stu_id: int = None,
    stu_name: str = None,
    company: str = None,
    min_salary: float = None,
    max_salary: float = None,
    skip: int = 0,
    limit: int = 50
):
    query = db.query(Employment).filter(Employment.is_deleted == 0)

    if emp_id is not None:
        query = query.filter(Employment.emp_id == emp_id)
    if stu_id is not None:
        query = query.filter(Employment.stu_id == stu_id)
    if stu_name is not None:
        query = query.filter(Employment.stu_name== stu_name)
    if company is not None:
        query = query.filter(Employment.company==company)
    if min_salary is not None:
        query = query.filter(Employment.salary >= min_salary)
    if max_salary is not None:
        query = query.filter(Employment.salary <= max_salary)

    query = query.order_by(Employment.emp_id)
    return query.offset(skip).limit(limit).all()


# 修改
def update_employment(db: Session, employment, update_data):
    try:
        update_dict = update_data.dict(exclude_unset=True)
        for key, value in update_dict.items():
            if hasattr(employment, key):
                setattr(employment, key, value)
        db.commit()
        db.refresh(employment)
        return True
    except Exception:
        db.rollback()
        return False

# 逻辑删除
def delete_employment(db: Session, employment: Employment):
    try:
        employment.is_deleted = 1
        db.commit()
        return True
    except Exception:
        db.rollback()
        return False