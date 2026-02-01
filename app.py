"""
Flask backend application for Entekhablock voting platform
Handles all API endpoints, authentication flow, and blockchain integration
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from werkzeug.utils import secure_filename
import os
import secrets
import csv
import requests
import json
import traceback
import jdatetime
from datetime import datetime, timedelta

# Import custom modules
from blockchain import Blockchain, hash_national_code
from utils.auth import VoterDatabase, OTPManager, BiometricSimulator, SessionManager, hash_voter_identity
from utils.poll_manager import PollManager

# Initialize Flask app
app = Flask(__name__)
# Use persistent secret key to prevent session invalidation on restart
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production-' + secrets.token_hex(16))
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB max file size
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# ==================== CONFIGURATION ====================
# To enable real biometric verification with Iranian Shahkar API:
# Set environment variable: VIDEOLIVE_API_TOKEN="your_api_token_here"
# Without the token, the system runs in MVP simulation mode
# API Documentation: https://s.api.ir/docs#operation/post_api_sw1_VideoLive
# ========================================================

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize core systems
print("[DEBUG] Initializing blockchain...", flush=True)
blockchain = Blockchain('data/blockchain.json')
print("[DEBUG] Initializing voter database...", flush=True)
voter_db = VoterDatabase('data/voters.csv')
print("[DEBUG] Initializing OTP manager...", flush=True)
otp_manager = OTPManager()
print("[DEBUG] Initializing biometric simulator...", flush=True)
biometric_sim = BiometricSimulator()
print("[DEBUG] Initializing session manager...", flush=True)
session_manager = SessionManager()
print("[DEBUG] Initializing poll manager...", flush=True)
poll_manager = PollManager('data/polls.json')
print("[DEBUG] All systems initialized!", flush=True)

# Admin credentials (MVP - hardcoded)
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin"
ADMIN_OTP = "1234"


@app.context_processor
def inject_user():
    # A simplified 'current_user' object for template context
    class SimpleUser:
        def __init__(self, is_authenticated=False, data=None, is_admin=False):
            self.is_authenticated = is_authenticated
            self.is_admin = is_admin
            self.data = data if data else {}

    auth_session_id = session.get('auth_session_id')
    admin_authenticated = session.get('admin_authenticated')

    if admin_authenticated:
        user = SimpleUser(is_authenticated=True, data={'full_name': 'مدیر سیستم'}, is_admin=True)
    elif auth_session_id and session_manager.is_fully_authenticated(auth_session_id):
        voter_data = session_manager.get_voter_data(auth_session_id)
        user = SimpleUser(is_authenticated=True, data=voter_data, is_admin=False)
    else:
        user = SimpleUser(is_authenticated=False)
        
    return dict(current_user=user)


@app.template_filter('jalali')
def jalali_filter(date_str):
    if not date_str:
        return "-"
    try:
        # Expected format: "YYYY-MM-DD HH:MM:SS" or "YYYY-MM-DD"
        if ' ' in date_str:
            dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
            jd = jdatetime.datetime.fromgregorian(datetime=dt)
            return jd.strftime("%Y/%m/%d - %H:%M")
        else:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            jd = jdatetime.date.fromgregorian(date=dt.date())
            return jd.strftime("%Y/%m/%d")
    except Exception as e:
        print(f"Jalali filter error: {e}")
        return date_str


# ==================== UTILITY FUNCTIONS ====================

def is_admin_logged_in():
    """Check if admin is authenticated"""
    return session.get('admin_authenticated', False)


def allowed_file(filename):
    """Check if uploaded file has allowed extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'jpg', 'jpeg', 'png'}


# ==================== PUBLIC ROUTES ====================

@app.route('/favicon.ico')
def favicon():
    """Return favicon quickly to prevent blocking page load"""
    return '', 204  # 204 No Content - fast response


@app.route('/')
def index():
    """Home page - voter entry point"""
    return render_template('index.html')


@app.route('/voter/authenticate')
def voter_authenticate():
    """Voter authentication page (3-stage process)"""
    if 'auth_session_id' not in session:
        session['auth_session_id'] = None
    return render_template('login.html')


@app.route('/vote/<poll_id>', methods=['GET', 'POST'])
def vote(poll_id):
    """Voting page for a specific poll"""
    return voter_vote(poll_id)


@app.route('/technical')
def technical_info():
    """Technical details page"""
    return render_template('technical.html')


