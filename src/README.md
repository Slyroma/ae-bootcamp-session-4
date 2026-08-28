# Slalom Capabilities Management API

<p align="center">
  <img src="./.images/byte-teacher.png" alt="Byte Teacher" width="200" />
</p>

A FastAPI application that enables Slalom consultants to register their capabilities and manage consulting expertise across the organization.

## Features

- View all available consulting capabilities
- Register consultant expertise and availability
- Track skill levels and certifications
- Manage capability capacity and team assignments

## Getting Started

1. Install the dependencies:

   ```
   pip install fastapi uvicorn
   ```

2. Run the application:

   ```
   python app.py
   ```

3. Open your browser and go to:
   - API documentation: http://localhost:8000/docs
   - Alternative documentation: http://localhost:8000/redoc
   - Capabilities Dashboard: http://localhost:8000/

## API Endpoints

| Method | Endpoint                                                          | Description                                                         |
| ------ | ----------------------------------------------------------------- | ------------------------------------------------------------------- |
| POST   | `/auth/login`                                                     | Authenticate a practice lead and return a bearer token             |
| POST   | `/auth/logout`                                                    | End the current authenticated session                              |
| GET    | `/auth/me`                                                        | Validate token and return current authenticated user               |
| GET    | `/capabilities`                                                   | Get all capabilities with details and current consultant assignments |
| POST   | `/capabilities/{capability_name}/register?email=consultant@slalom.com` | Register consultant for a capability                     |
| DELETE | `/capabilities/{capability_name}/unregister?email=consultant@slalom.com` | Unregister consultant from a capability              |

## Practice Lead Authentication

- Role-based access is enforced for registration and unregistration actions.
- Sessions expire after eight hours and can be ended from the dashboard.
- Practice leads can modify capabilities only in their assigned practice areas.
- Login, logout, authorization, and capability changes are written to the server audit log.
- Use the following seeded accounts for local testing:
   - Username: `mona.lead` / Password: `lead123!`
   - Username: `marcus.lead` / Password: `strategy456!`

## Data Model

The application uses a consulting-focused data model:

1. **Capabilities** - Uses capability name as identifier:
   - Description of the consulting capability
   - Skill levels (Emerging, Proficient, Advanced, Expert)
   - Practice area (Strategy, Technology, Operations)
   - Industry verticals served
   - Required certifications
   - List of consultant emails registered
   - Available capacity (hours per week)
   - Geographic location preferences

2. **Consultants** - Uses email as identifier:
   - Name
   - Practice area
   - Skill level
   - Certifications
   - Availability

All data is currently stored in memory for this learning exercise. In a production environment, this would be backed by a robust database system.

## Future Enhancements

This exercise will guide you through implementing:
- Capability maturity assessments
- Intelligent team matching algorithms  
- Analytics dashboards for practice leads
- Integration with project management systems
- Advanced search and filtering capabilities
