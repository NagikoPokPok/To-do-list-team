"""
Tasks API Controller - Quản lý công việc
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# Schemas
class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    priority: str = "medium"
    due_date: Optional[datetime] = None

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    due_date: Optional[datetime] = None

class Task(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    priority: str
    status: str
    due_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    assignee_id: Optional[int] = None
    team_id: Optional[int] = None

# Router
router = APIRouter(prefix="/api/v1/tasks", tags=["Tasks"])

# Mock data
MOCK_TASKS = [
    {
        "id": 1,
        "title": "Hoàn thành báo cáo tuần",
        "description": "Tổng hợp kết quả công việc tuần này",
        "priority": "high",
        "status": "in_progress",
        "due_date": "2025-09-30T23:59:59",
        "created_at": "2025-09-26T10:00:00",
        "updated_at": "2025-09-26T10:00:00",
        "assignee_id": 1,
        "team_id": 1
    },
    {
        "id": 2,
        "title": "Review code pull request",
        "description": "Kiểm tra và review các pull request mới",
        "priority": "medium",
        "status": "todo",
        "due_date": "2025-09-28T17:00:00",
        "created_at": "2025-09-26T09:30:00",
        "updated_at": "2025-09-26T09:30:00",
        "assignee_id": 1,
        "team_id": 1
    },
    {
        "id": 3,
        "title": "Cập nhật tài liệu API",
        "description": "Cập nhật documentation cho các API mới",
        "priority": "low",
        "status": "completed",
        "due_date": "2025-09-27T16:00:00",
        "created_at": "2025-09-25T14:00:00",
        "updated_at": "2025-09-26T11:00:00",
        "assignee_id": 1,
        "team_id": 1
    }
]

@router.get("/", response_model=List[dict])
async def get_tasks(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None)
):
    """Get list of tasks"""
    print(f"📋 Getting tasks: limit={limit}, offset={offset}, status={status}, priority={priority}")
    
    tasks = MOCK_TASKS.copy()
    
    # Filter by status
    if status:
        tasks = [task for task in tasks if task["status"] == status]
    
    # Filter by priority
    if priority:
        tasks = [task for task in tasks if task["priority"] == priority]
    
    # Apply pagination
    total = len(tasks)
    tasks = tasks[offset:offset + limit]
    
    return {
        "tasks": tasks,
        "total": total,
        "limit": limit,
        "offset": offset
    }

@router.post("/", response_model=dict)
async def create_task(task_data: TaskCreate):
    """Create a new task"""
    print(f"📝 Creating task: {task_data.title}")
    
    new_task = {
        "id": len(MOCK_TASKS) + 1,
        "title": task_data.title,
        "description": task_data.description,
        "priority": task_data.priority,
        "status": "todo",
        "due_date": task_data.due_date.isoformat() if task_data.due_date else None,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "assignee_id": 1,
        "team_id": 1
    }
    
    MOCK_TASKS.append(new_task)
    
    return {
        "message": "Task tạo thành công",
        "task": new_task
    }

@router.get("/{task_id}", response_model=dict)
async def get_task(task_id: int):
    """Get task by ID"""
    print(f"🔍 Getting task: {task_id}")
    
    task = next((task for task in MOCK_TASKS if task["id"] == task_id), None)
    
    if not task:
        raise HTTPException(status_code=404, detail="Task không tìm thấy")
    
    return task

@router.put("/{task_id}", response_model=dict)
async def update_task(task_id: int, task_data: TaskUpdate):
    """Update task"""
    print(f"✏️ Updating task: {task_id}")
    
    task = next((task for task in MOCK_TASKS if task["id"] == task_id), None)
    
    if not task:
        raise HTTPException(status_code=404, detail="Task không tìm thấy")
    
    # Update fields
    if task_data.title is not None:
        task["title"] = task_data.title
    if task_data.description is not None:
        task["description"] = task_data.description
    if task_data.priority is not None:
        task["priority"] = task_data.priority
    if task_data.status is not None:
        task["status"] = task_data.status
    if task_data.due_date is not None:
        task["due_date"] = task_data.due_date.isoformat()
    
    task["updated_at"] = datetime.now().isoformat()
    
    return {
        "message": "Task cập nhật thành công",
        "task": task
    }

@router.delete("/{task_id}", response_model=dict)
async def delete_task(task_id: int):
    """Delete task"""
    print(f"🗑️ Deleting task: {task_id}")
    
    task_index = next((i for i, task in enumerate(MOCK_TASKS) if task["id"] == task_id), None)
    
    if task_index is None:
        raise HTTPException(status_code=404, detail="Task không tìm thấy")
    
    deleted_task = MOCK_TASKS.pop(task_index)
    
    return {
        "message": "Task xóa thành công",
        "task": deleted_task
    }

@router.get("/health", response_model=dict)
async def health_check():
    """Health check"""
    return {
        "status": "healthy",
        "service": "tasks",
        "version": "1.0.0",
        "total_tasks": len(MOCK_TASKS)
    }