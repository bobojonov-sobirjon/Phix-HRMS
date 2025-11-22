from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc
from typing import List, Optional
from app.models.notification import Notification, NotificationType
from app.models.user import User
from app.models.proposal import Proposal
from app.models.gig_job import GigJob
from app.models.full_time_job import FullTimeJob
from app.pagination import PaginationParams


class NotificationRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        type: NotificationType,
        title: str,
        body: str,
        recipient_user_id: int,
        proposal_id: Optional[int] = None,
        job_id: Optional[int] = None,
        job_type: Optional[str] = None,
        applicant_id: Optional[int] = None
    ) -> Notification:
        """Create a new notification"""
        notification = Notification(
            type=type,
            title=title,
            body=body,
            recipient_user_id=recipient_user_id,
            proposal_id=proposal_id,
            job_id=job_id,
            job_type=job_type,
            applicant_id=applicant_id,
            is_read=False
        )
        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)
        return notification

    def get_by_id(self, notification_id: int) -> Optional[Notification]:
        """Get notification by ID"""
        return self.db.query(Notification).options(
            joinedload(Notification.recipient),
            joinedload(Notification.proposal),
            joinedload(Notification.applicant)
        ).filter(Notification.id == notification_id).first()

    def get_user_notifications(
        self,
        user_id: int,
        notification_type: Optional[NotificationType] = None,
        is_read: Optional[bool] = None,
        pagination: Optional[PaginationParams] = None
    ) -> tuple[List[Notification], int]:
        """Get user notifications with optional filtering"""
        query = self.db.query(Notification).options(
            joinedload(Notification.proposal).joinedload(Proposal.user).joinedload(User.location),
            joinedload(Notification.proposal).joinedload(Proposal.user).joinedload(User.main_category),
            joinedload(Notification.proposal).joinedload(Proposal.user).joinedload(User.sub_category),
            joinedload(Notification.proposal).joinedload(Proposal.user).joinedload(User.skills),
            joinedload(Notification.proposal).joinedload(Proposal.attachments),
            joinedload(Notification.proposal).joinedload(Proposal.gig_job).joinedload(GigJob.category),
            joinedload(Notification.proposal).joinedload(Proposal.gig_job).joinedload(GigJob.subcategory),
            joinedload(Notification.proposal).joinedload(Proposal.gig_job).joinedload(GigJob.location),
            joinedload(Notification.proposal).joinedload(Proposal.gig_job).joinedload(GigJob.skills),
            joinedload(Notification.proposal).joinedload(Proposal.full_time_job).joinedload(FullTimeJob.category),
            joinedload(Notification.proposal).joinedload(Proposal.full_time_job).joinedload(FullTimeJob.subcategory),
            joinedload(Notification.proposal).joinedload(Proposal.full_time_job).joinedload(FullTimeJob.skills),
            joinedload(Notification.applicant),
            joinedload(Notification.recipient).joinedload(User.location),
            joinedload(Notification.recipient).joinedload(User.main_category),
            joinedload(Notification.recipient).joinedload(User.sub_category),
            joinedload(Notification.recipient).joinedload(User.skills)
        ).filter(Notification.recipient_user_id == user_id)

        # Filter by type
        if notification_type:
            query = query.filter(Notification.type == notification_type)

        # Filter by read status
        if is_read is not None:
            query = query.filter(Notification.is_read == is_read)

        # Get total count
        total = query.count()

        # Apply pagination
        if pagination:
            query = query.order_by(desc(Notification.created_at)).offset(pagination.offset).limit(pagination.limit)
        else:
            query = query.order_by(desc(Notification.created_at))

        notifications = query.all()
        return notifications, total

    def get_applications(
        self,
        user_id: int,
        pagination: PaginationParams
    ) -> tuple[List[Notification], int]:
        """Get application notifications (when someone applies to user's jobs)"""
        return self.get_user_notifications(
            user_id=user_id,
            notification_type=NotificationType.APPLICATION,
            is_read=False,  # Only return unread notifications
            pagination=pagination
        )

    def get_my_proposals(
        self,
        user_id: int,
        pagination: PaginationParams
    ) -> tuple[List[Notification], int]:
        """Get proposal viewed notifications (when user's proposals are viewed)"""
        return self.get_user_notifications(
            user_id=user_id,
            notification_type=NotificationType.PROPOSAL_VIEWED,
            is_read=False,  # Only return unread notifications
            pagination=pagination
        )

    def mark_as_read(self, notification_id: int, user_id: int) -> bool:
        """Mark notification as read"""
        notification = self.db.query(Notification).filter(
            and_(
                Notification.id == notification_id,
                Notification.recipient_user_id == user_id
            )
        ).first()

        if not notification:
            return False

        notification.is_read = True
        self.db.commit()
        return True

    def mark_all_as_read(self, user_id: int, notification_type: Optional[NotificationType] = None) -> int:
        """Mark all notifications as read for a user"""
        query = self.db.query(Notification).filter(
            and_(
                Notification.recipient_user_id == user_id,
                Notification.is_read == False
            )
        )

        if notification_type:
            query = query.filter(Notification.type == notification_type)

        count = query.update({"is_read": True})
        self.db.commit()
        return count

    def get_unread_count(self, user_id: int, notification_type: Optional[NotificationType] = None) -> int:
        """Get count of unread notifications"""
        query = self.db.query(Notification).filter(
            and_(
                Notification.recipient_user_id == user_id,
                Notification.is_read == False
            )
        )

        if notification_type:
            query = query.filter(Notification.type == notification_type)

        return query.count()

    def delete(self, notification_id: int, user_id: int) -> bool:
        """Delete a notification"""
        notification = self.db.query(Notification).filter(
            and_(
                Notification.id == notification_id,
                Notification.recipient_user_id == user_id
            )
        ).first()

        if not notification:
            return False

        self.db.delete(notification)
        self.db.commit()
        return True

