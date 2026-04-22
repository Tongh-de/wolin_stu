from sqlalchemy.orm import Session
from model.class_model import Class, class_teacher
from schemas.class_schemas import ClassCreate, ClassUpdate


class ClassService:
    @staticmethod
    def _class_to_dict(cls: Class) -> dict:
        return {
            "class_id": cls.class_id,
            "class_name": cls.class_name,
            "start_time": cls.start_time.isoformat() if cls.start_time else None,
            "head_teacher_id": cls.head_teacher_id,
            "is_deleted": cls.is_deleted
        }

    @staticmethod
    def get_all_class(db: Session, include_deleted: bool = False):
        query = db.query(Class)
        if not include_deleted:
            query = query.filter(Class.is_deleted == False)
        classes = query.all()
        return [ClassService._class_to_dict(c) for c in classes]

    @staticmethod
    def get_class_by_id(db: Session, class_id: int, include_deleted: bool = False):
        query = db.query(Class).filter(Class.class_id == class_id)
        if not include_deleted:
            query = query.filter(Class.is_deleted == False)
        cls = query.first()
        return ClassService._class_to_dict(cls) if cls else None

    @staticmethod
    def get_class_teachers(db: Session, class_id: int):
        cls = db.query(Class).filter(Class.class_id == class_id, Class.is_deleted == False).first()
        if not cls:
            return []
        return {
            "class_id": cls.class_id,
            "class_name": cls.class_name,
            "head_teacher_id": cls.head_teacher_id,
            "head_teacher_name": cls.head_teacher_info.teacher_name if cls.head_teacher_info else None,
            "teachers": [{"teacher_id": teacher.teacher_id, "teacher_name": teacher.teacher_name} for teacher in cls.teachers]
        }

    @staticmethod
    def create_class(db: Session, class_data: ClassCreate):
        db_class = Class(class_name=class_data.class_name, start_time=class_data.start_time, head_teacher_id=class_data.head_teacher_id, is_deleted=False)
        db.add(db_class)
        db.commit()
        db.refresh(db_class)
        return ClassService._class_to_dict(db_class)

    @staticmethod
    def update_class(db: Session, class_id: int, class_data: ClassUpdate):
        db_class = db.query(Class).filter(Class.class_id == class_id, Class.is_deleted == False).first()
        if not db_class:
            return None
        if class_data.class_name is not None:
            db_class.class_name = class_data.class_name
        if class_data.start_time is not None:
            db_class.start_time = class_data.start_time
        if class_data.head_teacher_id is not None:
            db_class.head_teacher_id = class_data.head_teacher_id
        db.commit()
        db.refresh(db_class)
        return ClassService._class_to_dict(db_class)

    @staticmethod
    def delete_class(db: Session, class_id: int, hard_delete: bool = False):
        db_class = db.query(Class).filter(Class.class_id == class_id, Class.is_deleted == False).first()
        if not db_class:
            return False
        if hard_delete:
            db.execute(class_teacher.delete().where(class_teacher.c.class_id == class_id))
            db.delete(db_class)
        else:
            db_class.is_deleted = True
        db.commit()
        return {"class_id": class_id, "deleted": True, "hard_deleted": hard_delete}

    @staticmethod
    def restore_class(db: Session, class_id: int):
        db_class = db.query(Class).filter(Class.class_id == class_id, Class.is_deleted == True).first()
        if not db_class:
            return None
        db_class.is_deleted = False
        db.commit()
        db.refresh(db_class)
        return ClassService._class_to_dict(db_class)
