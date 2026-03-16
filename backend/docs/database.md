# Supabase Database Guide

This guide explains how to create tables and manage data within our AI Interview Analysis project.

We use **Supabase** (PostgreSQL) as our database under the hood. There are two primary ways to manage your tables: via the Supabase Dashboard, or directly from the backend code utilizing SQLAlchemy.

---

## 🚀 Option 1: Supabase Dashboard (Recommended)

This is the easiest way to interact with your data visually and write raw SQL.

1. Navigate to your project on the [Supabase Dashboard](https://supabase.com/dashboard).
2. Go to the **SQL Editor** tab.
3. Run standard PostgreSQL statements to create your tables. 

### SQL Example

```sql
-- Example: Create an interviews table
CREATE TABLE interviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    candidate_email TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Example: Create questions table with a foreign key relation
CREATE TABLE interview_questions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    interview_id UUID REFERENCES interviews(id) ON DELETE CASCADE,
    question_text TEXT NOT NULL,
    answer_text TEXT,
    score INTEGER,
    created_at TIMESTAMPTZ DEFAULT now()
);
```

---

## 🛠️ Option 2: From Backend Code (SQLAlchemy)

You can define your database schema directly in Python using SQLAlchemy ORM models.

### Step 1: Define your models
Add your new model to `app/db/models/`. Example for an `Interview` model:

```python
# app/db/models/interview.py
from sqlalchemy import Column, String, Text, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.models.base import BaseModel

class Interview(BaseModel):
    __tablename__ = "interviews"
    
    title = Column(String(255), nullable=False)
    candidate_email = Column(String(255), nullable=False)
    status = Column(String(50), default="pending")
    
    # Relationship Example
    questions = relationship("InterviewQuestion", back_populates="interview")
```

### Step 2: Ensure Tables are Created
In standard practices, Alembic handle migrations. Under rapid prototyping, tables can be quickly synced in your lifespan hook (e.g., `app/main.py`):

```python
from app.db.session import get_engine, Base
from app.db.models import *  # Import models to ensure they're registered

async def create_tables():
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
```

### Step 3: Manipulate Data via Services
Create a dedicated service file for business logic involving the database.

```python
# app/db/services/interview_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models.interview import Interview

class InterviewService:
    async def create_interview(self, db: AsyncSession, title: str, email: str):
        interview = Interview(title=title, candidate_email=email)
        db.add(interview)
        await db.commit()
        await db.refresh(interview)
        return interview
```

### Step 4: Add to Routers
Connect your FastAPI router to the service logic to handle incoming HTTP requests.

```python
# app/routers/interviews.py
from fastapi import APIRouter, Depends
from app.db.session import get_db
from app.db.services.interview_service import interview_service

router = APIRouter(prefix="/interviews", tags=["Interviews"])

@router.post("/")
async def create_interview(title: str, email: str, db = Depends(get_db)):
    return await interview_service.create_interview(db, title, email)
```

---

## 📚 Quick Reference: Common SQLAlchemy Types

| SQLAlchemy Type                | PostgreSQL Equivalent |
| ------------------------------ | --------------------- |
| `Column(String(255))`          | `VARCHAR(255)`        |
| `Column(Text)`                 | `TEXT`                |
| `Column(Integer)`              | `INTEGER`             |
| `Column(Boolean)`              | `BOOLEAN`             |
| `Column(DateTime)`             | `TIMESTAMP`           |
| `Column(UUID(as_uuid=True))`   | `UUID`                |
| `Column(ForeignKey("table.id"))` | `Foreign Key`       |

---

## 💡 Pro Tip: Viewing Data

Whenever you need to verify if data actually saved correctly:
- Look at the **Table Editor** inside the Supabase Dashboard.
- Alternatively, run `SELECT * FROM interviews;` inside the Supabase SQL Editor.
