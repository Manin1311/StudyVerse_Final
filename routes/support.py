
from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from extensions import db
from models import SupportTicket, SupportMessage, User
from services.support import SupportService
from utils import admin_required
from datetime import datetime

support_bp = Blueprint('support', __name__)

@support_bp.route('/support')
@login_required
def index():
    tickets = SupportTicket.query.filter_by(user_id=current_user.id).order_by(SupportTicket.updated_at.desc()).all()
    return render_template('support.html', tickets=tickets)

@support_bp.route('/support/create', methods=['POST'])
@login_required
def create():
    subject = request.form.get('subject')
    message = request.form.get('message')
    
    if not subject or not message:
        flash('Subject and message are required', 'error')
        return redirect(url_for('support.index'))
        
    SupportService.create_ticket(current_user.id, subject, message)
    flash('Support ticket created successfully', 'success')
    return redirect(url_for('support.index'))

@support_bp.route('/support/<int:ticket_id>')
@login_required
def detail(ticket_id):
    ticket = SupportTicket.query.get_or_404(ticket_id)
    
    # Ensure user owns ticket or is admin
    if ticket.user_id != current_user.id and not current_user.is_admin:
        flash('Unauthorized', 'error')
        return redirect(url_for('support.index'))
        
    # Mark as read for user if ticket has admin reply
    if not current_user.is_admin and ticket.user_unread_count > 0:
        ticket.user_unread_count = 0
        
        # Also mark messages read
        unread_msgs = SupportMessage.query.filter_by(
            ticket_id=ticket.id, 
            read_by_user=False,
            is_admin=True # Messages from admin
        ).all()
        for msg in unread_msgs:
            msg.read_by_user = True
            
        db.session.commit()
        
    messages = SupportMessage.query.filter_by(ticket_id=ticket.id).order_by(SupportMessage.created_at.asc()).all()
    return render_template('support_ticket.html', ticket=ticket, messages=messages)

@support_bp.route('/support/<int:ticket_id>/reply', methods=['POST'])
@login_required
def reply(ticket_id):
    ticket = SupportTicket.query.get_or_404(ticket_id)
    
    if ticket.user_id != current_user.id and not current_user.is_admin:
        flash('Unauthorized', 'error')
        return redirect(url_for('support.index'))
        
    if ticket.status == 'closed':
        flash('This ticket is closed.', 'error')
        return redirect(url_for('support.detail', ticket_id=ticket_id))
        
    message = request.form.get('message')
    if not message:
        flash('Message cannot be empty', 'error')
        return redirect(url_for('support.detail', ticket_id=ticket_id))
        
    is_admin = current_user.is_admin
    SupportService.add_message(ticket_id, current_user.id, message, is_admin=is_admin)
    return redirect(url_for('support.detail', ticket_id=ticket_id))
