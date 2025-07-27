# Migration Guide for New Models in Phix HRMS

This guide explains how to add a new database model and migrate it using Alembic in the Phix HRMS project. Follow these steps **after** you've created your new model file (e.g., in `app/models/new_model.py`).

## Prerequisites
- Ensure your new model subclasses `Base` from `app.database` (e.g., `class NewModel(Base): ...`).
- Make sure the model defines `__tablename__` and all columns/relationships correctly.
- Have Alembic set up (it already is in this project).

## Step-by-Step Instructions

### Step 1: Import the New Model in Alembic Configuration
Alembic needs to "see" your new model for autogeneration. Add an import for it in `alembic/env.py`.

Open `alembic/env.py` and add the import below the existing model imports:

```
# Import ALL models here so Alembic can detect them for autogeneration
from app.models.user import User
from app.models.otp import OTP
from app.models.location import Location

from app.models.new_model import NewModel
```

Replace `new_model` and `NewModel` with your actual file and class names.

### Step 2: Generate a New Migration
Run this command in your terminal from the project root (`/d:/Projects/Phix-Hrms`):

```
alembic revision --autogenerate -m "Add NewModel table"
```

- This creates a new file in `alembic/versions/` (e.g., `XXXX_add_newmodel_table.py`).
- The `-m` flag adds a description; make it descriptive (e.g., "Add NewModel table and relationships").

### Step 3: Review and Edit the Migration File (If Needed)
- Open the new migration file in `alembic/versions/`.
- Check the `upgrade()` function: It should include `op.create_table()` for your new model.
- Verify any foreign keys, indexes, or relationships are correct.
- If something is missing or wrong (e.g., due to complex relationships), edit it manually.
- Also check the `downgrade()` function for reversibility (e.g., `op.drop_table()`).

### Step 4: Apply the Migration
Run this command to apply the changes to the database:

```
alembic upgrade head
```

- This will create the new table in your PostgreSQL database (`phix_hrms`).
- If there are errors (e.g., conflicts with existing data), resolve them and re-run.

### Step 5: Verify the Changes
- Connect to your database (e.g., using pgAdmin or `psql`).
- Check that the new table exists and has the correct columns.
- Test your application to ensure the new model works (e.g., via API endpoints or tests).

## Tips and Best Practices
- **Always Backup Your Database**: Before applying migrations, especially in production.
- **Handle Relationships**: If your new model has foreign keys to existing tables, ensure those tables exist (they should via prior migrations).
- **Multiple Changes**: If adding multiple models or fields, do them in one migration for atomicity.
- **Downgrade Testing**: Test `alembic downgrade -1` to ensure reversibility.
- **Environment Variables**: Ensure your `.env` file has the correct `DATABASE_URL`.
- **Common Errors**:
  - "Target database is not up to date": Run `alembic upgrade head` first.
  - Model not detected: Double-check imports in `alembic/env.py`.
- **Production**: In production, avoid `--autogenerate` and manually write migrations for control.

If you encounter issues, check the Alembic docs or consult the project README.

Last updated: [Insert Date] 

sudo systemctl start gunicorn.socket
sudo systemctl enable gunicorn.socket
sudo systemctl daemon-reload
sudo systemctl restart gunicorn