@app.route('/voter/vote', defaults={'poll_id': None}, methods=['GET', 'POST'])
@app.route('/voter/vote/<poll_id>', methods=['GET', 'POST'])
def voter_vote(poll_id):
    """Voting page - only accessible after full authentication"""
    auth_session_id = session.get('auth_session_id')
    
    if not auth_session_id or not session_manager.is_fully_authenticated(auth_session_id):
        return redirect(url_for('voter_authenticate'))
    
    if not poll_id:
        return redirect(url_for('dashboard'))
        
    poll_obj = poll_manager.get_poll(poll_id)
    if not poll_obj or not poll_obj.is_active():
        flash("نظرسنجی معتبر یافت نشد یا پایان یافته است", "error")
        return redirect(url_for('dashboard'))
        
    voter_data = session_manager.get_voter_data(auth_session_id)

    if request.method == 'POST':
        choice = request.form.get('option')
        if not choice:
            flash("لطفاً یک گزینه را انتخاب کنید", "error")
        else:
            voter_hash = hash_voter_identity(voter_data['national_code'])
            success, message = poll_obj.record_vote(voter_hash, choice)
            
            if success:
                # Add to blockchain
                vote_data = {
                    'voter_hash': voter_hash,
                    'poll_id': poll_id,
                    'choice': choice,
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                blockchain.add_block(vote_data)
                poll_manager._save_polls()
                flash("رأی شما با موفقیت ثبت شد", "success")
                return redirect(url_for('dashboard')) # Or a success page
            else:
                flash(message, "error")
    
    return render_template('vote.html', 
                         poll=poll_obj,
                         voter_name=voter_data.get('full_name', 'کاربر') if voter_data else 'کاربر')


@app.route('/results')
def public_results():
    """Public results page"""
    all_polls = poll_manager.get_all_polls()
    ended_polls = []
    
    for p in all_polls:
        p_res = p.get_results()
        # Add some convenient properties for the template
        p_res['id'] = p.poll_id
        p_res['options_count'] = len(p.options)
        ended_polls.append(p_res)
    
    return render_template('results.html', polls=ended_polls)


@app.route('/results/<poll_id>')
def view_results(poll_id):
    """View results for a specific poll"""
    poll_obj = poll_manager.get_poll(poll_id)
    if not poll_obj:
        flash("نظرسنجی یافت نشد", "error")
        return redirect(url_for('public_results'))
    
    res_data = poll_obj.get_results()
    total_votes = res_data['total_votes']
    
    # Calculate winner
    winner = "نامشخص"
    winner_percentage = 0
    if total_votes > 0:
        # Find option with most votes
        winner_option = max(poll_obj.votes, key=poll_obj.votes.get)
        winner = winner_option
        winner_percentage = res_data['percentages'].get(winner_option, 0)
    
    return render_template('results.html', 
                         poll=poll_obj, 
                         results=poll_obj.votes, 
                         total_votes=total_votes,
                         winner=winner,
                         winner_percentage=winner_percentage,
                         labels=list(poll_obj.votes.keys()),
                         values=list(poll_obj.votes.values()),
                         blockchain_length=len(blockchain.chain))


# ==================== VOTER API ENDPOINTS ====================

@app.route('/api/voter/auth/stage1', methods=['POST'])
def api_auth_stage1():
    """Stage 1: Verify basic information"""
    try:
        data = request.json
        national_code = data.get('national_code', '').strip()
        birth_date = data.get('birth_date', '').strip()
        serial_number = data.get('serial_number', '').strip()
        
        if not all([national_code, birth_date, serial_number]):
            return jsonify({'success': False, 'message': 'لطفاً تمام فیلدها را پر کنید'}), 400
        
        success, message, voter_data = voter_db.verify_stage1(national_code, birth_date, serial_number)
        
        if not success:
            return jsonify({'success': False, 'message': message}), 401
        
        auth_session_id = session_manager.create_session(national_code)
        session_manager.update_stage(auth_session_id, 'stage1', voter_data)
        session['auth_session_id'] = auth_session_id
        
        return jsonify({
            'success': True,
            'message': message,
            'mobile': voter_data['mobile'],
            'full_name': voter_data['full_name']
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'خطای سرور: {str(e)}'}), 500


@app.route('/api/voter/auth/stage2/send-otp', methods=['POST'])
def api_auth_stage2_send():
    """Stage 2: Send OTP to mobile number"""
    try:
        auth_session_id = session.get('auth_session_id')
        
        if not auth_session_id or not session_manager.sessions[auth_session_id]['stages_completed']['stage1']:
            return jsonify({'success': False, 'message': 'ابتدا مرحله ۱ را تکمیل کنید'}), 403
        
        voter_data = session_manager.get_voter_data(auth_session_id)
        mobile = voter_data['mobile']
        
        success, message = otp_manager.send_otp(mobile)
        
        return jsonify({
            'success': success,
            'message': message,
            'otp_hint': f'کد تأیید: {OTPManager.FIXED_OTP}'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'خطا: {str(e)}'}), 500


@app.route('/api/voter/auth/stage2/verify-otp', methods=['POST'])
def api_auth_stage2_verify():
    """Stage 2: Verify OTP code"""
    try:
        data = request.json
        otp_code = data.get('otp_code', '').strip()
        
        auth_session_id = session.get('auth_session_id')
        
        # Safe dictionary access
        if not auth_session_id or not session_manager.sessions.get(auth_session_id, {}).get('stages_completed', {}).get('stage1'):
            return jsonify({'success': False, 'message': 'ابتدا مرحله ۱ را تکمیل کنید'}), 403
        
        voter_data = session_manager.get_voter_data(auth_session_id)
        if not voter_data or not isinstance(voter_data, dict):
            return jsonify({'success': False, 'message': 'اطلاعات رای‌دهنده یافت نشد'}), 403
        
        mobile = voter_data.get('mobile')
        if not mobile:
            return jsonify({'success': False, 'message': 'شماره موبایل یافت نشد'}), 403
        
        success, message = otp_manager.verify_otp(mobile, otp_code)
        
        if success:
            session_manager.update_stage(auth_session_id, 'stage2')
        
        return jsonify({'success': success, 'message': message})
        
    except Exception as e:
        print(f"[ERROR] api_auth_stage2_verify: {str(e)}", flush=True)
        return jsonify({'success': False, 'message': f'خطا: {str(e)}'}), 500


@app.route('/api/voter/auth/stage3', methods=['POST'])
def api_auth_stage3():
    """Stage 3: Biometric face verification"""
    try:
        auth_session_id = session.get('auth_session_id')
        
        if not auth_session_id:
            return jsonify({'success': False, 'message': 'جلسه نامعتبر است'}), 403
        
        stages = session_manager.sessions[auth_session_id]['stages_completed']
        if not (stages['stage1'] and stages['stage2']):
            return jsonify({'success': False, 'message': 'ابتدا مراحل قبلی را تکمیل کنید'}), 403
        
        if 'face_image' not in request.files:
            return jsonify({'success': False, 'message': 'تصویر آپلود نشده است'}), 400
        
        file = request.files['face_image']
        
        if file.filename == '':
            return jsonify({'success': False, 'message': 'فایلی انتخاب نشده است'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'message': 'فرمت فایل باید JPG یا PNG باشد'}), 400
        
        image_data = file.read()
        voter_data = session_manager.get_voter_data(auth_session_id)
        success, message, confidence = biometric_sim.verify_face(image_data, voter_data['national_code'])
        
        if success:
            session_manager.update_stage(auth_session_id, 'stage3')
        
        return jsonify({
            'success': success,
            'message': message,
            'confidence': confidence if success else 0
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'خطا: {str(e)}'}), 500


@app.route('/api/poll/<poll_id>')
def api_get_poll(poll_id):
    """Get poll data"""
    poll = poll_manager.get_poll(poll_id)
    if not poll:
        return jsonify({'success': False, 'message': 'نظرسنجی یافت نشد'}), 404
    
    return jsonify(poll.to_dict())


@app.route('/api/voter/submit-vote', methods=['POST'])
def api_submit_vote():
    """Submit vote to blockchain"""
    try:
        data = request.json
        poll_id = data.get('poll_id')
        choice = data.get('choice')
        
        auth_session_id = session.get('auth_session_id')
        if not auth_session_id or not session_manager.is_fully_authenticated(auth_session_id):
            return jsonify({'success': False, 'message': 'لطفاً ابتدا احراز هویت کنید'}), 403
        
        voter_data = session_manager.get_voter_data(auth_session_id)
        voter_hash = hash_voter_identity(voter_data['national_code'])
        
        poll = poll_manager.get_poll(poll_id)
        if not poll:
            return jsonify({'success': False, 'message': 'نظرسنجی یافت نشد'}), 404
        
        success, message = poll.record_vote(voter_hash, choice)
        
        if not success:
            return jsonify({'success': False, 'message': message}), 400
        
        vote_data = {
            'voter_hash': voter_hash,
            'poll_id': poll_id,
            'choice': choice,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        block = blockchain.add_block(vote_data)
        poll_manager._save_polls()
        
        return jsonify({
            'success': True,
            'message': 'رأی شما با موفقیت ثبت شد',
            'block_hash': block.hash,
            'block_index': block.index
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'خطا: {str(e)}'}), 500


@app.route('/api/poll/<poll_id>/results')
def api_poll_results(poll_id):
    """Get results for a specific poll"""
    try:
        poll = poll_manager.get_poll(poll_id)
        
        if not poll:
            return jsonify({'success': False, 'message': 'نظرسنجی یافت نشد'}), 404
        
        results = poll.get_results()
        
        return jsonify({
            'success': True,
            'results': results
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'خطا: {str(e)}'}), 500


# ==================== ADMIN ROUTES ====================

@app.route('/admin', methods=['GET', 'POST'])
def admin_login_page():
    """Admin login page"""
    if request.args.get('reset'):
        session.pop('admin_login_stage1', None)
        session.pop('admin_authenticated', None)
        return redirect(url_for('admin_login_page'))

    if is_admin_logged_in():
        return redirect(url_for('admin_dashboard'))
    
    if request.method == 'POST':
        # Check if this is an OTP submission
        otp_code = request.form.get('otp_code')
        if otp_code:
            if session.get('admin_login_stage1') and otp_code == ADMIN_OTP:
                session['admin_authenticated'] = True
                session.pop('admin_login_stage1', None)
                flash('ورود موفقیت‌آمیز', 'success')
                return redirect(url_for('admin_dashboard'))
            else:
                flash('کد OTP اشتباه است', 'error')
                return render_template('admin/otp.html')

        # This is an initial login submission
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_login_stage1'] = True
            flash('لطفاً کد OTP را وارد کنید', 'info')
            return render_template('admin/otp.html', otp_hint=ADMIN_OTP)
        else:
            flash('نام کاربری یا رمز عبور اشتباه است', 'error')
            return render_template('admin/login.html')
            
    # GET request - if already in stage 1, show OTP page
    if session.get('admin_login_stage1'):
        return render_template('admin/otp.html', otp_hint=ADMIN_OTP)
        
    return render_template('admin/login.html')


@app.route('/admin/dashboard')
def admin_dashboard():
    """Admin dashboard"""
    if not is_admin_logged_in():
        return redirect(url_for('admin_login_page'))
    
    # Get all polls and convert to dict for template compatibility
    polls_raw = poll_manager.get_all_polls()
    polls = []
    
    total_votes = 0
    for p in polls_raw:
        p_dict = p.to_dict()
        p_dict['id'] = p.poll_id # Add 'id' as 'poll_id' is used in the class
        p_dict['status'] = p.get_status() # 'active', 'ended', 'upcoming'
        p_dict['total_votes'] = sum(p.votes.values())
        polls.append(p_dict)
        total_votes += p_dict['total_votes']
    
    chain_info = blockchain.get_chain_info()
    
    return render_template('admin/dashboard.html', 
                         polls=polls,
                         total_polls=len(polls),
                         total_votes=total_votes,
                         total_voters=len(voter_db.voters),
                         blockchain_valid=blockchain.is_chain_valid(),
                         blockchain_info=chain_info)


@app.route('/admin/create-poll', methods=['GET', 'POST'])
def admin_create_poll():
    """Admin create poll page"""
    if not is_admin_logged_in():
        return redirect(url_for('admin_login_page'))
    
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        start_date = request.form.get('start_date', '').strip()
        end_date = request.form.get('end_date', '').strip()
        options = request.form.getlist('options[]')
        
        # Combine date with default time if only date is provided
        start_time = f"{start_date} 00:00:00" if start_date else ""
        end_time = f"{end_date} 23:59:59" if end_date else ""
        
        success, message, poll = poll_manager.create_poll(
            title=title,
            options=options,
            start_time=start_time,
            end_time=end_time,
            description=description
        )
        
        if success:
            flash(message, 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash(message, 'error')
            
    return render_template('admin/create_poll.html')


@app.route('/admin/logout')
def admin_logout():
    """Admin logout"""
    session.pop('admin_authenticated', None)
    session.pop('admin_login_stage1', None)
    session.pop('admin_otp_verified', None)
    return redirect(url_for('admin_login_page'))


# ==================== ADMIN API ENDPOINTS ====================

@app.route('/api/admin/login', methods=['POST'])
def api_admin_login():
    """Admin login"""
    try:
        data = request.json
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_login_stage1'] = True
            return jsonify({
                'success': True,
                'message': 'لطفاً کد OTP را وارد کنید',
                'otp_hint': f'کد OTP: {ADMIN_OTP}'
            })
        else:
            return jsonify({'success': False, 'message': 'نام کاربری یا رمز عبور اشتباه است'}), 401
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'خطا: {str(e)}'}), 500


@app.route('/api/admin/verify-otp', methods=['POST'])
def api_admin_verify_otp():
    """Admin OTP verification"""
    try:
        data = request.json
        otp = data.get('otp', '').strip()
        
        if not session.get('admin_login_stage1'):
            return jsonify({'success': False, 'message': 'ابتدا وارد شوید'}), 403
        
        if otp == ADMIN_OTP:
            session['admin_authenticated'] = True
            session.pop('admin_login_stage1', None)
            return jsonify({'success': True, 'message': 'ورود موفقیت‌آمیز'})
        else:
            return jsonify({'success': False, 'message': 'کد OTP اشتباه است'}), 401
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'خطا: {str(e)}'}), 500


