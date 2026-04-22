from sqlalchemy import and_
from sqlalchemy.orm import Session
from model.exam_model import StuExamRecord


class ExamService:
    @staticmethod
    def exam_submit(exam_data, db: Session):
        _query = db.query(StuExamRecord).filter(
            and_(StuExamRecord.is_deleted == 1, StuExamRecord.stu_id == exam_data.stu_id, StuExamRecord.seq_no == exam_data.seq_no)
        )
        data = _query.first()
        if data:
            _query.update({StuExamRecord.is_deleted: 0, StuExamRecord.grade: exam_data.grade, StuExamRecord.exam_date: exam_data.exam_date})
            db.commit()
            return {"message": "success", "stu_id": exam_data.stu_id, "seq_no": exam_data.seq_no, "grade": exam_data.grade, "exam_date": exam_data.exam_date}
        else:
            try:
                submit = StuExamRecord(stu_id=exam_data.stu_id, seq_no=exam_data.seq_no, grade=exam_data.grade, exam_date=exam_data.exam_date, is_deleted=0)
                db.add(submit)
                db.commit()
                db.refresh(submit)
                return {"message": "success", "stu_id": submit.stu_id, "seq_no": submit.seq_no, "grade": submit.grade, "exam_date": submit.exam_date}
            except Exception as e:
                pk_e = "duplicate entry"
                fk_e = "foreign key constraint fails"
                if pk_e in str(e).lower():
                    return {"message": "提交失败：该学生的此次考核记录已存在"}
                elif fk_e in str(e).lower():
                    return {"message": "提交失败：该学生编号不存在"}
                else:
                    return {"message": f"{e}"}

    @staticmethod
    def exam_update(stu_id: int, seq_no: int, exam_data, db: Session):
        _query = db.query(StuExamRecord).filter(and_(StuExamRecord.is_deleted == 0, StuExamRecord.stu_id == stu_id, StuExamRecord.seq_no == seq_no))
        data = _query.first()
        if data:
            cnt = _query.update({StuExamRecord.grade: exam_data.grade, StuExamRecord.exam_date: exam_data.exam_date})
            db.commit()
            return f"'{stu_id=}' & '{seq_no=}' -> {cnt} rows updated"
        else:
            return f"'{stu_id=}' & '{seq_no=}' not found"

    @staticmethod
    def exam_delete(stu_id: int, seq_no: int | None, db: Session):
        _query = db.query(StuExamRecord).filter(and_(StuExamRecord.is_deleted == 0, StuExamRecord.stu_id == stu_id))
        if seq_no is not None:
            _query = _query.filter(StuExamRecord.seq_no == seq_no)
        cnt = _query.update({StuExamRecord.is_deleted: 1})
        db.commit()
        if cnt != 0:
            return f"'{stu_id=}' & '{seq_no=}' -> {cnt} rows deleted"
        else:
            return f"'{stu_id=}' & '{seq_no=}' not found"

    @staticmethod
    def exam_get(stu_id: int, seq_no: int | None, db: Session):
        _query = db.query(StuExamRecord).filter(and_(StuExamRecord.is_deleted == 0, StuExamRecord.stu_id == stu_id))
        if seq_no is not None:
            _query = _query.filter(StuExamRecord.seq_no == seq_no).first()
            data = {"stu_id": _query.stu_id, "seq_no": _query.seq_no, "grade": _query.grade, "exam_date": _query.exam_date}
        else:
            _query = _query.all()
            data = [{"stu_id": i.stu_id, "seq_no": i.seq_no, "grade": i.grade, "exam_date": i.exam_date} for i in _query]
        if data:
            return {"msg": "success", "data": data}
        else:
            return {"msg": f"'{stu_id=}' & '{seq_no=}' not found"}
