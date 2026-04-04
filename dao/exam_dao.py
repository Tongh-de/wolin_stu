from sqlalchemy.orm import Session
from model.exam_model import StuExamRecord


def submit_grade(
        exam_data,
        db: Session
):
    """"按考核序次录⼊考核成绩（学⽣编号、考核序次、成绩）"""
    _return = StuExamRecord(
        stu_id = exam_data.stu_id,
        seq_no = exam_data.seq_no,
        grade = exam_data.grade,
        exam_date = exam_data.exam_date,
        is_deleted = exam_data.is_deleted
    )
    db.add(_return)
    db.commit()
    db.refresh(_return)
    return _return


# def modify_grade(
#         11
# ):
#     """考试成绩修改"""
#
#
# def grade_is_deleted(
#         11
# ):
#     """逻辑删除考试成绩"""