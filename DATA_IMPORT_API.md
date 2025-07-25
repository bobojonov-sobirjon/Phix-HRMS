# Data Import API

This API allows you to import data from JSON files into the database models for companies, education facilities, and certification centers.

## Base URL
```
http://localhost:8000/api/v1/data-management
```

## Endpoints

### 1. Import All Data
**POST** `/import-all`

Import all data from JSON files into the database models.

**Response:**
```json
{
    "message": "Data imported successfully",
    "data": {
        "companies_imported": 20,
        "education_facilities_imported": 50,
        "certification_centers_imported": 100,
        "total_imported": 170
    }
}
```

### 2. Get Import Statistics
**GET** `/stats`

Get statistics about the imported data and JSON files.

**Response:**
```json
{
    "database_stats": {
        "companies": 20,
        "education_facilities": 50,
        "certification_centers": 100,
        "total": 170
    },
    "json_file_stats": {
        "companies": 20,
        "education_facilities": 50,
        "certification_centers": 100,
        "total": 170
    }
}
```

## Features

- **Duplicate Prevention**: Checks if records already exist before importing
- **Batch Import**: Imports all data from JSON files in one request
- **Error Handling**: Continues importing even if individual records fail
- **Statistics**: Provides detailed import statistics
- **Database Models**: Imports data into proper database models instead of JSON files

## Data Sources

The API reads from these JSON files:
- `app/utils/files/it_companies.json` - Companies data
- `app/utils/files/it_certifications.json` - Certification centers data  
- `app/utils/files/education_institutions_corrected.json` - Education facilities data

## Database Models

Data is imported into these database models:
- `Company` - Companies with name, icon, country
- `EducationFacility` - Education facilities with name, icon, country
- `CertificationCenter` - Certification centers with name, icon

## Testing

You can test the API using the provided test script:

```bash
python test_data_import.py
```

## Usage Examples

```bash
# Import all data
curl -X POST "http://localhost:8000/api/v1/data-management/import-all"

# Get import statistics
curl -X GET "http://localhost:8000/api/v1/data-management/stats"
```

## Error Responses

### 500 Internal Server Error
When there's an error during import:
```json
{
    "detail": "Failed to import data: [error message]"
}
``` 