# PRD: AI-Powered Business Data Crawler - Web & Database MVP

## User Interaction and Design Goals

Overall Vision & Experience: The primary goal is to transform the existing command-line tool into a professional, user-friendly, and data-intensive web application. The experience should empower users to visually interact with the collected business data, manage scraping jobs, and view results without ever touching a command-line interface or manually opening JSON files.
Key Interaction Paradigms:
A central, interactive dashboard for at-a-glance insights into the scraped data.
A powerful, filterable, and searchable data table/grid to explore collected business information.
Simple, form-based workflows for initiating and monitoring new scraping jobs.
Core Screens/Views (Conceptual):
Dashboard: The landing page after login, displaying key metrics.
Data Explorer: A view for all cleaned data featuring a searchable and filterable table/grid.
Business Detail View: A page displaying all structured fields for a single business.
Job Management Page: A UI-driven replacement for the main.py CLI menu.
Settings Page: A secure page for managing the API Key for the Google Gemini 2.5 model.
Target Devices/Platforms: The initial focus is on a web desktop experience, with a responsive design usable on tablets.
Functional Requirements (MVP)
The system shall display a dashboard summarizing the contents of the output/cleaned/ directories.
Users must be able to view all cleaned business data in a paginated, searchable, and filterable table.
Users must be able to start new scraping jobs by submitting search terms or website URLs through a form.
The UI shall provide real-time feedback on the status of active scraping jobs.
The system shall persist the final, cleaned business data to a specified MongoDB collection.
The AI data extraction process will specifically use the Google Gemini 2.5 model.
The system shall include backend logic to detect and merge duplicate business entities.
The system shall provide a manual tool or script to ingest data from a JSON file into the database.
The application's logs shall be saved to a dedicated collection in the MongoDB database.
Non-Functional Requirements (MVP)
Performance: The Data Explorer page must load and render at least 1,000 business records with interactive filtering and sorting in under 3 seconds.
Usability: The web interface must be intuitive enough for a non-technical user to operate without requiring documentation.
Security: The Google API Key for Gemini 2.5 must not be exposed to the client-side browser.
Data Integrity: Data written to MongoDB must be identical to the data written to JSON file outputs and pass Pydantic schema validation.
Reliability & Portability: The entire application (frontend and backend) must be containerized using Docker for easy and consistent deployment on any machine.
Technical Assumptions
A backend API will be created to serve data from MongoDB, handle job requests, and provide status updates.
The architecture will be updated to include a MongoDB database.
The data extraction will be powered by the Google Gemini 2.5 model, requiring a GOOGLE_API_KEY.
The frontend will be developed using the Nuxt.js framework.
Epic Overview
Epic 1: Web Application Interface & Database MVP
Goal: To provide a complete, web-based graphical user interface that allows users to view all collected business data and manage scraping jobs, and to establish a scalable database backend for data persistence.
Story 1.0: As a system administrator, I want the initial project and infrastructure setup, so that development can begin on a clean foundation (Nuxt, API, Dockerfile).
Story 1.1: As a user, I want to see a dashboard with key metrics, so that I can get a quick overview of the collected data.
Story 1.2: As a user, I want a data explorer page where I can search, filter, and sort all collected businesses, so that I can easily find the information I need.
Story 1.3: As a user, I want to view all the details of a single business on a dedicated page, so that I can analyze its specific information.
Story 1.4: As a user, I want a "New Job" page where I can start scraping tasks, so that I don't have to use the CLI menu.
Story 1.5: As a user, I want to see the status of my active and completed jobs, so I know when my data is ready.
Story 1.6: As a system administrator, I want the cleaned business data to be automatically saved to a MongoDB database, so that it can be queried more efficiently.
Story 1.7: As a system administrator, I want the application to detect and merge duplicate business entities during the data cleaning process, so that the final database is accurate.
Story 1.8: As a system administrator, I want a manual tool to ingest data from a JSON file into MongoDB, so that I can import historical data.
Story 1.9: As a system administrator, I want the application's logs to be saved to a MongoDB collection, so that I can easily query and analyze log data.

## Out of Scope Ideas Post MVP

Advanced data analytics and visualization dashboard.
A specialized scraper to find and backfill null data fields for existing records.
A UI-based tool for manually reviewing and managing potential duplicates.
