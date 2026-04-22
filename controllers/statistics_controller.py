from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from services.statistics_service import StatisticsService
from schemas import ResponseBase

router = APIRouter(tags=["统计分析模块"], prefix="/statistics")


@router.get("/students/over30", summary="查询所有超过30岁的学员信息")
def get_students_over_30(db: Session = Depends(get_db)):
    return StatisticsService.get_students_over_30(db)


@router.get("/classes/gender-stat", summary="统计每个班级的人数和男女生人数")
def class_gender_statistics(db: Session = Depends(get_db)):
    return StatisticsService.class_gender_statistics(db)


@router.get("/score/always-above-80", summary="每次考试成绩都在80分以上的学生")
def students_always_above_80(db: Session = Depends(get_db)):
    return StatisticsService.students_always_above_80(db)


@router.get("/score/twice-failed", summary="有两次以上不及格的学生")
def students_twice_failed(db: Session = Depends(get_db)):
    return StatisticsService.students_twice_failed(db)


@router.get("/score/class-avg-per-exam", summary="每次考试每个班级的平均分")
def class_avg_per_exam(db: Session = Depends(get_db)):
    return StatisticsService.class_avg_per_exam(db)


@router.get("/employment/top5-salary", summary="就业薪资最高的前五名学生")
def top5_salary_students(db: Session = Depends(get_db)):
    return StatisticsService.top5_salary_students(db)


@router.get("/employment/duration-per-student", summary="每个学生的就业时长")
def employment_duration_per_student(db: Session = Depends(get_db)):
    return StatisticsService.employment_duration_per_student(db)


@router.get("/employment/avg-duration-per-class", summary="每个班级的平均就业时长")
def avg_duration_per_class(db: Session = Depends(get_db)):
    return StatisticsService.avg_duration_per_class(db)


@router.get("/advanced/class-avg-score-rank", summary="各班平均成绩排名")
def class_avg_score_rank(db: Session = Depends(get_db)):
    return StatisticsService.class_avg_score_rank(db)


@router.get("/advanced/salary-distribution", summary="各薪资区间学生人数统计")
def salary_distribution(db: Session = Depends(get_db)):
    return StatisticsService.salary_distribution(db)


@router.get("/advanced/most-improved-students", summary="成绩进步最快的学生")
def most_improved_students(limit: int = 5, db: Session = Depends(get_db)):
    return StatisticsService.most_improved_students(db, limit)


@router.get("/advanced/class-employment-rate", summary="各班级就业率")
def class_employment_rate(db: Session = Depends(get_db)):
    return StatisticsService.class_employment_rate(db)


@router.get("/dashboard", summary="数据看板汇总")
def dashboard_stats(db: Session = Depends(get_db)):
    return StatisticsService.dashboard_stats(db)
