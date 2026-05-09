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
        """优化：使用子查询一次性获取所有成绩，避免N+1问题"""
        from model.student import StuBasicInfo
        from model.exam_model import StuExamRecord
        
        # 子查询：找出有低于80分记录的学生
        subquery = db.query(StuExamRecord.stu_id).filter(
            StuExamRecord.grade < 80, 
            StuExamRecord.is_deleted == 0
        ).distinct().subquery()
        
        # 查询优秀学生及其所有成绩（一次查询）
        good_students = db.query(StuBasicInfo).filter(
            StuBasicInfo.is_deleted == False, 
            StuBasicInfo.stu_id.notin_(subquery)
        ).all()
        
        stu_ids = [s.stu_id for s in good_students]
        
        # 批量获取所有成绩
        all_exams = db.query(StuExamRecord).filter(
            StuExamRecord.stu_id.in_(stu_ids),
            StuExamRecord.is_deleted == 0
        ).order_by(StuExamRecord.stu_id, StuExamRecord.seq_no).all()
        
        # 按学生分组
        exams_by_student = {}
        for exam in all_exams:
            if exam.stu_id not in exams_by_student:
                exams_by_student[exam.stu_id] = {
                    "stu_name": next((s.stu_name for s in good_students if s.stu_id == exam.stu_id), ""),
                    "grades": []
                }
            exams_by_student[exam.stu_id]["grades"].append({
                "seq_no": exam.seq_no,
                "grade": exam.grade,
                "exam_date": exam.exam_date
            })
        
        result = [
            {"stu_id": sid, "stu_name": info["stu_name"], "grades": info["grades"]}
            for sid, info in exams_by_student.items()
        ]
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
        """优化：使用单次查询获取所有数据，避免循环查询"""
        from model.student import StuBasicInfo
        from model.exam_model import StuExamRecord
        from model.class_model import Class
        
        # 一次性查询所有数据
        all_data = db.query(
            StuExamRecord.seq_no,
            Class.class_id,
            Class.class_name,
            StuExamRecord.grade
        ).join(StuBasicInfo, StuBasicInfo.class_id == Class.class_id).join(
            StuExamRecord, StuExamRecord.stu_id == StuBasicInfo.stu_id
        ).filter(
            StuExamRecord.is_deleted == 0,
            StuBasicInfo.is_deleted == False,
            Class.is_deleted == False
        ).all()
        
        # Python端聚合
        from collections import defaultdict
        data_by_seq = defaultdict(lambda: defaultdict(list))
        
        for row in all_data:
            data_by_seq[row.seq_no][(row.class_id, row.class_name)].append(row.grade)
        
        # 计算平均值
        result_by_seq = {}
        for seq in sorted(data_by_seq.keys()):
            class_grades = data_by_seq[seq]
            avg_scores = []
            for (class_id, class_name), grades in class_grades.items():
                avg = sum(grades) / len(grades) if grades else 0
                avg_scores.append({
                    "class_name": class_name,
                    "avg_grade": round(avg, 2)
                })
            # 按平均分排序
            avg_scores.sort(key=lambda x: x["avg_grade"], reverse=True)
            result_by_seq[f"第{seq}次考试"] = avg_scores
        
        return {"code": 200, "data": result_by_seq}

    @staticmethod
    def top5_salary_students(db: Session):
        from model.employment import Employment
        from model.class_model import Class
        from model.student import StuBasicInfo
        top5 = db.query(
            StuBasicInfo.stu_id, 
            StuBasicInfo.stu_name, 
            Employment.company, 
            Employment.salary, 
            Employment.offer_time, 
            Class.class_name
        ).join(
            StuBasicInfo, Employment.stu_id == StuBasicInfo.stu_id
        ).join(
            Class, Employment.class_id == Class.class_id
        ).filter(
            Employment.is_deleted == False, 
            Employment.salary.isnot(None), 
            StuBasicInfo.is_deleted == False,
            Class.is_deleted == False
        ).order_by(desc(Employment.salary)).limit(5).all()
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
        """优化：使用CASE WHEN一次性查询，避免多次数据库往返"""
        from model.employment import Employment
        from sqlalchemy import case, literal_column
        
        # 使用数据库端CASE WHEN分组
        salary_ranges = db.query(
            case(
                (Employment.salary < 5000, "<5k"),
                (Employment.salary < 8000, "5k-8k"),
                (Employment.salary < 12000, "8k-12k"),
                (Employment.salary < 20000, "12k-20k"),
                else_=">20k"
            ).label("range"),
            func.count(Employment.emp_id).label("count")
        ).filter(
            Employment.is_deleted == False,
            Employment.salary.isnot(None)
        ).group_by(
            case(
                (Employment.salary < 5000, "<5k"),
                (Employment.salary < 8000, "5k-8k"),
                (Employment.salary < 12000, "8k-12k"),
                (Employment.salary < 20000, "12k-20k"),
                else_=">20k"
            )
        ).all()
        
        # 确保所有区间都有值
        range_order = ["<5k", "5k-8k", "8k-12k", "12k-20k", ">20k"]
        result_map = {r.range: r.count for r in salary_ranges}
        result = [{"range": r, "count": result_map.get(r, 0)} for r in range_order]
        
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
        from model.teachers import Teacher
        from model.employment import Employment
        
        # 基础统计
        total_students = db.query(StuBasicInfo).filter(StuBasicInfo.is_deleted == False).count()
        total_classes = db.query(Class).filter(Class.is_deleted == False).count()
        total_teachers = db.query(Teacher).filter(Teacher.is_deleted == False).count()
        
        # 平均年龄
        avg_age_result = db.query(func.avg(StuBasicInfo.age)).filter(StuBasicInfo.is_deleted == False).first()
        avg_age = round(avg_age_result[0], 1) if avg_age_result[0] else 0
        
        # 就业统计
        employed = db.query(func.count(distinct(Employment.stu_id))).filter(Employment.is_deleted == False, Employment.salary.isnot(None)).scalar() or 0
        unemployed = total_students - employed
        employment_rate = round(employed / total_students * 100, 1) if total_students > 0 else 0
        
        # 高薪榜 TOP5 - 从 StuBasicInfo 获取姓名，确保不为空
        from model.student import StuBasicInfo
        top_salary = db.query(
            StuBasicInfo.stu_name, 
            Class.class_name, 
            Employment.salary, 
            Employment.company
        ).join(
            StuBasicInfo, Employment.stu_id == StuBasicInfo.stu_id
        ).join(
            Class, Employment.class_id == Class.class_id
        ).filter(
            Employment.is_deleted == False, 
            Employment.salary.isnot(None), 
            StuBasicInfo.is_deleted == False,
            Class.is_deleted == False
        ).order_by(Employment.salary.desc()).limit(5).all()
        top_salary_list = [{"name": row.stu_name, "class_name": row.class_name, "salary": row.salary, "company": row.company} for row in top_salary]
        
        # 班级人数分布
        class_stats = db.query(
            Class.class_id,
            Class.class_name,
            func.count(StuBasicInfo.stu_id).label("count")
        ).join(StuBasicInfo, StuBasicInfo.class_id == Class.class_id).filter(
            Class.is_deleted == False, 
            StuBasicInfo.is_deleted == False
        ).group_by(Class.class_id, Class.class_name).all()
        class_distribution = [{"class_name": row.class_name, "count": row.count} for row in class_stats]
        
        return {
            "code": 200, 
            "data": {
                "total_students": total_students, 
                "total_classes": total_classes, 
                "total_teachers": total_teachers,
                "avg_age": avg_age, 
                "employment_rate": employment_rate, 
                "top_salary": top_salary_list,
                "class_distribution": class_distribution,
                "employment_stats": {
                    "employed": employed,
                    "unemployed": unemployed
                }
            }
        }
