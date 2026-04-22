from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
from services import ClassService
from schemas.class_schemas import ClassCreate, ClassUpdate
from schemas import ResponseBase

router = APIRouter(prefix="/class", tags=["班级管理"])


@router.get("/", response_model=ResponseBase)
def read_all_classes(
        db: Session = Depends(get_db),
        include_deleted: bool = Query(False, description="是否包含已删除的班级")
):
    classes_list = ClassService.get_all_class(db, include_deleted=include_deleted)
    classes_dict = {str(c["class_id"]): c for c in classes_list}
    return ResponseBase(code=200, message="查询成功", data=classes_dict)


@router.get("/{class_id}", response_model=ResponseBase)
def read_one_class(
        class_id: int,
        db: Session = Depends(get_db),
        include_deleted: bool = Query(False)
):
    cls_dict = ClassService.get_class_by_id(db, class_id, include_deleted=include_deleted)
    if not cls_dict:
        raise HTTPException(status_code=404, detail="班级不存在")
    return ResponseBase(code=200, message="查询成功", data=cls_dict)


@router.get("/{class_id}/teachers", response_model=ResponseBase)
def get_teachers(
        class_id: int,
        db: Session = Depends(get_db)
):
    teacher_list = ClassService.get_class_teachers(db, class_id)
    if not teacher_list:
        raise HTTPException(status_code=404, detail="班级不存在或暂无教师授课老师")
    return ResponseBase(code=200, message="查询成功", data=teacher_list)


@router.post("/", response_model=ResponseBase, status_code=201)
def create_new_class(class_data: ClassCreate, db: Session = Depends(get_db)):
    cls_dict = ClassService.create_class(db, class_data)
    return ResponseBase(code=201, message="创建成功", data=cls_dict)


@router.put("/{class_id}", response_model=ResponseBase)
def update_exist_class(
        class_id: int,
        class_data: ClassUpdate,
        db: Session = Depends(get_db)
):
    cls_dict = ClassService.update_class(db, class_id, class_data)
    if not cls_dict:
        raise HTTPException(status_code=404, detail="班级不存在")
    return ResponseBase(code=200, message="更新成功", data=cls_dict)


@router.delete("/{class_id}", response_model=ResponseBase)
def delete_exist_class(
        class_id: int,
        db: Session = Depends(get_db),
        hard_delete: bool = Query(False, description="是否硬删除")
):
    result = ClassService.delete_class(db, class_id, hard_delete=hard_delete)
    if result is False:
        raise HTTPException(status_code=404, detail="班级不存在")
    msg = "硬删除成功" if hard_delete else "软删除成功"
    return ResponseBase(code=200, message=msg, data=result)


@router.post("/{class_id}/restore", response_model=ResponseBase)
def restore_deleted_class(class_id: int, db: Session = Depends(get_db)):
    cls_dict = ClassService.restore_class(db, class_id)
    if not cls_dict:
        raise HTTPException(status_code=404, detail="班级被删除或者不存在")
    return ResponseBase(code=200, message="恢复成功", data=cls_dict)
