"""
Router setup and registration
"""
from fastapi import FastAPI
from ..api import (
    auth, profile, contact_us, faq, skills, roles, languages, locations,
    user_skills, data_management, company, education_facility, certification_center,
    gig_jobs, proposals, saved_jobs, corporate_profile, full_time_job, team_member,
    category, chat, corporate_profile_follow, notifications
)


def register_routers(app: FastAPI):
    """Register all API routers"""
    routers = [
        (auth, "/api/v1"),
        (profile, "/api/v1"),
        (contact_us, "/api/v1"),
        (faq, "/api/v1"),
        (skills, "/api/v1"),
        (roles, "/api/v1"),
        (languages, "/api/v1"),
        (locations, "/api/v1"),
        (user_skills, "/api/v1"),
        (data_management, "/api/v1"),
        (company.router, "/api/v1"),
        (education_facility.router, "/api/v1"),
        (certification_center.router, "/api/v1"),
        (gig_jobs, "/api/v1"),
        (proposals, "/api/v1"),
        (saved_jobs.router, "/api/v1"),
        (corporate_profile.router, "/api/v1"),
        (corporate_profile_follow.router, "/api/v1"),
        (full_time_job.router, "/api/v1"),
        (team_member.router, "/api/v1"),
        (category.router, "/api/v1"),
        (chat.router, "/api/v1/chat"),
        (notifications.router, "/api/v1"),
    ]
    
    for router, prefix in routers:
        app.include_router(router, prefix=prefix)
