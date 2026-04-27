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
# app/db/models/job_role.py
from sqlalchemy import Column, String, Text, Integer, ForeignKey, Boolean, Float, JSON
from sqlalchemy.orm import relationship
from app.db.models.base import BaseModel

class JobRole(BaseModel):
    __tablename__ = "job_roles"
    
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    required_skills = Column(JSON, default=[])
    is_remote = Column(Boolean, default=False)
    cutoff_score = Column(Float, default=60.0)
    
    # Relationship Example
    interviews = relationship("Interview", back_populates="job_role")
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
Connect your FastAPI router to handle incoming HTTP requests using your dependencies and models.

```python
# app/routers/campaign.py
from fastapi import APIRouter, Depends
from sqlalchemy import select
from app.db.session import get_session_maker
from app.deps import get_current_organization
from app.db.models.job_role import JobRole
from app.db.models.organization import Organization
from app.schemas.campaign import CampaignCreate

router = APIRouter(prefix="/campaigns", tags=["Campaigns"])

@router.post("/")
async def create_campaign(campaign: CampaignCreate, org: Organization = Depends(get_current_organization)):
    session_maker = get_session_maker()
    async with session_maker() as session:
        new_campaign = JobRole(organization_id=org.id, **campaign.model_dump())
        session.add(new_campaign)
        await session.commit()
        await session.refresh(new_campaign)
        return new_campaign
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
