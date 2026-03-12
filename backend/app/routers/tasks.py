from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.dependencies import get_db, require_groups
from app.models.task import Task
from app.models.user import User
from app.schemas.task import TaskOut, TaskCreate, TaskUpdate

router = APIRouter(prefix="/tasks", tags=["tasks"])


def _row_to_out(task: Task, creator: Optional[User] = None) -> TaskOut:
    return TaskOut(
        id=task.id,
        title=task.title,
        description=task.description,
        deadline=task.deadline,
        is_done=task.is_done,
        created_by_user_id=task.created_by_user_id,
        created_by_name=creator.full_name if creator else None,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


@router.get("", response_model=List[TaskOut])
async def get_tasks(
    filter: Optional[str] = None,  # 'active' | 'done'
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_groups("office_group", "admin_group")),
):
    stmt = select(Task).order_by(Task.is_done, Task.deadline.asc().nullslast(), Task.created_at.desc())
    if filter == "active":
        stmt = stmt.where(Task.is_done == False)
    elif filter == "done":
        stmt = stmt.where(Task.is_done == True)
    result = await db.execute(stmt)
    tasks = result.scalars().all()

    # Load creators
    user_ids = {t.created_by_user_id for t in tasks if t.created_by_user_id}
    creators = {}
    if user_ids:
        ur = await db.execute(select(User).where(User.id.in_(user_ids)))
        for u in ur.scalars().all():
            creators[u.id] = u

    return [_row_to_out(t, creators.get(t.created_by_user_id)) for t in tasks]


@router.post("", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
async def create_task(
    body: TaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_groups("office_group", "admin_group")),
):
    task = Task(
        title=body.title,
        description=body.description,
        deadline=body.deadline,
        created_by_user_id=current_user.id,
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return _row_to_out(task, current_user)


@router.put("/{task_id}", response_model=TaskOut)
async def update_task(
    task_id: int,
    body: TaskUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_groups("office_group", "admin_group")),
):
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    if body.title is not None:
        task.title = body.title
    if body.description is not None:
        task.description = body.description
    if body.deadline is not None:
        task.deadline = body.deadline
    if body.is_done is not None:
        task.is_done = body.is_done

    await db.commit()
    await db.refresh(task)

    creator = None
    if task.created_by_user_id:
        cr = await db.execute(select(User).where(User.id == task.created_by_user_id))
        creator = cr.scalar_one_or_none()
    return _row_to_out(task, creator)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_groups("office_group", "admin_group")),
):
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    await db.delete(task)
    await db.commit()
