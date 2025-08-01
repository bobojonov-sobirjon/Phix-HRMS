from fastapi import APIRouter, HTTPException, Body, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from ..database import get_db
from ..models.company import Company
from ..models.education_facility import EducationFacility
from ..models.certification_center import CertificationCenter
from ..models.location import Location
import json
import os
import logging
from sqlalchemy import and_

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/data-management", tags=["Data Management"])

# File paths for JSON data
COMPANIES_FILE = "app/utils/files/it_companies.json"
CERTIFICATIONS_FILE = "app/utils/files/it_certifications.json"
EDUCATION_FILE = "app/utils/files/education_institutions_corrected.json"
COUNTRIES_FILE = "app/utils/files/countries.json"

def read_json_file(file_path: str) -> List[Dict[str, Any]]:
    """Read JSON file and return its content with error handling"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        return []
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error in {file_path}: {e}")
        return []
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        return []

def batch_insert_companies(db: Session, companies_data: List[Dict[str, Any]]) -> int:
    """Batch insert companies for better performance"""
    companies_imported = 0
    
    # Group companies by unique combinations to avoid duplicates
    unique_companies = {}
    for company_data in companies_data:
        key = (company_data.get("name"), company_data.get("country"), company_data.get("icon"))
        if key not in unique_companies:
            unique_companies[key] = company_data
    
    # Check existing companies in batch
    existing_companies = db.query(Company).filter(
        and_(
            Company.is_deleted == False
        )
    ).all()
    
    existing_keys = {(c.name, c.country, c.icon) for c in existing_companies}
    
    # Prepare new companies for batch insert
    new_companies = []
    for company_data in unique_companies.values():
        company_key = (company_data.get("name"), company_data.get("country"), company_data.get("icon"))
        if company_key not in existing_keys:
            company = Company(
                name=company_data.get("name"),
                icon=company_data.get("icon"),
                country=company_data.get("country")
            )
            new_companies.append(company)
            companies_imported += 1
    
    # Batch insert
    if new_companies:
        db.bulk_save_objects(new_companies)
        db.commit()
    
    return companies_imported

def batch_insert_education_facilities(db: Session, education_data: List[Dict[str, Any]]) -> int:
    """Batch insert education facilities for better performance"""
    education_imported = 0
    
    # Group by unique combinations
    unique_facilities = {}
    for edu_data in education_data:
        key = (edu_data.get("name"), edu_data.get("country"), edu_data.get("icon"))
        if key not in unique_facilities:
            unique_facilities[key] = edu_data
    
    # Check existing facilities in batch
    existing_facilities = db.query(EducationFacility).filter(
        and_(
            EducationFacility.is_deleted == False
        )
    ).all()
    
    existing_keys = {(f.name, f.country, f.icon) for f in existing_facilities}
    
    # Prepare new facilities for batch insert
    new_facilities = []
    for edu_data in unique_facilities.values():
        facility_key = (edu_data.get("name"), edu_data.get("country"), edu_data.get("icon"))
        if facility_key not in existing_keys:
            education_facility = EducationFacility(
                name=edu_data.get("name"),
                icon=edu_data.get("icon"),
                country=edu_data.get("country")
            )
            new_facilities.append(education_facility)
            education_imported += 1
    
    # Batch insert
    if new_facilities:
        db.bulk_save_objects(new_facilities)
        db.commit()
    
    return education_imported

def batch_insert_certification_centers(db: Session, certifications_data: List[Dict[str, Any]]) -> int:
    """Batch insert certification centers for better performance"""
    certifications_imported = 0
    
    # Group by unique combinations
    unique_certifications = {}
    for cert_data in certifications_data:
        key = (cert_data.get("name"), cert_data.get("icon"), cert_data.get("country"))
        if key not in unique_certifications:
            unique_certifications[key] = cert_data
    
    # Check existing certifications in batch
    existing_certifications = db.query(CertificationCenter).filter(
        and_(
            CertificationCenter.is_deleted == False
        )
    ).all()
    
    existing_keys = {(c.name, c.icon, c.country) for c in existing_certifications}
    
    # Prepare new certifications for batch insert
    new_certifications = []
    for cert_data in unique_certifications.values():
        cert_key = (cert_data.get("name"), cert_data.get("icon"), cert_data.get("country"))
        if cert_key not in existing_keys:
            certification_center = CertificationCenter(
                name=cert_data.get("name"),
                icon=cert_data.get("icon")
            )
            new_certifications.append(certification_center)
            certifications_imported += 1
    
    # Batch insert
    if new_certifications:
        db.bulk_save_objects(new_certifications)
        db.commit()
    
    return certifications_imported

def batch_insert_locations(db: Session, countries_data: List[Dict[str, Any]]) -> int:
    """Batch insert locations for better performance"""
    locations_imported = 0
    
    # Group by unique combinations
    unique_locations = {}
    for country_data in countries_data:
        key = (country_data.get("name"), country_data.get("flag_image"), country_data.get("code"))
        if key not in unique_locations:
            unique_locations[key] = country_data
    
    # Check existing locations in batch
    existing_locations = db.query(Location).filter(
        and_(
            Location.is_deleted == False
        )
    ).all()
    
    existing_keys = {(l.name, l.flag_image, l.code) for l in existing_locations}
    
    # Prepare new locations for batch insert
    new_locations = []
    for country_data in unique_locations.values():
        location_key = (country_data.get("name"), country_data.get("flag_image"), country_data.get("code"))
        if location_key not in existing_keys:
            location = Location(
                name=country_data.get("name"),
                flag_image=country_data.get("flag_image"),
                code=country_data.get("code")
            )
            new_locations.append(location)
            locations_imported += 1
    
    # Batch insert
    if new_locations:
        db.bulk_save_objects(new_locations)
        db.commit()
    
    return locations_imported

@router.post("/import-all")
async def import_all_data(db: Session = Depends(get_db)):
    """
    Import all data from JSON files into database models with optimized batch operations
    """
    try:
        # Read JSON files
        companies_data = read_json_file(COMPANIES_FILE)
        certifications_data = read_json_file(CERTIFICATIONS_FILE)
        education_data = read_json_file(EDUCATION_FILE)
        countries_data = read_json_file(COUNTRIES_FILE)
        
        logger.info(f"Starting import: {len(companies_data)} companies, {len(education_data)} education facilities, {len(certifications_data)} certifications, {len(countries_data)} locations")
        
        # Import companies using batch operations
        companies_imported = batch_insert_companies(db, companies_data)
        
        # Import education facilities using batch operations
        education_imported = batch_insert_education_facilities(db, education_data)
        
        # Import certification centers using batch operations
        certifications_imported = batch_insert_certification_centers(db, certifications_data)
        
        # Import locations using batch operations
        locations_imported = batch_insert_locations(db, countries_data)
        
        total_imported = companies_imported + education_imported + certifications_imported + locations_imported
        
        logger.info(f"Import completed: {total_imported} total records imported")
        
        return {
            "message": "Data imported successfully",
            "data": {
                "companies_imported": companies_imported,
                "education_facilities_imported": education_imported,
                "certification_centers_imported": certifications_imported,
                "locations_imported": locations_imported,
                "total_imported": total_imported
            }
        }
    
    except Exception as e:
        logger.error(f"Failed to import data: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to import data: {str(e)}")

@router.get("/stats")
async def get_import_stats(db: Session = Depends(get_db)):
    """
    Get statistics about imported data with optimized queries
    """
    try:
        # Count records in database using optimized queries
        companies_count = db.query(Company).filter(Company.is_deleted == False).count()
        education_count = db.query(EducationFacility).filter(EducationFacility.is_deleted == False).count()
        certifications_count = db.query(CertificationCenter).filter(CertificationCenter.is_deleted == False).count()
        locations_count = db.query(Location).filter(Location.is_deleted == False).count()
        
        # Count records in JSON files
        companies_data = read_json_file(COMPANIES_FILE)
        education_data = read_json_file(EDUCATION_FILE)
        certifications_data = read_json_file(CERTIFICATIONS_FILE)
        countries_data = read_json_file(COUNTRIES_FILE)
        
        return {
            "database_stats": {
                "companies": companies_count,
                "education_facilities": education_count,
                "certification_centers": certifications_count,
                "locations": locations_count,
                "total": companies_count + education_count + certifications_count + locations_count
            },
            "json_file_stats": {
                "companies": len(companies_data),
                "education_facilities": len(education_data),
                "certification_centers": len(certifications_data),
                "locations": len(countries_data),
                "total": len(companies_data) + len(education_data) + len(certifications_data) + len(countries_data)
            }
        }
    
    except Exception as e:
        logger.error(f"Failed to get stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}") 