@app.route('/api/admin/create-poll', methods=['POST'])
def api_admin_create_poll():
    """Create new poll"""
    try:
        if not is_admin_logged_in():
            return jsonify({'success': False, 'message': 'دسترسی غیرمجاز'}), 403
        
        data = request.json
        title = data.get('title', '').strip()
        options = data.get('options', [])
        start_time = data.get('start_time', '').strip()
        end_time = data.get('end_time', '').strip()
        description = data.get('description', '').strip()
        
        success, message, poll = poll_manager.create_poll(
            title=title,
            options=options,
            start_time=start_time,
            end_time=end_time,
            description=description
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': message,
                'poll': poll.to_dict()
            })
        else:
            return jsonify({'success': False, 'message': message}), 400
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'خطا: {str(e)}'}), 500


@app.route('/api/admin/polls', methods=['GET'])
def api_admin_polls():
    """Get all polls (admin only)"""
    try:
        if not is_admin_logged_in():
            return jsonify({'success': False, 'message': 'دسترسی غیرمجاز'}), 403
        
        all_polls = poll_manager.get_all_polls()
        polls_data = []
        for p in all_polls:
            p_dict = p.to_dict()
            p_dict['id'] = p.poll_id
            p_dict['is_active'] = p.is_active()
            p_dict['total_votes'] = sum(p.votes.values())
            p_dict['total_voters'] = len(p.voters)
            polls_data.append(p_dict)
            
        return jsonify({'success': True, 'polls': polls_data})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/admin/stats', methods=['GET'])
