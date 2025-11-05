# PlanningApp
This is an app for Backlog Estimation.
A user can create an estimation session and add user stories and tasks to estimate. This user is called the admin.
Other users can join with just the link to the session.

An estimation session goes as follows:
- The admin selects the user story and the according tasks to estimate
- The admin and the other users can estimate the effort for the tasks that dont have an estimation yet. They can select from planning poker like cards.
- Voting ends whe all users cast their votes or when a timer has completed
- The estimate from the tasks is summed up in the user story.
- We start from the top to estimate the next items

## Tech Stack
### Backend
- Django 5.2.7

### Frontend
- Django Templates
- HTMX
- Alpine.js

## Design and Usability
Desktop-First App with modern design like Notion.
Votes from other users and other updates need to be shown LIVE to all users.

## Setup Instructions

### Prerequisites
- Python 3.11+
- pip

### Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run migrations:
```bash
python manage.py migrate
```

3. Create a superuser (optional, for admin access):
```bash
python manage.py createsuperuser
```

4. Run the development server:
```bash
python manage.py runserver
```

5. Open your browser and navigate to:
```
http://localhost:8000
```

### Usage

1. **Create a Session**: Click "Create New Session" and enter a session name and your name as admin
2. **Add User Stories**: Once in the session, use the admin controls to add user stories
3. **Add Tasks**: Under each user story, add tasks that need to be estimated
4. **Invite Participants**: Share the session URL with team members
5. **Start Voting**: Click "Start Voting" on any task without an estimate
6. **Cast Votes**: All participants select their estimate using planning poker cards (0, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, ?)
7. **View Results**: Voting automatically ends when all participants vote or the timer expires
8. **Set Final Estimate**: Admin sets the final estimate based on the results
9. **Continue**: Move to the next task and repeat

### Features

- Real-time updates using WebSockets (Django Channels)
- Planning poker card voting (Fibonacci sequence)
- Automatic voting timer (60 seconds)
- Admin controls for managing sessions
- Notion-like modern UI
- Desktop-first responsive design
- Live participant tracking
- Automatic estimate summation for user stories

### Database

The app uses SQLite by default for easy setup. The database file is `db.sqlite3` in the project root.
