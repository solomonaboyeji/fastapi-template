#!/bin/bash

# Prompt for the project name
read -p "Enter the project name: " PROJECT_NAME

# Create the main project directory
mkdir -p "$PROJECT_NAME"

# Define subdirectories
DIRECTORIES=(
    "api/routes"
    "core"
    "models"
    "schemas"
    "services"
    "dao"
    "utils"
    "i18n/en"
    "i18n/es"
    "migrations"
    "tests/test_api"
    "tests/test_services"
)

# Create subdirectories
for dir in "${DIRECTORIES[@]}"; do
    mkdir -p "$PROJECT_NAME/$dir"
done

# Create sample files
touch "$PROJECT_NAME/api/routes/user_routes.py"
touch "$PROJECT_NAME/core/config.py"
touch "$PROJECT_NAME/core/database.py"
touch "$PROJECT_NAME/core/localization.py"
touch "$PROJECT_NAME/models/user.py"
touch "$PROJECT_NAME/schemas/user_schema.py"
touch "$PROJECT_NAME/services/user_service.py"
touch "$PROJECT_NAME/dao/user_dao.py"
touch "$PROJECT_NAME/utils/security.py"
touch "$PROJECT_NAME/utils/responses.py"
touch "$PROJECT_NAME/utils/exception_handlers.py"
touch "$PROJECT_NAME/i18n/en/messages.po"
touch "$PROJECT_NAME/i18n/en/errors.po"
touch "$PROJECT_NAME/i18n/es/messages.po"
touch "$PROJECT_NAME/i18n/es/errors.po"
touch "$PROJECT_NAME/migrations/001_initial_setup.sql"
touch "$PROJECT_NAME/tests/test_api/test_user_routes.py"
touch "$PROJECT_NAME/tests/test_services/test_user_service.py"

# Create README file in the project root
cat <<EOF > $PROJECT_NAME/README.md
# $PROJECT_NAME

This is the main directory for $PROJECT_NAME.

## Structure

- \`api/\`: Contains API routes and dependencies.
- \`core/\`: Core application configurations.
- \`models/\`: Database models.
- \`schemas/\`: Pydantic schemas for data validation.
- \`services/\`: Business logic layer.
- \`dao/\`: Data Access Objects.
- \`utils/\`: Utility functions and classes.
- \`migrations/\`: SQL migration scripts.
- \`tests/\`: Test cases for the application.
- \`i18n/\`: Internationalization resources.

Each subdirectory contains relevant files for each aspect of the application.
EOF

# Create a basic .gitignore file
cat <<EOF > $PROJECT_NAME/.gitignore
# Python
__pycache__/
*.py[cod]
*.pyc

# Virtual environment
venv/
EOF

# Create a basic requirements.txt file
cat <<EOF > $PROJECT_NAME/requirements.txt
fastapi==0.65.2
sqlalchemy==1.4.15
pydantic==1.8.2
uvicorn[standard]==0.13.4
python-multipart
bcrypt
python-jose[cryptography]
python-dotenv
psycopg2-binary
EOF

# Display message
echo "Project structure for '$PROJECT_NAME' created successfully."