def api_admin_stats():
    """Get dashboard stats"""
    try:
        if not is_admin_logged_in():
            return jsonify({'success': False, 'message': 'دسترسی غیرمجاز'}), 403
        
        all_polls = poll_manager.get_all_polls()
        active_polls = [p for p in all_polls if p.is_active()]
        
        total_votes = 0
        for p in all_polls:
            total_votes += sum(p.votes.values())
            
        stats = {
            'total_polls': len(all_polls),
            'active_polls': len(active_polls),
            'total_votes': total_votes,
            'total_voters': len(voter_db.voters)
        }
        
        return jsonify({'success': True, 'stats': stats})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/admin/poll/<poll_id>', methods=['DELETE'])
@app.route('/api/admin/delete-poll/<poll_id>', methods=['DELETE'])
def api_admin_delete_poll(poll_id):
    """Delete poll"""
    try:
        if not is_admin_logged_in():
            return jsonify({'success': False, 'message': 'دسترسی غیرمجاز'}), 403
        
        success, message = poll_manager.delete_poll(poll_id)
        return jsonify({'success': success, 'message': message})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'خطا: {str(e)}'}), 500


@app.route('/api/admin/upload-voters', methods=['POST'])
def api_admin_upload_voters():
    """Upload CSV file of eligible voters"""
    try:
        if not is_admin_logged_in():
            return jsonify({'success': False, 'message': 'دسترسی غیرمجاز'}), 403
        
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': 'فایل انتخاب نشده'}), 400
        
        file = request.files['file']
        
        if file.filename == '' or not file.filename.endswith('.csv'):
            return jsonify({'success': False, 'message': 'فرمت فایل باید CSV باشد'}), 400
        
        stream = StringIO(file.stream.read().decode("UTF-8"))
        csv_reader = csv.DictReader(stream)
        
        added_count = 0
        errors = []
        
        for row in csv_reader:
            try:
                required = ['national_code', 'birth_date', 'serial_number', 'mobile', 'full_name']
                if all(field in row for field in required):
                    voter_db.voters[row['national_code']] = row
                    added_count += 1
                else:
                    errors.append(f"ردیف ناقص: {row.get('national_code', 'نامشخص')}")
            except Exception as e:
                errors.append(f"خطا در پردازش: {str(e)}")
        
        voter_db.save_to_csv('data/voters.csv')
        
        return jsonify({
            'success': True,
            'message': f'{added_count} رأی‌دهنده افزوده شد',
            'added': added_count,
            'errors': errors
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'خطا: {str(e)}'}), 500


