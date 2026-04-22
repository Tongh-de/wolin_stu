from sqlalchemy.orm import Session
from model.teachers import Teacher
from model.class_model import Class
from schemas.teacher import TeacheresUpdata


class TeacherService:
    @staticmethod
    def create_teacher(db: Session, teacher: TeacheresUpdata):
        db_teacher = Teacher(teacher_name=teacher.teacher_name, gender=teacher.gender, phone=teacher.phone, role=teacher.role, is_deleted=False)
        db.add(db_teacher)
        db.commit()
        db.refresh(db_teacher)
        return {"teacher_id": db_teacher.teacher_id, "teacher_name": db_teacher.teacher_name, "gender": db_teacher.gender, "phone": db_teacher.phone, "role": db_teacher.role}

    @staticmethod
    def get_teacher(db: Session, teacher_id: int = None, teacher_name: str = None):
        query = db.query(Teacher).filter(Teacher.is_deleted == False)
        if teacher_id is not None:
            query = query.filter(Teacher.teacher_id == teacher_id)
        if teacher_name is not None:
            query = query.filter(Teacher.teacher_name == teacher_name)
        teacher = query.first()
        if not teacher:
            return None
        return {"teacher_id": teacher.teacher_id, "teacher_name": teacher.teacher_name, "gender": teacher.gender, "phone": teacher.phone, "role": teacher.role}

    @staticmethod
    def get_all_teachers(db: Session):
        data = db.query(Teacher).filter(Teacher.is_deleted == False).all()
        return [{"teacher_id": i.teacher_id, "teacher_name": i.teacher_name, "phone": i.phone, "role": i.role, "gender": i.gender} for i in data]

    @staticmethod
    def update_teacher(db: Session, teacher_id: int, teacher: TeacheresUpdata):
        db_teacher = db.query(Teacher).filter(Teacher.teacher_id == teacher_id, Teacher.is_deleted == False).first()
        if not db_teacher:
            return None
        for key, value in teacher.model_dump(exclude_unset=True).items():
            setattr(db_teacher, key, value)
        db.commit()
        db.refresh(db_teacher)
        return {"teacher_id": db_teacher.teacher_id, "teacher_name": db_teacher.teacher_name, "gender": db_teacher.gender, "phone": db_teacher.phone, "role": db_teacher.role}

    @staticmethod
    def delete_teacher(db: Session, teacher_id: int):
        db_teacher = db.query(Teacher).filter(Teacher.teacher_id == teacher_id, Teacher.is_deleted == False).first()
        if db_teacher:
            db_teacher.is_deleted = True
            db.commit()
            return True
        return False

    @staticmethod
    def bind_teacher_to_class(db: Session, teacher_id: int, class_ids: list):
        teacher = db.query(Teacher).filter(Teacher.teacher_id == teacher_id, Teacher.is_deleted == False, Teacher.role == "lecturer").first()
        if not teacher:
            return None
        classes = db.query(Class).filter(Class.class_id.in_(class_ids), Class.is_deleted == False).all()
        if not classes:
            return None
        teacher.teach_classes = classes
        db.commit()
        db.refresh(teacher)
        return teacher

    @staticmethod
    def unbind_teacher_from_class(db: Session, teacher_id: int, class_id: int):
        teacher = db.query(Teacher).filter(Teacher.teacher_id == teacher_id, Teacher.is_deleted == False, Teacher.role == "lecturer").first()
        if not teacher:
            return False
        target_class = db.query(Class).filter(Class.class_id == class_id, Class.is_deleted == False).first()
        if target_class not in teacher.teach_classes:
            return False
        teacher.teach_classes.remove(target_class)
        db.commit()
        return True

    @staticmethod
    def get_head_classes(db: Session, teacher_id: int):
        teacher = db.query(Teacher).filter(Teacher.teacher_id == teacher_id, Teacher.is_deleted == False).first()
        if not teacher:
            return "老师不存在"
        if not teacher.class_as_head:
            return "该老师不是班主任"
        return [{"class_id": c.class_id, "class_name": c.class_name, "head_teacher_id": c.head_teacher_id, "haed_teacher_name": teacher.teacher_name} for c in teacher.class_as_head]

    @staticmethod
    def get_teach_classes(db: Session, teacher_id: int):
        teacher = db.query(Teacher).filter(Teacher.teacher_id == teacher_id, Teacher.is_deleted == False).first()
        if not teacher:
            return "老师不存在"
        if teacher.role != "lecturer":
            return "该老师不是讲师"
        return [{"class_id": c.class_id, "class_name": c.class_name, "head_teacher_id": teacher.teacher_id, "teacher_name": teacher.teacher_name} for c in teacher.teach_classes]

    @staticmethod
    def get_my_students(db: Session, teacher_id: int):
        teacher = db.query(Teacher).filter(Teacher.teacher_id == teacher_id, Teacher.is_deleted == False).first()
        if not teacher:
            return "老师不存在"
        if teacher.role != "counselor":
            return "该老师不是顾问，无负责的学生"
        if not teacher.students:
            return "该顾问暂无负责的学生"
        return [{"stu_id": s.stu_id, "stu_name": s.stu_name, "class_id": s.class_id, "counselor_name": teacher.teacher_name} for s in teacher.students]
