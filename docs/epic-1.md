Epic 1: Web Application Interface & Database MVP
Goal: To provide a complete, web-based graphical user interface that allows users to view all collected business data and manage scraping jobs, and to establish a scalable database backend for data persistence.

Stories:

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