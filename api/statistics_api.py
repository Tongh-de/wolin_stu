from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, case, and_
from database import get_db

# ===================== 【修复核心】相对导入，匹配你们的目录结构 =====================
from model.student import StuBasicInfo
from model.class_model import Class
from model.exam_model import StuExamRecord
from model.employment import Employment
from model.teachers import Teacher

router = APIRouter(tags=["学生管理统计分析模块"], prefix="/statistics")

# ===================== 测试接口 =====================
@router.get("/test", summary="【调试接口】测试连通性")
def test_api(db: Session = Depends(get_db)):
    students = db.query(StuBasicInfo).filter(StuBasicInfo.is_deleted == 0).limit(3).all()
    data = [{"stu_id": s.stu_id, "stu_name": s.stu_name, "age": s.age} for s in students]
    return {"code": 200, "message": "接口正常", "data": data}

# ===================== 学生+班级统计 =====================
@router.get("/student/age-stat", summary="30岁以上学生统计")
def student_age_over_30(db: Session = Depends(get_db)):
    query = db.query(
        StuBasicInfo.stu_id, StuBasicInfo.stu_name, StuBasicInfo.age,
        StuBasicInfo.gender, Class.class_name
    ).join(Class, StuBasicInfo.class_id == Class.class_id
    ).filter(StuBasicInfo.age > 30, StuBasicInfo.is_deleted == 0).all()
    result = [{"stu_id": i[0], "stu_name": i[1], "age": i[2], "gender": i[3], "class_name": i[4]} for i in query]
    return {"code": 200, "count": len(result), "data": result}

@router.get("/student/class-gender", summary="班级男女比例")
def class_gender_stat(db: Session = Depends(get_db)):
    query = db.query(
        Class.class_name,
        func.count(StuBasicInfo.stu_id).label("total"),
        func.sum(case((StuBasicInfo.gender == "男", 1), else_=0)).label("male"),
        func.sum(case((StuBasicInfo.gender == "女", 1), else_=0)).label("female")
    ).join(StuBasicInfo).filter(StuBasicInfo.is_deleted == 0).group_by(Class.class_id).all()
    return {"code":200, "data":[{"class_name":i[0],"total":i[1],"male":i[2],"female":i[3]} for i in query]}

# ===================== 成绩统计 =====================
@router.get("/score/class-average", summary="班级平均分排名")
def class_avg_score(db: Session = Depends(get_db)):
    query = db.query(
        Class.class_name,
        func.avg(StuExamRecord.grade).label("avg_grade"),
        func.max(StuExamRecord.grade).label("max_grade")
    ).join(StuBasicInfo, StuExamRecord.stu_id == StuBasicInfo.stu_id
    ).join(Class, StuBasicInfo.class_id == Class.class_id
    ).group_by(Class.class_id).all()
    return {"code":200, "data":[{"class_name":i[0],"avg":round(i[1],2) if i[1] else 0,"max":i[2]} for i in query]}

@router.get("/score/fail-list", summary="不及格学生名单")
def fail_student_list(db: Session = Depends(get_db)):
    query = db.query(
        StuBasicInfo.stu_name, Class.class_name, StuExamRecord.grade, StuExamRecord.seq_no
    ).join(StuExamRecord).join(Class).filter(StuExamRecord.grade < 60).all()
    return {"code":200, "data":[{"stu_name":i[0],"class_name":i[1],"grade":i[2],"exam_times":i[3]} for i in query]}

# ===================== 就业统计 =====================
@router.get("/job/top-salary", summary="薪资TOP5")
def top5_salary(db: Session = Depends(get_db)):
    query = db.query(
        StuBasicInfo.stu_name, Class.class_name, Employment.company, Employment.salary
    ).join(Employment).join(Class).order_by(Employment.salary.desc()).limit(5).all()
    return {"code":200, "data":[{"name":i[0],"cls":i[1],"com":i[2],"sal":i[3]} for i in query]}

@router.get("/job/company-stat", summary="各公司就业人数统计")
def company_employ_stat(db: Session = Depends(get_db)):
    query = db.query(
        Employment.company, func.count(Employment.emp_id).label("count")
    ).group_by(Employment.company).all()
    return {"code":200, "data":[{"company":i[0],"count":i[1]} for i in query]}

# ===================== 全局大盘 =====================
@router.get("/dashboard/all", summary="数据总览")
def dashboard(db: Session = Depends(get_db)):
    total_stu = db.query(func.count(StuBasicInfo.stu_id)).scalar()
    total_cls = db.query(func.count(Class.class_id)).scalar()
    total_emp = db.query(func.count(Employment.emp_id)).scalar()
    avg_sal = db.query(func.avg(Employment.salary)).scalar() or 0

    return {
        "code":200,
        "data":{
            "总学生":total_stu,
            "总班级":total_cls,
            "已就业":total_emp,
            "平均薪资":round(avg_sal,2)
        }
    }