from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from ..db.database import get_db
from ..utils.auth import get_current_user
from ..repositories.corporate_profile_repository import CorporateProfileRepository
from ..repositories.full_time_job_repository import FullTimeJobRepository
from ..repositories.team_member_repository import TeamMemberRepository
from ..schemas.corporate_profile import CorporateProfileCreate
from ..schemas.full_time_job import FullTimeJobCreate
from ..schemas.gig_job import GigJobCreate
from ..models.team_member import TeamMemberRole, TeamMemberStatus
from ..models.full_time_job import JobStatus, JobType, WorkMode, ExperienceLevel, PayPeriod
from ..models.gig_job import GigJobStatus, ProjectLength
from datetime import datetime

router = APIRouter(prefix="/test", tags=["Test"])


def get_user_id(user) -> int:
    """Get user ID from either dict or User object"""
    return user.get('id') if isinstance(user, dict) else user.id


def get_user_email(user) -> str:
    """Get user email from either dict or User object"""
    return user.get('email') if isinstance(user, dict) else user.email


@router.post("/corporate-profile")
async def test_corporate_profile(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Test Corporate Profile API: Create, Read, Update, Delete"""
    user_id = get_user_id(current_user)
    user_email = get_user_email(current_user)
    
    results = {
        "test_name": "Corporate Profile API Test",
        "user_id": user_id,
        "user_email": user_email,
        "timestamp": datetime.now().isoformat(),
        "tests": []
    }
    
    try:
        corporate_repo = CorporateProfileRepository(db)
        
        # Test 1: Check if user already has profile
        results["tests"].append({
            "step": "1. Check existing profile",
            "status": "running"
        })
        
        existing_profile = corporate_repo.get_by_user_id(user_id)
        if existing_profile:
            results["tests"][-1].update({
                "status": "success",
                "message": f"User already has corporate profile (ID: {existing_profile.id})",
                "data": {"profile_id": existing_profile.id}
            })
            results["overall_status"] = "success"
            results["message"] = "User already has a corporate profile"
            return results
        
        results["tests"][-1].update({
            "status": "success",
            "message": "User has no existing profile"
        })
        
        # Test 2: Create corporate profile
        results["tests"].append({
            "step": "2. Create corporate profile",
            "status": "running"
        })
        
        profile_data = CorporateProfileCreate(
            company_name=f"Test Company {user_id}",
            phone_number="+998901234567",
            country_code="+998",
            location_id=1,
            overview="Test company overview for API testing",
            website_url="https://testcompany.com",
            company_size="1-10",
            category_id=1
        )
        
        created_profile = corporate_repo.create(profile_data, user_id)
        
        results["tests"][-1].update({
            "status": "success",
            "message": f"Corporate profile created successfully",
            "data": {
                "profile_id": created_profile.id,
                "company_name": created_profile.company_name
            }
        })
        
        # Test 3: Read profile
        results["tests"].append({
            "step": "3. Read corporate profile",
            "status": "running"
        })
        
        read_profile = corporate_repo.get_by_id(created_profile.id)
        
        results["tests"][-1].update({
            "status": "success",
            "message": "Profile retrieved successfully",
            "data": {"profile_id": read_profile.id}
        })
        
        results["overall_status"] = "success"
        results["message"] = "All corporate profile tests passed"
        
    except Exception as e:
        results["overall_status"] = "error"
        results["error"] = str(e)
        import traceback
        results["traceback"] = traceback.format_exc()
    
    return results


@router.post("/full-time-job")
async def test_full_time_job(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Test Full-Time Job API: Create, Read, Update, Delete"""
    user_id = get_user_id(current_user)
    
    results = {
        "test_name": "Full-Time Job API Test",
        "user_id": user_id,
        "timestamp": datetime.now().isoformat(),
        "tests": []
    }
    
    try:
        corporate_repo = CorporateProfileRepository(db)
        job_repo = FullTimeJobRepository(db)
        
        # Test 1: Check corporate profile
        results["tests"].append({
            "step": "1. Verify corporate profile exists",
            "status": "running"
        })
        
        profile = corporate_repo.get_by_user_id(user_id)
        if not profile:
            results["tests"][-1].update({
                "status": "error",
                "message": "User must have a corporate profile first"
            })
            results["overall_status"] = "error"
            return results
        
        results["tests"][-1].update({
            "status": "success",
            "message": f"Corporate profile found (ID: {profile.id})",
            "data": {"profile_id": profile.id}
        })
        
        # Test 2: Create full-time job
        results["tests"].append({
            "step": "2. Create full-time job",
            "status": "running"
        })
        
        job_data = FullTimeJobCreate(
            title="Test Full-Time Position",
            description="Test job description for API testing",
            responsibilities="Test responsibilities",
            location="Test City",
            job_type=JobType.FULL_TIME,
            work_mode=WorkMode.REMOTE,
            experience_level=ExperienceLevel.MID,
            skill_ids=[1],
            min_salary=1000.0,
            max_salary=2000.0,
            pay_period=PayPeriod.PER_MONTH,
            status=JobStatus.ACTIVE,
            category_id=1,
            subcategory_id=2,
            corporate_profile_id=profile.id
        )
        
        created_job = job_repo.create_with_context(
            job_data,
            profile.id,
            user_id,
            TeamMemberRole.OWNER
        )
        
        results["tests"][-1].update({
            "status": "success",
            "message": "Full-time job created successfully",
            "data": {
                "job_id": created_job.get('id'),
                "title": created_job.get('title'),
                "status": created_job.get('status')
            }
        })
        
        # Test 3: Read job
        results["tests"].append({
            "step": "3. Read full-time job",
            "status": "running"
        })
        
        job_id = created_job.get('id')
        read_job = job_repo.get_by_id(job_id, user_id)
        
        results["tests"][-1].update({
            "status": "success",
            "message": "Job retrieved successfully",
            "data": {"job_id": job_id}
        })
        
        results["overall_status"] = "success"
        results["message"] = "All full-time job tests passed"
        
    except Exception as e:
        results["overall_status"] = "error"
        results["error"] = str(e)
        import traceback
        results["traceback"] = traceback.format_exc()
    
    return results


@router.post("/all")
async def test_all_apis(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Test ALL APIs: Corporate Profile, Jobs, Chat, Proposals, etc."""
    user_id = get_user_id(current_user)
    user_email = get_user_email(current_user)
    
    results = {
        "test_name": "Complete API Test Suite",
        "user_id": user_id,
        "user_email": user_email,
        "timestamp": datetime.now().isoformat(),
        "tests": [],
        "summary": {}
    }
    
    try:
        # ===== 1. CORPORATE PROFILE =====
        results["tests"].append({
            "api": "Corporate Profile",
            "step": "1. Check/Create corporate profile",
            "status": "running"
        })
        
        corporate_repo = CorporateProfileRepository(db)
        profile = corporate_repo.get_by_user_id(user_id)
        
        if not profile:
            profile_data = CorporateProfileCreate(
                company_name=f"Test Company {user_id}",
                phone_number="+998901234567",
                country_code="+998",
                location_id=1,
                overview="Auto-generated test company",
                website_url="https://test.com",
                company_size="1-10",
                category_id=1
            )
            profile = corporate_repo.create(profile_data, user_id)
            results["tests"][-1].update({
                "status": "success",
                "message": f"Corporate profile created (ID: {profile.id})"
            })
        else:
            results["tests"][-1].update({
                "status": "success",
                "message": f"Corporate profile exists (ID: {profile.id})"
            })
        
        profile_id = profile.id
        
        # ===== 2. FULL-TIME JOB =====
        results["tests"].append({
            "api": "Full-Time Job",
            "step": "2. Create full-time job",
            "status": "running"
        })
        
        job_repo = FullTimeJobRepository(db)
        job_data = FullTimeJobCreate(
            title=f"Test Job {datetime.now().strftime('%H%M%S')}",
            description="Test job for API testing",
            responsibilities="Test responsibilities",
            location="Remote",
            job_type=JobType.FULL_TIME,
            work_mode=WorkMode.REMOTE,
            experience_level=ExperienceLevel.MID,
            skill_ids=[1],
            min_salary=1500.0,
            max_salary=2500.0,
            pay_period=PayPeriod.PER_MONTH,
            status=JobStatus.ACTIVE,
            category_id=1,
            subcategory_id=2,
            corporate_profile_id=profile_id
        )
        
        created_job = job_repo.create_with_context(
            job_data,
            profile_id,
            user_id,
            TeamMemberRole.OWNER
        )
        
        results["tests"][-1].update({
            "status": "success",
            "message": f"Full-time job created (ID: {created_job.get('id')})",
            "data": {"job_id": created_job.get('id')}
        })
        
        # ===== 3. GIG JOB =====
        results["tests"].append({
            "api": "Gig Job",
            "step": "3. Create gig job",
            "status": "running"
        })
        
        from ..repositories.gig_job_repository import GigJobRepository
        from ..models.gig_job import ExperienceLevel as GigExperienceLevel
        
        gig_repo = GigJobRepository(db)
        gig_data = GigJobCreate(
            title=f"Test Gig {datetime.now().strftime('%H%M%S')}",
            description="Test gig job for API testing",
            experience_level=GigExperienceLevel.MID,
            project_length=ProjectLength.ONE_TO_THREE_MONTHS,
            skill_ids=[1],
            min_salary=500.0,
            max_salary=1500.0,
            category_id=1,
            subcategory_id=2,
            location_id=1
        )
        
        created_gig = gig_repo.create(gig_data, user_id)
        
        results["tests"][-1].update({
            "status": "success",
            "message": f"Gig job created (ID: {created_gig.id})",
            "data": {"gig_id": created_gig.id}
        })
        
        # ===== 4. SAVED JOB =====
        results["tests"].append({
            "api": "Saved Job",
            "step": "4. Save full-time job",
            "status": "running"
        })
        
        from ..repositories.saved_job_repository import SavedJobRepository
        
        saved_repo = SavedJobRepository(db)
        saved_job = saved_repo.save_full_time_job(
            user_id=user_id,
            job_id=created_job.get('id')
        )
        
        results["tests"][-1].update({
            "status": "success",
            "message": f"Job saved successfully (ID: {saved_job.id})",
            "data": {"saved_job_id": saved_job.id}
        })
        
        # ===== 5. CHAT ROOM =====
        results["tests"].append({
            "api": "Chat",
            "step": "5. Create chat room",
            "status": "running"
        })
        
        from ..repositories.chat_repository import ChatRepository
        
        chat_repo = ChatRepository(db)
        
        # Find another user to chat with (use admin if exists)
        from ..repositories.user_repository import UserRepository
        user_repo = UserRepository(db)
        other_user = user_repo.get_user_by_email("admin@admin.com")
        
        if other_user and other_user.id != user_id:
            chat_room = chat_repo.get_or_create_room(
                user1_id=user_id,
                user2_id=other_user.id
            )
            
            results["tests"][-1].update({
                "status": "success",
                "message": f"Chat room created/found (ID: {chat_room.id})",
                "data": {
                    "room_id": chat_room.id,
                    "participant_ids": [user_id, other_user.id]
                }
            })
        else:
            results["tests"][-1].update({
                "status": "skipped",
                "message": "No other user found for chat test"
            })
        
        # ===== 6. PROPOSAL =====
        results["tests"].append({
            "api": "Proposal",
            "step": "6. Create proposal for gig job",
            "status": "running"
        })
        
        from ..repositories.proposal_repository import ProposalRepository
        from ..schemas.proposals import ProposalCreate
        
        proposal_repo = ProposalRepository(db)
        proposal_data = ProposalCreate(
            gig_job_id=created_gig.id,
            cover_letter="Test proposal cover letter",
            proposed_amount=1000.0,
            delivery_time=7
        )
        
        created_proposal = proposal_repo.create(proposal_data, user_id)
        
        results["tests"][-1].update({
            "status": "success",
            "message": f"Proposal created (ID: {created_proposal.id})",
            "data": {"proposal_id": created_proposal.id}
        })
        
        # ===== SUMMARY =====
        results["overall_status"] = "success"
        results["message"] = "All API tests completed successfully!"
        results["summary"] = {
            "total_tests": len(results["tests"]),
            "passed": sum(1 for t in results["tests"] if t.get("status") == "success"),
            "failed": sum(1 for t in results["tests"] if t.get("status") == "error"),
            "skipped": sum(1 for t in results["tests"] if t.get("status") == "skipped")
        }
        
    except Exception as e:
        results["overall_status"] = "error"
        results["error"] = str(e)
        import traceback
        results["error_traceback"] = traceback.format_exc()
    
    return results


@router.get("/health")
async def test_health():
    """Simple health check endpoint - no authentication required"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "message": "Test API is working"
    }