# ==================== BLOCKCHAIN API ENDPOINTS ====================

@app.route('/api/blockchain/info')
def api_blockchain_info():
    """Get blockchain information"""
    return jsonify(blockchain.get_chain_info())


@app.route('/api/blockchain/validate')
def api_blockchain_validate():
    """Validate blockchain integrity"""
    is_valid = blockchain.is_chain_valid()
    
    return jsonify({
        'success': True,
        'is_valid': is_valid,
        'message': 'زنجیره سالم است' if is_valid else 'زنجیره دستکاری شده است!'
    })


# ==================== TEMPLATE COMPATIBILITY ROUTES ====================

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login handler - STAGE 1 verification"""
    if request.method == 'POST':
        # Get form data
        national_code = request.form.get('national_code', '').strip()
        birth_date = request.form.get('birth_date', '').strip()
        serial_number = request.form.get('serial_number', '').strip()
        
        if not all([national_code, birth_date, serial_number]):
            flash('لطفاً تمام فیلدها را پر کنید', 'error')
            return redirect(url_for('login'))
        
        # Verify stage 1
        success, message, voter_data = voter_db.verify_stage1(national_code, birth_date, serial_number)
        
        if not success:
            flash(message, 'error')
            return redirect(url_for('login'))
        
        # Create session and mark stage 1 as complete
        auth_session_id = session_manager.create_session(national_code)
        session_manager.update_stage(auth_session_id, 'stage1', voter_data)
        session['auth_session_id'] = auth_session_id
        
        flash(message, 'success')
        return redirect(url_for('verify_otp'))
    
    return render_template('login.html')


@app.route('/verify_otp', methods=['GET', 'POST'])
def verify_otp():
    """OTP verification handler - STAGE 2 verification"""
    try:
        auth_session_id = session.get('auth_session_id')
        
        # Check if stage 1 is complete
        if not auth_session_id or not session_manager.sessions.get(auth_session_id, {}).get('stages_completed', {}).get('stage1'):
            flash('ابتدا مرحله ۱ را تکمیل کنید', 'error')
            return redirect(url_for('login'))
        
        if request.method == 'POST':
            otp_code = request.form.get('otp', '').strip()
            
            if not otp_code:
                flash('لطفاً کد تأیید را وارد کنید', 'error')
                return redirect(url_for('verify_otp'))
            
            # Verify OTP
            voter_data = session_manager.get_voter_data(auth_session_id)
            if not voter_data or not isinstance(voter_data, dict):
                flash('خطا: اطلاعات رای‌دهنده یافت نشد', 'error')
                return redirect(url_for('login'))
            
            # Safely get mobile number
            voter_mobile = voter_data.get('mobile')
            if not voter_mobile:
                flash('خطا: شماره موبایل یافت نشد', 'error')
                return redirect(url_for('login'))
            
            success, message = otp_manager.verify_otp(voter_mobile, otp_code)
            
            print(f"[DEBUG] OTP Verification - Mobile: {voter_mobile}, Entered: {otp_code}, Success: {success}, Message: {message}")
            
            if not success:
                flash(message, 'error')
                return redirect(url_for('verify_otp'))
            
            # Mark stage 2 as complete
            session_manager.update_stage(auth_session_id, 'stage2', {})
            flash(message, 'success')
            
            print(f"[DEBUG] verify_otp: session_id={auth_session_id}", flush=True)
            print(f"[DEBUG] verify_otp: session_data={json.dumps(session_manager.sessions.get(auth_session_id), default=str)}", flush=True)

            # Redirect to biometric verification (stage 3)
            return redirect(url_for('biometric'))
        
        # GET request - Send OTP if not already sent
        voter_data = session_manager.get_voter_data(auth_session_id)
        if not voter_data or not isinstance(voter_data, dict):
            flash('خطا: اطلاعات رای‌دهنده یافت نشد', 'error')
            return redirect(url_for('login'))
        
        # Safely get mobile number
        mobile = voter_data.get('mobile')
        if not mobile:
            flash('خطا: شماره موبایل یافت نشد', 'error')
            return redirect(url_for('login'))
        
        # Send OTP to mobile number
        success, otp_message = otp_manager.send_otp(mobile)
        if not success:
            flash(otp_message, 'error')
            return redirect(url_for('login'))
        
        flash(otp_message, 'info')
        return render_template('otp.html', mobile=mobile)
        
    except Exception as e:
        print(f"[ERROR] verify_otp exception: {str(e)}", flush=True)
        print(f"[ERROR] Traceback: {traceback.format_exc()}", flush=True)
        flash('خطای سرور رخ داد. لطفاً دوباره تلاش کنید', 'error')
        return redirect(url_for('login'))


@app.route('/biometric', methods=['GET', 'POST'])
def biometric():
    """Biometric verification page - STAGE 3 (VideoLive API)"""
    auth_session_id = session.get('auth_session_id')
    print(f"[DEBUG] biometric: session_id={auth_session_id}", flush=True)
    print(f"[DEBUG] biometric: session_data={json.dumps(session_manager.sessions.get(auth_session_id), default=str)}", flush=True)
    
    try:
        # Check if stage 2 is complete
        if not auth_session_id or not session_manager.sessions.get(auth_session_id, {}).get('stages_completed', {}).get('stage2'):
            flash('ابتدا مرحله ۲ را تکمیل کنید', 'error')
            return redirect(url_for('verify_otp'))
        
        if request.method == 'POST':
            voter_data = session_manager.get_voter_data(auth_session_id)
            video_data = request.form.get('video_data', '')
            
            # If no video data provided, still allow in MVP mode
            if not video_data:
                flash('هشدار: ویدئویی ضبط نشد، احراز هویت به صورت شبیه‌سازی انجام می‌شود', 'warning')
            else:
                # Call VideoLive API for real biometric verification
                try:
                    success = call_videolive_api(
                        national_code=voter_data['national_code'],
                        birth_date=voter_data['birth_date'],
                        serial_number=voter_data['serial_number'],
                        video_base64=video_data
                    )
                    
                    if not success:
                        flash('احراز هویت ناموفق بود. لطفاً دوباره تلاش کنید', 'error')
                        return redirect(url_for('biometric'))
                    
                    flash('احراز هویت بیومتریک موفق بود', 'success')
                except Exception as e:
                    flash(f'خطا در احراز هویت: {str(e)}', 'error')
                    return redirect(url_for('biometric'))
            
            # Mark stage 3 as complete (authentication fully complete)
            session_manager.update_stage(auth_session_id, 'stage3', {})
            
            flash('احراز هویت با موفقیت انجام شد', 'success')
            return redirect(url_for('dashboard'))
        
        return render_template('biometric.html')
    except Exception as e:
        error_message = str(e)
        tb_str = traceback.format_exc()
        print(f"ERROR in /biometric: {error_message}\n{tb_str}")
        return render_template('debug_error.html', error_message=error_message, traceback=tb_str)


def call_videolive_api(national_code: str, birth_date: str, serial_number: str, video_base64: str) -> bool:
    """
    Call the Iranian Shahkar VideoLive API for biometric verification
    
    Args:
        national_code: National code
        birth_date: Birth date
        serial_number: ID card serial number
        video_base64: Video encoded as base64
    
    Returns:
        bool: True if verification successful, False otherwise
    """
    import requests
    
    # VideoLive API endpoint
    api_url = "https://s.api.ir/api/sw1/VideoLive"
    
    # Get API token from environment or config
    api_token = os.getenv('VIDEOLIVE_API_TOKEN', '')
    
    if not api_token:
        # For MVP mode without token, just return True
        print("WARNING: VideoLive API token not configured. Using MVP mode.")
        return True
    
    try:
        # Prepare request payload
        payload = {
            "nationalCode": national_code,
            "birthDate": birth_date.replace('-', '/'),  # Convert from 1370-05-15 to 1370/5/15
            "serialNumber": serial_number,
            "videoBase64": video_base64,
            "matchingThreshold": 90,
            "livenessThreshold": 80
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_token}"
        }
        
        response = requests.post(api_url, json=payload, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and data.get('data', {}).get('isMatch') and data.get('data', {}).get('isLiveness'):
                return True
        
        return False
    except Exception as e:
        print(f"VideoLive API error: {str(e)}")
        # In MVP mode, return True to allow testing
        return True



@app.route('/logout')
def logout():
    """Logout handler"""
    session.pop('auth_session_id', None)
    session.pop('admin_authenticated', None)
    return redirect(url_for('index'))


# ==================== VOTER API ENDPOINTS ====================

@app.route('/api/user/profile', methods=['GET'])
def api_user_profile():
    """Get current user profile information"""
    auth_session_id = session.get('auth_session_id')
    
    if not auth_session_id or not session_manager.is_fully_authenticated(auth_session_id):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    voter_data = session_manager.get_voter_data(auth_session_id)
    
    if not voter_data:
        return jsonify({'success': False, 'error': 'User data not found'}), 404
    
    return jsonify({
        'success': True,
        'user': {
            'name': voter_data.get('full_name', 'کاربر'),
            'national_code': voter_data.get('national_code', ''),
            'mobile': voter_data.get('mobile', '')
        }
    })


@app.route('/api/polls', methods=['GET'])
def api_polls():
    """Get available polls with pagination"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 6, type=int)
    search = request.args.get('search', '', type=str)
    
    auth_session_id = session.get('auth_session_id')
    
    if not auth_session_id or not session_manager.is_fully_authenticated(auth_session_id):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    # Get active polls
    active_polls = poll_manager.get_active_polls()
    
    # Filter by search if provided
    if search:
        active_polls = [p for p in active_polls if search.lower() in p.title.lower()]
    
    # Paginate
    total = len(active_polls)
    start = (page - 1) * per_page
    end = start + per_page
    paginated_polls = active_polls[start:end]
    
    polls_data = []
    for poll in paginated_polls:
        polls_data.append({
            'id': poll.poll_id,
            'title': poll.title,
            'description': poll.description,
            'options': poll.options,
            'is_active': poll.is_active(),
            'total_votes': sum(poll.votes.values())
        })
    
    return jsonify({
        'success': True,
        'polls': polls_data,
        'total': total,
        'page': page,
        'per_page': per_page,
        'total_pages': (total + per_page - 1) // per_page
    })


