from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
from services import ClassService
from schemas.class_schemas import ClassCreate, ClassUpdate
from schemas import ResponseBase
from utils.logger import get_logger
from utils.auth_deps import get_current_user, require_admin, require_teacher_or_admin
from model.user import User

logger = get_logger("class")
router = APIRouter(prefix="/class", tags=["班级管理"])


@router.get("/", response_model=ResponseBase)
def read_all_classes(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),  # 登录用户
        include_deleted: bool = Query(False, description="是否包含已删除的班级")
):
    logger.info(f"查询班级列表: include_deleted={include_deleted}, 操作者: {current_user.username}")
    classes_list = ClassService.get_all_class(db, include_deleted=include_deleted)
    classes_dict = {str(c["class_id"]): c for c in classes_list}
    logger.info(f"查询成功: 共{len(classes_list)}个班级")
    return ResponseBase(code=200, message="查询成功", data=classes_dict)


@router.get("/{class_id}", response_model=ResponseBase)
def read_one_class(
        class_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),  # 登录用户
        include_deleted: bool = Query(False)
):
    logger.info(f"查询班级详情: class_id={class_id}, 操作者: {current_user.username}")
    cls_dict = ClassService.get_class_by_id(db, class_id, include_deleted=include_deleted)
    if not cls_dict:
        logger.warning(f"班级不存在: class_id={class_id}")
        raise HTTPException(status_code=404, detail="班级不存在")
    logger.info(f"查询成功: {cls_dict.get('class_name')}")
    return ResponseBase(code=200, message="查询成功", data=cls_dict)


@router.get("/{class_id}/teachers", response_model=ResponseBase)
def get_teachers(
        class_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)  # 登录用户
):
    logger.info(f"查询班级教师: class_id={class_id}, 操作者: {current_user.username}")
    teacher_list = ClassService.get_class_teachers(db, class_id)
    if not teacher_list:
        logger.warning(f"班级无教师: class_id={class_id}")
        raise HTTPException(status_code=404, detail="班级不存在或暂无教师授课老师")
    return ResponseBase(code=200, message="查询成功", data=teacher_list)


@router.post("/", response_model=ResponseBase, status_code=201)
def create_new_class(
        class_data: ClassCreate, 
        db: Session = Depends(get_db),
        current_user: User = Depends(require_admin)  # 仅管理员
):
    logger.info(f"创建班级: {class_data.class_name}, 操作者: {current_user.username}")
    cls_dict = ClassService.create_class(db, class_data)
    logger.info(f"班级创建成功: class_id={cls_dict['class_id']}")
    return ResponseBase(code=201, message="创建成功", data=cls_dict)


@router.put("/{class_id}", response_model=ResponseBase)
def update_exist_class(
        class_id: int,
        class_data: ClassUpdate,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_admin)  # 仅管理员
):
    logger.info(f"更新班级: class_id={class_id}, 操作者: {current_user.username}")
    cls_dict = ClassService.update_class(db, class_id, class_data)
    if not cls_dict:
        logger.warning(f"班级不存在: class_id={class_id}")
        raise HTTPException(status_code=404, detail="班级不存在")
    logger.info(f"班级更新成功: class_id={class_id}")
    return ResponseBase(code=200, message="更新成功", data=cls_dict)


@router.delete("/{class_id}", response_model=ResponseBase)
def delete_exist_class(
        class_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_admin),  # 仅管理员
        hard_delete: bool = Query(False, description="是否硬删除")
):
    logger.info(f"删除班级: class_id={class_id}, hard_delete={hard_delete}, 操作者: {current_user.username}")
    result = ClassService.delete_class(db, class_id, hard_delete=hard_delete)
    if result is False:
        logger.warning(f"班级不存在: class_id={class_id}")
        raise HTTPException(status_code=404, detail="班级不存在")
    msg = "硬删除成功" if hard_delete else "软删除成功"
    logger.info(f"班级删除成功: {msg}")
    return ResponseBase(code=200, message=msg, data=result)


@router.post("/{class_id}/restore", response_model=ResponseBase)
def restore_deleted_class(
        class_id: int, 
        db: Session = Depends(get_db),
        current_user: User = Depends(require_admin)  # 仅管理员
):
    logger.info(f"恢复班级: class_id={class_id}, 操作者: {current_user.username}")
    cls_dict = ClassService.restore_class(db, class_id)
    if not cls_dict:
        logger.warning(f"班级恢复失败: class_id={class_id}")
        raise HTTPException(status_code=404, detail="班级被删除或者不存在")
    logger.info(f"班级恢复成功: class_id={class_id}")
    return ResponseBase(code=200, message="恢复成功", data=cls_dict)
