from sqlalchemy import and_
from sqlalchemy.orm import Session
from model.student import StuBasicInfo
from model.teachers import Teacher
from model.class_model import Class
from schemas.student import StudentCreate
from fastapi import HTTPException


class StudentService:
    @staticmethod
    def _is_teacher_counselor(counselor_id, db: Session):
        counselor_ids = db.query(Teacher.teacher_id).filter(Teacher.role == 'counselor').all()
        counselor_id_list = [c[0] for c in counselor_ids]
        if counselor_id not in counselor_id_list:
            raise HTTPException(status_code=400, detail=f"教师 ID {counselor_id} 不存在或不是counselor角色")

    @staticmethod
    def _is_classes_exist(class_id, db: Session):
        class_ids = db.query(Class.class_id).all()
        class_id_list = [c[0] for c in class_ids]
        if class_id not in class_id_list:
            raise HTTPException(status_code=400, detail=f"班级 ID {class_id} 不存在")

    @staticmethod
    def _format_student_data(students_query_result):
        if isinstance(students_query_result, list):
            return [
                {
                    "stu_id": i.stu_id, "stu_name": i.stu_name, "class_id": i.class_id,
                    "native_place": i.native_place, "graduated_school": i.graduated_school,
                    "major": i.major, "admission_date": i.admission_date, "graduation_date": i.graduation_date,
                    "education": i.education, "advisor_id": i.advisor_id, "age": i.age, "gender": i.gender
                }
                for i in students_query_result
            ]
        else:
            return {
                "stu_id": students_query_result.stu_id, "stu_name": students_query_result.stu_name,
                "class_id": students_query_result.class_id, "native_place": students_query_result.native_place,
                "graduated_school": students_query_result.graduated_school, "major": students_query_result.major,
                "admission_date": students_query_result.admission_date, "graduation_date": students_query_result.graduation_date,
                "education": students_query_result.education, "advisor_id": students_query_result.advisor_id,
                "age": students_query_result.age, "gender": students_query_result.gender
            }

    @staticmethod
    def create_student(new_student_data: StudentCreate, db: Session):
        StudentService._is_teacher_counselor(new_student_data.advisor_id, db)
        StudentService._is_classes_exist(new_student_data.class_id, db)
        new_student = StuBasicInfo(
            stu_name=new_student_data.stu_name, class_id=new_student_data.class_id,
            native_place=new_student_data.native_place, graduated_school=new_student_data.graduated_school,
            major=new_student_data.major, admission_date=new_student_data.admission_date,
            graduation_date=new_student_data.graduation_date, education=new_student_data.education,
            advisor_id=new_student_data.advisor_id, age=new_student_data.age, gender=new_student_data.gender,
        )
        db.add(new_student)
        db.commit()
        db.refresh(new_student)
        return StudentService._format_student_data(new_student)

    @staticmethod
    def get_students(db: Session, stu_id: int = None, stu_name: str = None, class_id: int = None):
        result = db.query(StuBasicInfo).filter(StuBasicInfo.is_deleted == False)
        if stu_id is not None:
            result = result.filter(StuBasicInfo.stu_id == stu_id)
        if stu_name is not None:
            result = result.filter(StuBasicInfo.stu_name == stu_name)
        if class_id is not None:
            result = result.filter(StuBasicInfo.class_id == class_id)
        students_temp = result.all()
        return StudentService._format_student_data(students_temp)

    @staticmethod
    def update_student(db: Session, stu_id: int, update_data):
        result = db.query(StuBasicInfo).filter(and_(StuBasicInfo.is_deleted == False, StuBasicInfo.stu_id == stu_id)).first()
        if not result:
            return False
        if update_data.stu_name is not None:
            result.stu_name = update_data.stu_name
        if update_data.class_id is not None:
            StudentService._is_classes_exist(update_data.class_id, db)
            result.class_id = update_data.class_id
        if update_data.native_place is not None:
            result.native_place = update_data.native_place
        if update_data.graduated_school is not None:
            result.graduated_school = update_data.graduated_school
        if update_data.major is not None:
            result.major = update_data.major
        if update_data.admission_date is not None:
            result.admission_date = update_data.admission_date
        if update_data.graduation_date is not None:
            result.graduation_date = update_data.graduation_date
        if update_data.education is not None:
            result.education = update_data.education
        if update_data.advisor_id is not None:
            StudentService._is_teacher_counselor(update_data.advisor_id, db)
            result.advisor_id = update_data.advisor_id
        if update_data.age is not None:
            result.age = update_data.age
        if update_data.gender is not None:
            result.gender = update_data.gender
        db.commit()
        db.refresh(result)
        return StudentService._format_student_data(result)

    @staticmethod
    def delete_student(db: Session, stu_id: int):
        result = db.query(StuBasicInfo).filter(and_(StuBasicInfo.is_deleted == False, StuBasicInfo.stu_id == stu_id)).first()
        if not result:
            return '不存在这个学生或已被删除'
        result.is_deleted = True
        db.commit()
        return '删除成功'
