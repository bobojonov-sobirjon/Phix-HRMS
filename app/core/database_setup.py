"""
Database table creation setup
"""
from ..db.database import engine
from ..models import (
    user, role, user_role, skill, user_skill, education, experience, certification,
    project, project_image, language, location, contact_us as contact_us_model,
    faq as faq_model, company as company_model, education_facility as education_facility_model,
    certification_center as certification_center_model, gig_job, proposal, saved_job,
    corporate_profile as corporate_profile_model, full_time_job as full_time_job_model,
    team_member as team_member_model, category as category_model, chat as chat_model,
    corporate_profile_follow as corporate_profile_follow_model, notification as notification_model
)


def create_all_tables():
    """Create all database tables"""
    models = [
        user, role, user_role, skill, user_skill, education, experience, certification,
        project, project_image, language, location, contact_us_model, faq_model,
        company_model, education_facility_model, certification_center_model, gig_job,
        proposal, saved_job, corporate_profile_model, full_time_job_model,
        team_member_model, category_model, chat_model, corporate_profile_follow_model,
        notification_model
    ]
    
    for model in models:
        model.Base.metadata.create_all(bind=engine)