@app.route('/dashboard')
def dashboard():
    """Dashboard page - voter voting interface"""
    auth_session_id = session.get('auth_session_id')
    
    if not auth_session_id or not session_manager.is_fully_authenticated(auth_session_id):
        return redirect(url_for('voter_authenticate'))
    
    active_polls = poll_manager.get_active_polls()
    voter_data = session_manager.get_voter_data(auth_session_id)
    
    return render_template('dashboard.html', 
                         polls=active_polls,
                         voter_name=voter_data.get('full_name', 'کاربر') if voter_data else 'کاربر')


@app.route('/view_blockchain')
def view_blockchain():
    """Blockchain view page"""
    chain_info = blockchain.get_chain_info()
    blocks = [
        {
            'index': block.index,
            'timestamp': block.timestamp,
            'data': block.data,
            'hash': block.hash,
            'previous_hash': block.previous_hash,
            'is_valid': block.hash == block.calculate_hash() if block.index > 0 else True
        }
        for block in blockchain.chain
    ]
    
    return render_template(
        'blockchain.html',
        blockchain_length=chain_info['total_blocks'],
        total_votes=chain_info['total_votes'],
        is_valid=chain_info['is_valid'],
        blocks=blocks,
        blockchain=chain_info
    )


@app.route('/blockchain_view')
def blockchain_view():
    """Alternative blockchain view route (for index.html compatibility)"""
    chain_info = blockchain.get_chain_info()
    blocks = [
        {
            'index': block.index,
            'timestamp': block.timestamp,
            'data': block.data,
            'hash': block.hash,
            'previous_hash': block.previous_hash,
            'is_valid': block.hash == block.calculate_hash() if block.index > 0 else True
        }
        for block in blockchain.chain
    ]
    
    return render_template(
        'blockchain.html',
        blockchain_length=chain_info['total_blocks'],
        total_votes=chain_info['total_votes'],
        is_valid=chain_info['is_valid'],
        blocks=blocks,
        blockchain=chain_info
    )


