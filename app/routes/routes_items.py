from fastapi import APIRouter
from app.controllers import (
    get_all_tasks, 
    get_task_by_id, 
    create_task, 
    update_task,
    delete_task
    )

router = APIRouter()

router.get("/", response_model=list)(get_all_tasks)
router.get("/{task_id}", response_model=dict)(get_task_by_id)
router.post("/", response_model=dict)(create_task)
router.put("/{task_id}", response_model=dict)(update_task)
router.delete("/{task_id}", response_model=dict)(delete_task)