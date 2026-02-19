
from extensions import db
from models import SupportTicket, SupportMessage
from datetime import datetime

class SupportService:
    """Service for handling support tickets and messages"""
    
    @staticmethod
    def create_ticket(user_id, subject, message, category='general', priority='normal'):
        """Create a new support ticket"""
        # Create ticket
        ticket = SupportTicket(
            user_id=user_id,
            subject=subject,
            category=category,
            priority=priority,
            status='open',
            user_unread_count=0,
            admin_unread_count=1  # Admin has 1 unread message
        )
        db.session.add(ticket)
        db.session.commit()
        
        # Create initial message
        msg = SupportMessage(
            ticket_id=ticket.id,
            sender_id=user_id,
            message=message,
            is_admin=False,
            read_by_user=True,
            read_by_admin=False
        )
        db.session.add(msg)
        db.session.commit()
        
        return ticket
    
    @staticmethod
    def add_message(ticket_id, sender_id, message, is_admin=False):
        """Add a message to an existing ticket"""
        ticket = SupportTicket.query.get(ticket_id)
        if not ticket:
            return None
            
        # Add message
        msg = SupportMessage(
            ticket_id=ticket.id,
            sender_id=sender_id,
            message=message,
            is_admin=is_admin,
            read_by_user=True, # Sender always reads their own message
            read_by_admin=True # Sender always reads their own message
        )
        
        # Override read status based on recipient
        if is_admin:
            # Admin sent it -> Admin read it (already True), User hasn't read it
            msg.read_by_user = False
            ticket.status = 'in_progress' # Admin replied
            ticket.user_unread_count += 1
            ticket.admin_unread_count = 0 # Admin read everything to reply (usually)
        else:
            # User sent it -> User read it (already True), Admin hasn't read it
            msg.read_by_admin = False
            ticket.status = 'open' # User replied, waiting for admin
            ticket.admin_unread_count += 1
            ticket.user_unread_count = 0 # User read everything to reply (usually)
            
        db.session.add(msg)
        ticket.updated_at = datetime.utcnow()
        db.session.commit()
        return msg

    @staticmethod
    def get_user_tickets(user_id):
        """Get all tickets for a user"""
        return SupportTicket.query.filter_by(user_id=user_id).order_by(SupportTicket.updated_at.desc()).all()
        
    @staticmethod
    def get_admin_tickets(status_filter=None):
        """Get all tickets for admin panel"""
        query = SupportTicket.query
        if status_filter and status_filter != 'all':
            query = query.filter_by(status=status_filter)
        return query.order_by(SupportTicket.updated_at.desc()).all()