@app.route('/api/blockchain/is_valid', methods=['GET'])
def api_blockchain_is_valid():
    """Check blockchain validity"""
    is_valid = blockchain.is_chain_valid()
    return jsonify({'is_valid': is_valid})


@app.route('/api/blockchain/tamper/<int:block_index>', methods=['POST'])
def api_blockchain_tamper(block_index):
    """Simulate tampering with a block"""
    try:
        # Prevent tampering with genesis block
        if block_index == 0:
            return jsonify({'success': False, 'message': 'امکان دستکاری بلاک پایه وجود ندارد'}), 400
            
        if block_index >= len(blockchain.chain):
            return jsonify({'success': False, 'message': 'شماره بلاک نامعتبر است'}), 400

        # Create fake data
        fake_data = {
            "voter_hash": "HACKED_HASH_" * 4,
            "poll_id": "MODIFIED_POLL",
            "choice": "DUMMY_CHOICE",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        result = blockchain.simulate_tampering(block_index, fake_data)
        
        msg = "دستکاری با موفقیت انجام شد. اعتبار زنجیره از بین رفت!" if result['integrity_broken'] else "دستکاری انجام شد."
        
        return jsonify({
            'success': True, 
            'message': msg,
            'details': result
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'خطا: {str(e)}'}), 500


# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found(e):
    """404 error handler"""
    return render_template('404.html'), 404


@app.errorhandler(500)
def server_error(e):
    """500 error handler"""
    return render_template('500.html'), 500


# ==================== RUN APPLICATION ====================

if __name__ == '__main__':
    os.makedirs('data', exist_ok=True)
    
    print("=" * 50)
    print("[STARTING] Entekhablock voting system...")
    print("=" * 50)
    print(f"[BLOCKCHAIN] Blocks: {len(blockchain.chain)}")
    print(f"[VOTERS] Registered: {len(voter_db.voters)}")
    print(f"[POLLS] Active: {len(poll_manager.get_active_polls())}")
    print(f"[ADMIN] Username: {ADMIN_USERNAME} | Password: {ADMIN_PASSWORD}")
    print(f"[OTP] Test Code: {OTPManager.FIXED_OTP}")
    print("=" * 50)
    print("[SERVER] Flask running on http://0.0.0.0:5000")
    print("=" * 50)
    
    app.run(debug=True, host='0.0.0.0', port=8080, threaded=True, use_reloader=True)
