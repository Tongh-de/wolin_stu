from sqlalchemy.orm import Session
from sqlalchemy import func
from model.employment import Employment


class EmploymentService:
    @staticmethod
    def get_all_employments(db: Session):
        """获取所有未删除的就业信息"""
        return db.query(Employment).filter(Employment.is_deleted == False).all()

    @staticmethod
    def get_employment_by_stu_id(db: Session, stu_id: int):
        return db.query(Employment).filter(Employment.stu_id == stu_id, Employment.is_deleted == False).first()

    @staticmethod
    def get_employment_by_class_id(db: Session, class_id: int):
        return db.query(Employment).filter(Employment.class_id == class_id, Employment.is_deleted == False).all()

    @staticmethod
    def update_employment(db: Session, employment: Employment, update_data):
        try:
            update_dict = update_data.model_dump(exclude_unset=True)
            update_dict.pop("stu_id", None)
            update_dict.pop("class_id", None)
            for key, value in update_dict.items():
                if hasattr(employment, key):
                    setattr(employment, key, value)
            db.commit()
            db.refresh(employment)
            return employment
        except Exception as e:
            db.rollback()
            from utils.logger import db_logger
            db_logger.error(f"更新就业信息失败: {e}")
            return False

    @staticmethod
    def delete_employment(db: Session, employment: Employment):
        try:
            employment.is_deleted = True
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            from utils.logger import db_logger
            db_logger.error(f"删除就业信息失败: {e}")
            return False

    @staticmethod
    def create_empty_employment(db: Session, stu_id: int, stu_name: str, class_id: int):
        emp = Employment(stu_id=stu_id, stu_name=stu_name, class_id=class_id, open_time=None, offer_time=None, company=None, salary=None, is_deleted=False)
        db.add(emp)
        db.commit()
        db.refresh(emp)
        return emp

    @staticmethod
    def create_employment(db: Session, create_data):
        """创建就业信息"""
        try:
            emp = Employment(
                stu_id=create_data.stu_id,
                stu_name=create_data.stu_name,
                class_id=create_data.class_id,
                open_time=create_data.open_time,
                offer_time=create_data.offer_time,
                company=create_data.company,
                salary=create_data.salary,
                is_deleted=False
            )
            db.add(emp)
            db.commit()
            db.refresh(emp)
            return emp
        except Exception as e:
            db.rollback()
            from utils.logger import db_logger
            db_logger.error(f"创建就业信息失败: {e}")
            return False

    @staticmethod
    def get_employment_by_emp_id(db: Session, emp_id: int):
        return db.query(Employment).filter(Employment.emp_id == emp_id, Employment.is_deleted == False).first()

    @staticmethod
    def restore_employment(db: Session, emp_id: int):
        emp = db.query(Employment).filter(Employment.emp_id == emp_id).first()
        if not emp:
            return False
        try:
            emp.is_deleted = False
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            from utils.logger import db_logger
            db_logger.error(f"恢复就业信息失败: {e}")
            return False

    @staticmethod
    def query_employment(db: Session, stu_id: int = None, company: str = None, min_salary: int = None, max_salary: int = None):
        """修复：使用参数化查询防止SQL注入"""
        from sqlalchemy import bindparam
        
        query = db.query(Employment).filter(Employment.is_deleted == False)
        if stu_id is not None:
            query = query.filter(Employment.stu_id == stu_id)
        if company is not None:
            # 使用ORM的like方法，SQLAlchemy会自动处理参数化
            query = query.filter(Employment.company.ilike(f"%{company}%"))  # 使用ilike支持大小写不敏感
        if min_salary is not None:
            query = query.filter(Employment.salary >= min_salary)
        if max_salary is not None:
            query = query.filter(Employment.salary <= max_salary)
        return query.all()
