from sqlalchemy.orm import Session
from sqlalchemy import func, case, and_, desc, distinct
from collections import defaultdict


class StatisticsService:
    @staticmethod
    def get_students_over_30(db: Session):
        from model.student import StuBasicInfo
        from model.class_model import Class
        students = db.query(
            StuBasicInfo.stu_id, StuBasicInfo.stu_name, StuBasicInfo.age, StuBasicInfo.gender, Class.class_name
        ).join(Class, StuBasicInfo.class_id == Class.class_id).filter(
            StuBasicInfo.is_deleted == False, Class.is_deleted == False, StuBasicInfo.age > 30
        ).all()
        result = [{"stu_id": s.stu_id, "stu_name": s.stu_name, "age": s.age, "gender": s.gender, "class_name": s.class_name} for s in students]
        return {"code": 200, "count": len(result), "data": result}

    @staticmethod
    def class_gender_statistics(db: Session):
        from model.student import StuBasicInfo
        from model.class_model import Class
        stats = db.query(
            Class.class_id, Class.class_name,
            func.count(StuBasicInfo.stu_id).label("total"),
            func.sum(case((StuBasicInfo.gender == "男", 1), else_=0)).label("male"),
            func.sum(case((StuBasicInfo.gender == "女", 1), else_=0)).label("female")
        ).join(StuBasicInfo, StuBasicInfo.class_id == Class.class_id).filter(
            Class.is_deleted == False, StuBasicInfo.is_deleted == False
        ).group_by(Class.class_id, Class.class_name).all()
        result = [{"class_id": c.class_id, "class_name": c.class_name, "total": c.total, "male": c.male, "female": c.female} for c in stats]
        return {"code": 200, "data": result}

    @staticmethod
    def students_always_above_80(db: Session):
        from model.student import StuBasicInfo
        from model.exam_model import StuExamRecord
        subquery = db.query(StuExamRecord.stu_id).filter(StuExamRecord.grade < 80, StuExamRecord.is_deleted == 0).distinct().subquery()
        good_students = db.query(StuBasicInfo).filter(StuBasicInfo.is_deleted == False, StuBasicInfo.stu_id.notin_(subquery)).all()
        result = []
        for stu in good_students:
            exams = db.query(StuExamRecord).filter(StuExamRecord.stu_id == stu.stu_id, StuExamRecord.is_deleted == 0).order_by(StuExamRecord.seq_no).all()
            result.append({"stu_id": stu.stu_id, "stu_name": stu.stu_name, "grades": [{"seq_no": e.seq_no, "grade": e.grade, "exam_date": e.exam_date} for e in exams]})
        return {"code": 200, "count": len(result), "data": result}

    @staticmethod
    def students_twice_failed(db: Session):
        from model.student import StuBasicInfo
        from model.exam_model import StuExamRecord
        from model.class_model import Class
        fail_counts = db.query(StuExamRecord.stu_id, func.count(StuExamRecord.seq_no).label("fail_count")).filter(StuExamRecord.grade < 60, StuExamRecord.is_deleted == 0).group_by(StuExamRecord.stu_id).having(func.count(StuExamRecord.seq_no) >= 2).subquery()
        result_query = db.query(StuBasicInfo.stu_id, StuBasicInfo.stu_name, Class.class_name, StuExamRecord.seq_no, StuExamRecord.grade, StuExamRecord.exam_date).join(fail_counts, StuBasicInfo.stu_id == fail_counts.c.stu_id).join(Class, StuBasicInfo.class_id == Class.class_id).join(StuExamRecord, StuBasicInfo.stu_id == StuExamRecord.stu_id).filter(StuExamRecord.grade < 60, StuExamRecord.is_deleted == 0, StuBasicInfo.is_deleted == False, Class.is_deleted == False).order_by(StuBasicInfo.stu_id, StuExamRecord.seq_no).all()
        grouped = defaultdict(lambda: {"stu_name": "", "class_name": "", "failed_exams": []})
        for row in result_query:
            key = row.stu_id
            grouped[key]["stu_name"] = row.stu_name
            grouped[key]["class_name"] = row.class_name
            grouped[key]["failed_exams"].append({"seq_no": row.seq_no, "grade": row.grade, "exam_date": row.exam_date})
        final = [{"stu_id": sid, "stu_name": info["stu_name"], "class_name": info["class_name"], "failed_count": len(info["failed_exams"]), "failed_exams": info["failed_exams"]} for sid, info in grouped.items()]
        return {"code": 200, "count": len(final), "data": final}

    @staticmethod
    def class_avg_per_exam(db: Session):
        from model.student import StuBasicInfo
        from model.exam_model import StuExamRecord
        from model.class_model import Class
        seq_nos = db.query(distinct(StuExamRecord.seq_no)).filter(StuExamRecord.is_deleted == 0).order_by(StuExamRecord.seq_no).all()
        seq_nos = [s[0] for s in seq_nos]
        result_by_seq = {}
        for seq in seq_nos:
            avg_scores = db.query(Class.class_id, Class.class_name, func.avg(StuExamRecord.grade).label("avg_grade")).join(StuBasicInfo, StuBasicInfo.class_id == Class.class_id).join(StuExamRecord, StuExamRecord.stu_id == StuBasicInfo.stu_id).filter(StuExamRecord.seq_no == seq, StuExamRecord.is_deleted == 0, StuBasicInfo.is_deleted == False, Class.is_deleted == False).group_by(Class.class_id, Class.class_name).order_by(desc("avg_grade")).all()
            result_by_seq[f"第{seq}次考试"] = [{"class_name": row.class_name, "avg_grade": round(row.avg_grade, 2)} for row in avg_scores]
        return {"code": 200, "data": result_by_seq}

    @staticmethod
    def top5_salary_students(db: Session):
        from model.employment import Employment
        from model.class_model import Class
        top5 = db.query(Employment.stu_id, Employment.stu_name, Employment.company, Employment.salary, Employment.offer_time, Class.class_name).join(Class, Employment.class_id == Class.class_id).filter(Employment.is_deleted == False, Employment.salary.isnot(None), Class.is_deleted == False).order_by(desc(Employment.salary)).limit(5).all()
        result = [{"stu_name": row.stu_name, "class_name": row.class_name, "salary": row.salary, "offer_time": row.offer_time, "company": row.company} for row in top5]
        return {"code": 200, "data": result}

    @staticmethod
    def employment_duration_per_student(db: Session):
        from model.employment import Employment
        records = db.query(Employment.stu_id, Employment.stu_name, Employment.open_time, Employment.offer_time).filter(Employment.is_deleted == False, Employment.open_time.isnot(None), Employment.offer_time.isnot(None)).all()
        result = []
        for rec in records:
            delta = (rec.offer_time - rec.open_time).days
            result.append({"stu_id": rec.stu_id, "stu_name": rec.stu_name, "open_time": rec.open_time, "offer_time": rec.offer_time, "duration_days": delta})
        return {"code": 200, "data": result}

    @staticmethod
    def avg_duration_per_class(db: Session):
        from model.employment import Employment
        from model.class_model import Class
        stats = db.query(Class.class_id, Class.class_name, func.avg(func.datediff(Employment.offer_time, Employment.open_time)).label("avg_days")).join(Employment, Employment.class_id == Class.class_id).filter(Class.is_deleted == False, Employment.is_deleted == False, Employment.open_time.isnot(None), Employment.offer_time.isnot(None)).group_by(Class.class_id, Class.class_name).all()
        result = [{"class_name": row.class_name, "avg_duration_days": round(row.avg_days, 1) if row.avg_days else None} for row in stats]
        return {"code": 200, "data": result}

    @staticmethod
    def class_avg_score_rank(db: Session):
        from model.student import StuBasicInfo
        from model.exam_model import StuExamRecord
        from model.class_model import Class
        from model.teachers import Teacher
        rank = db.query(Class.class_id, Class.class_name, Teacher.teacher_name.label("head_teacher"), func.avg(StuExamRecord.grade).label("avg_score")).join(Teacher, Class.head_teacher_id == Teacher.teacher_id).join(StuBasicInfo, StuBasicInfo.class_id == Class.class_id).join(StuExamRecord, StuExamRecord.stu_id == StuBasicInfo.stu_id).filter(Class.is_deleted == False, Teacher.is_deleted == False, StuBasicInfo.is_deleted == False, StuExamRecord.is_deleted == 0).group_by(Class.class_id, Class.class_name, Teacher.teacher_name).order_by(desc("avg_score")).all()
        result = [{"rank": idx + 1, "class_name": row.class_name, "head_teacher": row.head_teacher, "avg_score": round(row.avg_score, 2)} for idx, row in enumerate(rank)]
        return {"code": 200, "data": result}

    @staticmethod
    def salary_distribution(db: Session):
        from model.employment import Employment
        bins = [(0, 5000, "<5k"), (5000, 8000, "5k-8k"), (8000, 12000, "8k-12k"), (12000, 20000, "12k-20k"), (20000, float('inf'), ">20k")]
        result = []
        for low, high, label in bins:
            count = db.query(func.count(Employment.emp_id)).filter(Employment.is_deleted == False, Employment.salary >= low, Employment.salary < high if high != float('inf') else Employment.salary >= low).scalar()
            result.append({"range": label, "count": count})
        return {"code": 200, "data": result}

    @staticmethod
    def most_improved_students(db: Session, limit: int = 5):
        from model.student import StuBasicInfo
        from model.exam_model import StuExamRecord
        from model.class_model import Class
        min_max = db.query(StuExamRecord.stu_id, func.min(StuExamRecord.seq_no).label("min_seq"), func.max(StuExamRecord.seq_no).label("max_seq")).filter(StuExamRecord.is_deleted == 0).group_by(StuExamRecord.stu_id).subquery()
        first = db.query(StuExamRecord.stu_id, StuExamRecord.grade.label("first_grade")).join(min_max, and_(StuExamRecord.stu_id == min_max.c.stu_id, StuExamRecord.seq_no == min_max.c.min_seq)).subquery()
        last = db.query(StuExamRecord.stu_id, StuExamRecord.grade.label("last_grade")).join(min_max, and_(StuExamRecord.stu_id == min_max.c.stu_id, StuExamRecord.seq_no == min_max.c.max_seq)).subquery()
        improved = db.query(StuBasicInfo.stu_id, StuBasicInfo.stu_name, Class.class_name, first.c.first_grade, last.c.last_grade, (last.c.last_grade - first.c.first_grade).label("improvement")).select_from(StuBasicInfo).join(Class, StuBasicInfo.class_id == Class.class_id).join(first, StuBasicInfo.stu_id == first.c.stu_id).join(last, StuBasicInfo.stu_id == last.c.stu_id).filter(StuBasicInfo.is_deleted == False, Class.is_deleted == False, first.c.first_grade.isnot(None), last.c.last_grade.isnot(None), StuBasicInfo.stu_id.in_(db.query(min_max.c.stu_id).filter(min_max.c.min_seq != min_max.c.max_seq))).order_by(desc("improvement")).limit(limit).all()
        result = [{"stu_name": row.stu_name, "class_name": row.class_name, "first_grade": row.first_grade, "last_grade": row.last_grade, "improvement": row.improvement} for row in improved]
        return {"code": 200, "data": result}

    @staticmethod
    def class_employment_rate(db: Session):
        from model.student import StuBasicInfo
        from model.exam_model import StuExamRecord
        from model.class_model import Class
        from model.employment import Employment
        total_students = db.query(Class.class_id, Class.class_name, func.count(StuBasicInfo.stu_id).label("total")).join(StuBasicInfo, StuBasicInfo.class_id == Class.class_id).filter(Class.is_deleted == False, StuBasicInfo.is_deleted == False).group_by(Class.class_id, Class.class_name).subquery()
        employed_students = db.query(Employment.class_id, func.count(distinct(Employment.stu_id)).label("employed")).filter(Employment.is_deleted == False, Employment.salary.isnot(None)).group_by(Employment.class_id).subquery()
        result = db.query(total_students.c.class_id, total_students.c.class_name, total_students.c.total, func.coalesce(employed_students.c.employed, 0).label("employed"), (func.coalesce(employed_students.c.employed, 0) / total_students.c.total * 100).label("rate")).outerjoin(employed_students, total_students.c.class_id == employed_students.c.class_id).all()
        final = [{"class_name": row.class_name, "total_students": row.total, "employed_students": row.employed, "employment_rate": round(row.rate, 2)} for row in result]
        return {"code": 200, "data": final}

    @staticmethod
    def dashboard_stats(db: Session):
        from model.student import StuBasicInfo
        from model.class_model import Class
        from model.employment import Employment
        total_students = db.query(StuBasicInfo).filter(StuBasicInfo.is_deleted == False).count()
        total_classes = db.query(Class).filter(Class.is_deleted == False).count()
        avg_age_result = db.query(func.avg(StuBasicInfo.age)).filter(StuBasicInfo.is_deleted == False).first()
        avg_age = round(avg_age_result[0], 1) if avg_age_result[0] else 0
        employed = db.query(func.count(distinct(Employment.stu_id))).filter(Employment.is_deleted == False, Employment.salary.isnot(None)).scalar() or 0
        employment_rate = round(employed / total_students * 100, 1) if total_students > 0 else 0
        top_salary = db.query(Employment.stu_name, Class.class_name, Employment.salary, Employment.company).join(Class, Employment.class_id == Class.class_id).filter(Employment.is_deleted == False, Employment.salary.isnot(None), Class.is_deleted == False).order_by(Employment.salary.desc()).limit(5).all()
        top_salary_list = [{"stu_name": row.stu_name, "class_name": row.class_name, "salary": row.salary, "company": row.company} for row in top_salary]
        return {"code": 200, "data": {"total_students": total_students, "total_classes": total_classes, "avg_age": avg_age, "employment_rate": employment_rate, "top_salary": top_salary_list}}
