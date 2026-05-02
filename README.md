# Team Task Manager

A full-stack web application that allows users to create projects, manage team members, assign tasks, and track progress using role-based access control.

---

## 📌 Features

### 🔐 Authentication
- User Signup and Login
- JWT-based authentication

---

### 📁 Project Management
- Any authenticated user can create a project
- The user who creates a project automatically becomes the **Admin of that project**

---

### 👥 Team Management
- Admin can add members to a project
- Members are linked to specific projects

---

### ✅ Task Management
- Admin can:
  - Create tasks
  - Assign tasks to team members
- Each task includes:
  - Title
  - Description
  - Due date
  - Assigned member

---

### 🔄 Task Status Tracking
- Task statuses:
  - To Do
  - In Progress
  - Done
- Members can update the status of their assigned tasks

---

### 🔐 Role-Based Access Control

Roles are **project-specific**, not global.

A user can have different roles in different projects:

- **Admin (for a project)**
  - Create tasks
  - Assign tasks
  - Add members

- **Member (for a project)**
  - View assigned tasks only
  - Update task status
  - Cannot assign tasks or add members

---

### 📊 Dashboard
- Displays tasks of the selected project
- Shows:
  - Total tasks
  - Completed tasks
  - Pending tasks

---

## 🛠️ Tech Stack

### Frontend
- HTML
- CSS
- JavaScript

### Backend
- Python (Flask)
- Flask-JWT-Extended
- Flask-SQLAlchemy

### Database
- SQLite

---

## ⚙️ Run Locally

```bash
git clone https://github.com/Gate2024/Team_Task_Manager.git
cd Team_Task_Manager

python -m venv venv
venv\Scripts\activate

pip install -r requirements.txt

python app.py