from flask import Blueprint, render_template, request, flash, jsonify, redirect, url_for, abort
from flask_login import login_required, current_user
from sqlalchemy import delete
from .models import Contact
from .models import Policy
from .models import user_policy
from . import db
import json


views = Blueprint('views', __name__)


@views.route('/', methods=['GET', 'POST'])
@login_required
def home():
    return render_template("home.html", user=current_user, chosen_policy=current_user.chosen_policies)

@views.route('/contact-us', methods=['GET', 'POST'])
@login_required
def contact_us():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')

        try:
            if not title:
                flash('Title is required.', category='error')
            else:
                new_inquery = Contact(title=title, description=description, user_id=current_user.id)
                db.session.add(new_inquery)
                db.session.commit()
                flash('Inquery created successfully!', category='success')
                return redirect(url_for('views.home'))
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred: {str(e)}', category='error')

    return render_template('contact-us.html', user=current_user)

@views.route('/delete-request/<int:contact_id>')
@login_required
def delete_inquery(contact_id):
    inquery = Contact.query.get(contact_id)
    if inquery:
        db.session.delete(inquery)
        db.session.commit()
        flash('Inquery deleted successfully!', category='success')
    else:
        flash('Inquery not found.', category='error')
    return redirect(url_for('views.home'))

@views.route('/choose-policy', methods=['GET', 'POST'])
@login_required
def choose_policy():
    policies = [
        {'id': 1, 'title': 'Basic Home Insurance', 'insurance_type': 'Home', 'description': 'Coverage for Your Home!', 'price': 1000.0},
        {'id': 2, 'title': 'Comprehensive Car Insurance', 'insurance_type': 'Car', 'description': 'Coverage for Your Car!', 'price': 800.0},
        {'id': 3, 'title': 'Health Plus Insurance', 'insurance_type': 'Health', 'description': 'Comprehensive Health Coverage!', 'price': 1200.0},
    ]
    
    if request.method == 'POST':
        chosen_policy_id = request.form.get('chosen_policy')
        chosen_policy = next((policy for policy in policies if policy['id'] == int(chosen_policy_id)), None)
        
        if chosen_policy:
            # Get the Policy instance from the database or create a new one
            policy_instance = Policy.query.get(chosen_policy['id'])
            if not policy_instance:
                policy_instance = Policy(**chosen_policy)
                db.session.add(policy_instance)
                db.session.commit()

            # Add the chosen policy to the user's chosen_policies relationship
            current_user.chosen_policies.append(policy_instance)
            db.session.commit()
            flash(f'You have chosen {chosen_policy["title"]} insurance!', category='success')

    return render_template('choose_policy.html', user=current_user, policies=policies)

@views.route('/delete-policy/<int:policy_id>', methods=['POST'])
@login_required
def delete_policy(policy_id):
    policy_to_delete = Policy.query.get(policy_id)

    if policy_to_delete:
        stmt = delete(user_policy).where(user_policy.c.user_id == current_user.id, user_policy.c.policy_id == policy_id)
        
        db.session.execute(stmt)
        db.session.commit()

        flash(f'The policy "{policy_to_delete.title}" has been removed.', category='success')
    else:
        flash('Policy not found.', category='error')

    return redirect(url_for('views.home'))
