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
- SQLite

### Frontend
- Django Templates
- HTMX
- Alpine.js

## Design and Usability
Desktop-First App with modern design like Notion.
Votes from other users and other updates need to be shown LIVE to all users.
