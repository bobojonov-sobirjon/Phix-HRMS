from fastapi import APIRouter, HTTPException, Body, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from ..database import get_db
from ..models.company import Company
from ..models.education_facility import EducationFacility
from ..models.certification_center import CertificationCenter
import json
import os

router = APIRouter(prefix="/data-management", tags=["Data Management"])

# File paths for JSON data
COMPANIES_FILE = "app/utils/files/it_companies.json"
CERTIFICATIONS_FILE = "app/utils/files/it_certifications.json"
EDUCATION_FILE = "app/utils/files/education_institutions_corrected.json"

def read_json_file(file_path: str) -> List[Dict[str, Any]]:
    """Read JSON file and return its content"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        return []

@router.post("/import-all")
async def import_all_data(db: Session = Depends(get_db)):
    """
    Import all data from JSON files into database models
    """
    try:
        # Read JSON files
        companies_data = read_json_file(COMPANIES_FILE)
        certifications_data = read_json_file(CERTIFICATIONS_FILE)
        education_data = read_json_file(EDUCATION_FILE)
        
        # Import companies
        companies_imported = 0
        for company_data in companies_data:
            try:
                # Check if company already exists
                existing_company = db.query(Company).filter(
                    Company.name == company_data.get("name"),
                    Company.country == company_data.get("country"),
                    Company.icon == company_data.get("icon"),
                    Company.is_deleted == False
                ).first()
                
                if not existing_company:
                    company = Company(
                        name=company_data.get("name"),
                        icon=company_data.get("icon"),
                        country=company_data.get("country")
                    )
                    db.add(company)
                    companies_imported += 1
            except Exception as e:
                print(f"Error importing company {company_data.get('name')}: {e}")
        
        # Import education facilities
        education_imported = 0
        for edu_data in education_data:
            try:
                # Check if education facility already exists
                existing_edu = db.query(EducationFacility).filter(
                    EducationFacility.name == edu_data.get("name"),
                    EducationFacility.country == edu_data.get("country"),
                    EducationFacility.icon == edu_data.get("icon"),
                    EducationFacility.is_deleted == False
                ).first()
                
                if not existing_edu:
                    education_facility = EducationFacility(
                        name=edu_data.get("name"),
                        icon=edu_data.get("icon"),
                        country=edu_data.get("country")
                    )
                    db.add(education_facility)
                    education_imported += 1
            except Exception as e:
                print(f"Error importing education facility {edu_data.get('name')}: {e}")
        
        # Import certification centers
        certifications_imported = 0
        for cert_data in certifications_data:
            try:
                # Check if certification center already exists
                existing_cert = db.query(CertificationCenter).filter(
                    CertificationCenter.name == cert_data.get("name"),
                    CertificationCenter.icon == cert_data.get("icon"),
                    CertificationCenter.country == cert_data.get("country"),
                    CertificationCenter.is_deleted == False
                ).first()
                
                if not existing_cert:
                    certification_center = CertificationCenter(
                        name=cert_data.get("name"),
                        icon=cert_data.get("icon")
                    )
                    db.add(certification_center)
                    certifications_imported += 1
            except Exception as e:
                print(f"Error importing certification center {cert_data.get('name')}: {e}")
        
        # Commit all changes
        db.commit()
        
        return {
            "message": "Data imported successfully",
            "data": {
                "companies_imported": companies_imported,
                "education_facilities_imported": education_imported,
                "certification_centers_imported": certifications_imported,
                "total_imported": companies_imported + education_imported + certifications_imported
            }
        }
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to import data: {str(e)}")

@router.get("/stats")
async def get_import_stats(db: Session = Depends(get_db)):
    """
    Get statistics about imported data
    """
    try:
        # Count records in database
        companies_count = db.query(Company).filter(Company.is_deleted == False).count()
        education_count = db.query(EducationFacility).filter(EducationFacility.is_deleted == False).count()
        certifications_count = db.query(CertificationCenter).filter(CertificationCenter.is_deleted == False).count()
        
        # Count records in JSON files
        companies_data = read_json_file(COMPANIES_FILE)
        education_data = read_json_file(EDUCATION_FILE)
        certifications_data = read_json_file(CERTIFICATIONS_FILE)
        
        return {
            "database_stats": {
                "companies": companies_count,
                "education_facilities": education_count,
                "certification_centers": certifications_count,
                "total": companies_count + education_count + certifications_count
            },
            "json_file_stats": {
                "companies": len(companies_data),
                "education_facilities": len(education_data),
                "certification_centers": len(certifications_data),
                "total": len(companies_data) + len(education_data) + len(certifications_data)
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}") 