"""
BriteTalent - Job Description Generator
Flask backend API for generating polished job descriptions with Claude AI
"""

import os
import sys
import json
import re
import secrets
from datetime import datetime

import pytz

from flask import Flask, request, jsonify, redirect, session, url_for, Response
from flask_cors import CORS
from authlib.integrations.flask_client import OAuth
from werkzeug.middleware.proxy_fix import ProxyFix

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Add backend to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# Import AI client
from backend.integrations.claude_client import ClaudeClient

# Import config
from config.briteroles_config import (
    COMPANY_DESCRIPTION,
    STANDARD_BENEFITS,
    DEPARTMENTS,
    EXPERIENCE_LEVELS,
    BRITEROLES_SYSTEM_PROMPT,
    AI_PROMPTS,
    GCS_CONFIG,
)

CHICAGO_TZ = pytz.timezone('America/Chicago')


# ============================================================================
# FLASK APP SETUP
# ============================================================================

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

# Fix for running behind Cloud Run's proxy
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Session configuration for OAuth
flask_key = os.environ.get('FLASK_SECRET_KEY')
if flask_key:
    app.secret_key = flask_key
    print("[OK] Flask secret key loaded from environment")
else:
    app.secret_key = secrets.token_hex(32)
    print("[WARNING] Flask secret key auto-generated - sessions will not persist across restarts. Set FLASK_SECRET_KEY env var.")
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = 86400 * 7  # 7 days


# ============================================================================
# OAUTH SETUP
# ============================================================================

oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=os.environ.get('GOOGLE_CLIENT_ID'),
    client_secret=os.environ.get('GOOGLE_CLIENT_SECRET'),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

ALLOWED_DOMAIN = 'brite.co'


def get_current_user():
    """Get current authenticated user from session"""
    return session.get('user')


# ============================================================================
# INITIALIZE CLAUDE CLIENT
# ============================================================================

claude_client = None

try:
    claude_client = ClaudeClient()
    print("[OK] Claude initialized")
except Exception as e:
    print(f"[WARNING] Claude not available: {e}")


# ============================================================================
# INITIALIZE GOOGLE CLOUD STORAGE
# ============================================================================

GCS_BUCKET = GCS_CONFIG['bucket']
gcs_client = None

try:
    from google.cloud import storage as gcs_storage
    gcs_client = gcs_storage.Client()
    print("[OK] GCS initialized")
except Exception as e:
    print(f"[WARNING] GCS not available: {e}")


# ============================================================================
# HELPERS
# ============================================================================

def safe_print(text):
    """Safe print for Unicode characters (Windows compat)"""
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode('ascii', 'replace').decode('ascii'))


# ============================================================================
# OAUTH AUTHENTICATION ROUTES
# ============================================================================

@app.route('/auth/login')
def auth_login():
    """Redirect to Google OAuth"""
    if get_current_user():
        return redirect('/')
    redirect_uri = url_for('auth_callback', _external=True)
    return google.authorize_redirect(redirect_uri)


@app.route('/auth/callback')
def auth_callback():
    """Handle OAuth callback from Google"""
    try:
        token = google.authorize_access_token()
        user_info = token.get('userinfo')

        if not user_info:
            return 'Failed to get user info', 400

        email = user_info.get('email', '')

        if not email.endswith(f'@{ALLOWED_DOMAIN}'):
            return f'''
            <html>
            <head><title>Access Denied</title></head>
            <body style="font-family: sans-serif; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; background: #272D3F;">
                <div style="text-align: center; color: white; padding: 2rem;">
                    <h1 style="color: #FC883A;">Access Denied</h1>
                    <p>Only @{ALLOWED_DOMAIN} email addresses are allowed.</p>
                    <p style="color: #A9C1CB;">You tried to sign in with: {email}</p>
                    <a href="/auth/login" style="color: #31D7CA;">Try again with a different account</a>
                </div>
            </body>
            </html>
            ''', 403

        session.permanent = True
        session['user'] = {
            'email': email,
            'name': user_info.get('name', ''),
            'picture': user_info.get('picture', '')
        }

        return redirect('/')

    except Exception as e:
        print(f"[AUTH ERROR] OAuth callback failed: {e}")
        return f'Authentication failed: {str(e)}', 500


@app.route('/auth/logout')
def auth_logout():
    """Clear session and redirect to login"""
    session.pop('user', None)
    return redirect('/auth/login')


# ============================================================================
# ROUTES - STATIC / HEALTH
# ============================================================================

@app.route('/')
def serve_index():
    """Serve the main app with auth check"""

    # Local dev: skip OAuth when no GOOGLE_CLIENT_ID is configured
    if not os.environ.get('GOOGLE_CLIENT_ID'):
        with open('index.html', 'r', encoding='utf-8') as f:
            html = f.read()

        dev_user = {"email": "dev@brite.co", "name": "Local Dev", "picture": ""}
        user_script = f'''<script>
    window.AUTH_USER = {json.dumps(dev_user)};
    </script>
</head>'''
        html = html.replace('</head>', user_script, 1)
        return Response(html, mimetype='text/html')

    # Production: require OAuth
    user = get_current_user()
    if not user:
        return redirect('/auth/login')

    with open('index.html', 'r', encoding='utf-8') as f:
        html = f.read()

    user_script = f'''<script>
    window.AUTH_USER = {json.dumps(user)};
    </script>
</head>'''
    html = html.replace('</head>', user_script, 1)

    return Response(html, mimetype='text/html')


@app.route('/health')
def health_check():
    """Simple health check for Cloud Run / load balancers"""
    return jsonify({
        "status": "healthy",
        "app": "BriteTalent",
        "timestamp": datetime.now().isoformat()
    })


# ============================================================================
# API ROUTES
# ============================================================================

@app.route('/api/config')
def get_config():
    """Return form configuration data for the frontend"""
    return jsonify({
        "departments": DEPARTMENTS,
        "experience_levels": EXPERIENCE_LEVELS,
        "standard_benefits": STANDARD_BENEFITS,
        "company_description": COMPANY_DESCRIPTION,
    })


@app.route('/api/generate-jd', methods=['POST'])
def generate_jd():
    """Generate a full job description using Claude"""
    if not claude_client:
        return jsonify({"error": "Claude AI is not available. Check ANTHROPIC_API_KEY."}), 503

    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body is required"}), 400

    # Extract fields
    title = data.get('title', '').strip()
    department = data.get('department', '').strip()
    reports_to = data.get('reports_to', '').strip()
    location = data.get('location', '').strip()
    experience_level = data.get('experience_level', '').strip()
    is_remote = data.get('is_remote', False)
    is_hybrid = data.get('is_hybrid', False)
    notes = data.get('notes', '').strip()

    # Validate required fields
    if not title:
        return jsonify({"error": "Job title is required"}), 400

    # Build remote/hybrid line
    if is_remote:
        remote_line = "- Work Type: Fully Remote\n"
    elif is_hybrid:
        remote_line = "- Work Type: Hybrid (remote + in-office)\n"
    else:
        remote_line = ""

    # Format the prompt
    prompt = AI_PROMPTS['generate_jd'].format(
        title=title,
        department=department or "Not specified",
        reports_to=reports_to or "Not specified",
        location=location or "Not specified",
        experience_level=experience_level or "Not specified",
        remote_line=remote_line,
        notes=notes or "No additional notes provided.",
    )

    system_prompt = BRITEROLES_SYSTEM_PROMPT

    safe_print(f"[GENERATE JD] Title: {title} | Dept: {department} | Level: {experience_level}")

    try:
        result = claude_client.generate_content(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.6,
            max_tokens=1500,
        )

        safe_print(f"[GENERATE JD] Done - {result.get('tokens', 0)} tokens, {result.get('latency_ms', 0)}ms")

        return jsonify({
            "job_description": result['content'],
            "model": result.get('model', ''),
            "tokens": result.get('tokens', 0),
            "cost_estimate": result.get('cost_estimate', ''),
            "latency_ms": result.get('latency_ms', 0),
        })

    except Exception as e:
        safe_print(f"[ERROR] generate-jd failed: {e}")
        return jsonify({"error": f"AI generation failed: {str(e)}"}), 500


@app.route('/api/adapt-jd', methods=['POST'])
def adapt_jd():
    """Adapt an external job description to BriteCo's voice using Claude"""
    if not claude_client:
        return jsonify({"error": "Claude AI is not available. Check ANTHROPIC_API_KEY."}), 503

    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body is required"}), 400

    original_jd = data.get('original_jd', '').strip()
    title = data.get('title', '').strip()
    department = data.get('department', '').strip()
    reports_to = data.get('reports_to', '').strip()
    location = data.get('location', '').strip()
    experience_level = data.get('experience_level', '').strip()
    is_remote = data.get('is_remote', False)
    is_hybrid = data.get('is_hybrid', False)
    notes = data.get('notes', '').strip()

    if not original_jd:
        return jsonify({"error": "Original job description is required"}), 400
    if not title:
        return jsonify({"error": "Job title is required"}), 400

    if is_remote:
        remote_line = "- Work Type: Fully Remote\n"
    elif is_hybrid:
        remote_line = "- Work Type: Hybrid (remote + in-office)\n"
    else:
        remote_line = ""

    prompt = AI_PROMPTS['adapt_jd'].format(
        original_jd=original_jd,
        title=title,
        department=department or "Not specified",
        reports_to=reports_to or "Not specified",
        location=location or "Not specified",
        experience_level=experience_level or "Not specified",
        remote_line=remote_line,
        notes=notes or "No additional notes.",
    )

    system_prompt = BRITEROLES_SYSTEM_PROMPT

    safe_print(f"[ADAPT JD] Title: {title} | Original length: {len(original_jd)} chars")

    try:
        result = claude_client.generate_content(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.6,
            max_tokens=1500,
        )

        safe_print(f"[ADAPT JD] Done - {result.get('tokens', 0)} tokens, {result.get('latency_ms', 0)}ms")

        return jsonify({
            "job_description": result['content'],
            "model": result.get('model', ''),
            "tokens": result.get('tokens', 0),
            "cost_estimate": result.get('cost_estimate', ''),
            "latency_ms": result.get('latency_ms', 0),
        })

    except Exception as e:
        safe_print(f"[ERROR] adapt-jd failed: {e}")
        return jsonify({"error": f"AI adaptation failed: {str(e)}"}), 500


@app.route('/api/rewrite-section', methods=['POST'])
def rewrite_section():
    """Rewrite a JD section with a different tone using Claude"""
    if not claude_client:
        return jsonify({"error": "Claude AI is not available. Check ANTHROPIC_API_KEY."}), 503

    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body is required"}), 400

    content = data.get('content', '').strip()
    tone = data.get('tone', '').strip()

    if not content:
        return jsonify({"error": "Content is required"}), 400
    if not tone:
        return jsonify({"error": "Tone is required"}), 400

    # Format the prompt
    prompt = AI_PROMPTS['rewrite_section'].format(
        content=content,
        tone=tone,
    )

    system_prompt = BRITEROLES_SYSTEM_PROMPT

    safe_print(f"[REWRITE] Tone: {tone} | Content length: {len(content)} chars")

    try:
        result = claude_client.generate_content(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.6,
            max_tokens=1000,
        )

        safe_print(f"[REWRITE] Done - {result.get('tokens', 0)} tokens, {result.get('latency_ms', 0)}ms")

        return jsonify({
            "rewritten_content": result['content'],
            "model": result.get('model', ''),
            "tokens": result.get('tokens', 0),
            "cost_estimate": result.get('cost_estimate', ''),
            "latency_ms": result.get('latency_ms', 0),
        })

    except Exception as e:
        safe_print(f"[ERROR] rewrite-section failed: {e}")
        return jsonify({"error": f"AI rewrite failed: {str(e)}"}), 500


# ============================================================================
# DRAFT SAVE / LOAD ROUTES (GCS)
# ============================================================================

def _slugify(text):
    """Convert text to URL-safe slug"""
    slug = text.lower().strip()
    slug = re.sub(r'[^a-z0-9]+', '-', slug)
    return slug.strip('-')[:60]


@app.route('/api/save-draft', methods=['POST'])
def save_draft():
    """Save JD draft to GCS"""
    if not gcs_client:
        return jsonify({'success': False, 'error': 'GCS not available'}), 503
    try:
        data = request.json
        title = data.get('title', 'untitled')
        saved_by = data.get('savedBy', 'unknown').split('@')[0].replace('.', '-')
        blob_name = f"drafts/{_slugify(title)}-{saved_by}.json"

        draft = {
            'title': title,
            'currentStep': data.get('currentStep'),
            'roleData': data.get('roleData'),
            'experienceLevel': data.get('experienceLevel'),
            'step2Mode': data.get('step2Mode'),
            'generatedSections': data.get('generatedSections'),
            'compensation': data.get('compensation'),
            'selectedBenefits': data.get('selectedBenefits'),
            'lastSavedBy': data.get('savedBy', 'unknown'),
            'lastSavedAt': datetime.now(CHICAGO_TZ).isoformat(),
        }

        bucket = gcs_client.bucket(GCS_BUCKET)
        blob = bucket.blob(blob_name)
        blob.upload_from_string(json.dumps(draft), content_type='application/json')
        safe_print(f"[DRAFT] Saved {blob_name}")
        return jsonify({'success': True, 'file': blob_name})

    except Exception as e:
        safe_print(f"[DRAFT SAVE ERROR] {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/list-drafts', methods=['GET'])
def list_drafts():
    """List all saved drafts from GCS"""
    if not gcs_client:
        return jsonify({'success': True, 'drafts': []})
    try:
        bucket = gcs_client.bucket(GCS_BUCKET)
        blobs = bucket.list_blobs(prefix='drafts/')
        drafts = []
        for blob in blobs:
            if not blob.name.endswith('.json'):
                continue
            data = json.loads(blob.download_as_text())
            drafts.append({
                'title': data.get('title', 'Untitled'),
                'currentStep': data.get('currentStep'),
                'lastSavedBy': data.get('lastSavedBy'),
                'lastSavedAt': data.get('lastSavedAt'),
                'filename': blob.name,
            })
        drafts.sort(key=lambda d: d.get('lastSavedAt', ''), reverse=True)
        return jsonify({'success': True, 'drafts': drafts})
    except Exception as e:
        safe_print(f"[DRAFT LIST ERROR] {str(e)}")
        return jsonify({'success': True, 'drafts': []})


@app.route('/api/load-draft', methods=['GET'])
def load_draft():
    """Load a specific draft from GCS"""
    if not gcs_client:
        return jsonify({'success': False, 'error': 'GCS not available'}), 503
    try:
        filename = request.args.get('file')
        if not filename:
            return jsonify({'success': False, 'error': 'No file specified'}), 400
        bucket = gcs_client.bucket(GCS_BUCKET)
        blob = bucket.blob(filename)
        data = json.loads(blob.download_as_text())
        return jsonify({'success': True, 'draft': data})
    except Exception as e:
        safe_print(f"[DRAFT LOAD ERROR] {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/delete-draft', methods=['DELETE'])
def delete_draft():
    """Delete a draft from GCS"""
    if not gcs_client:
        return jsonify({'success': True})
    try:
        filename = request.json.get('file')
        if not filename:
            return jsonify({'success': False, 'error': 'No file specified'}), 400
        bucket = gcs_client.bucket(GCS_BUCKET)
        blob = bucket.blob(filename)
        if blob.exists():
            blob.delete()
        safe_print(f"[DRAFT] Deleted {filename}")
        return jsonify({'success': True})
    except Exception as e:
        safe_print(f"[DRAFT DELETE ERROR] {str(e)}")
        return jsonify({'success': True})


# ============================================================================
# SAVED ROLES ROUTES (GCS)
# ============================================================================

@app.route('/api/save-role', methods=['POST'])
def save_role():
    """Save completed role to GCS"""
    if not gcs_client:
        return jsonify({'success': False, 'error': 'GCS not available'}), 503
    try:
        data = request.json
        title = data.get('title', 'untitled')
        saved_by = data.get('savedBy', 'unknown').split('@')[0].replace('.', '-')
        blob_name = f"saved/{_slugify(title)}-{saved_by}.json"

        role = {
            'title': title,
            'roleData': data.get('roleData'),
            'experienceLevel': data.get('experienceLevel'),
            'generatedSections': data.get('generatedSections'),
            'compensation': data.get('compensation'),
            'selectedBenefits': data.get('selectedBenefits'),
            'lastSavedBy': data.get('savedBy', 'unknown'),
            'lastSavedAt': datetime.now(CHICAGO_TZ).isoformat(),
        }

        bucket = gcs_client.bucket(GCS_BUCKET)
        blob = bucket.blob(blob_name)
        blob.upload_from_string(json.dumps(role), content_type='application/json')
        safe_print(f"[ROLE] Saved {blob_name}")

        # Delete corresponding draft if it exists
        draft_name = f"drafts/{_slugify(title)}-{saved_by}.json"
        draft_blob = bucket.blob(draft_name)
        if draft_blob.exists():
            draft_blob.delete()
            safe_print(f"[ROLE] Cleaned up draft {draft_name}")

        return jsonify({'success': True, 'file': blob_name})

    except Exception as e:
        safe_print(f"[ROLE SAVE ERROR] {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/list-saved-roles', methods=['GET'])
def list_saved_roles():
    """List all saved roles from GCS"""
    if not gcs_client:
        return jsonify({'success': True, 'roles': []})
    try:
        bucket = gcs_client.bucket(GCS_BUCKET)
        blobs = bucket.list_blobs(prefix='saved/')
        roles = []
        for blob in blobs:
            if not blob.name.endswith('.json'):
                continue
            data = json.loads(blob.download_as_text())
            rd = data.get('roleData', {})
            roles.append({
                'title': data.get('title', 'Untitled'),
                'department': rd.get('department', ''),
                'lastSavedBy': data.get('lastSavedBy'),
                'lastSavedAt': data.get('lastSavedAt'),
                'filename': blob.name,
            })
        roles.sort(key=lambda d: d.get('lastSavedAt', ''), reverse=True)
        return jsonify({'success': True, 'roles': roles})
    except Exception as e:
        safe_print(f"[ROLE LIST ERROR] {str(e)}")
        return jsonify({'success': True, 'roles': []})


@app.route('/api/load-saved-role', methods=['GET'])
def load_saved_role():
    """Load a specific saved role from GCS"""
    if not gcs_client:
        return jsonify({'success': False, 'error': 'GCS not available'}), 503
    try:
        filename = request.args.get('file')
        if not filename:
            return jsonify({'success': False, 'error': 'No file specified'}), 400
        bucket = gcs_client.bucket(GCS_BUCKET)
        blob = bucket.blob(filename)
        if not blob.exists():
            return jsonify({'success': False, 'error': 'Not found'}), 404
        data = json.loads(blob.download_as_text())
        return jsonify({'success': True, 'role': data})
    except Exception as e:
        safe_print(f"[ROLE LOAD ERROR] {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/delete-saved-role', methods=['DELETE'])
def delete_saved_role():
    """Delete a saved role from GCS"""
    if not gcs_client:
        return jsonify({'success': True})
    try:
        filename = request.json.get('file')
        if not filename:
            return jsonify({'success': False, 'error': 'No file specified'}), 400
        bucket = gcs_client.bucket(GCS_BUCKET)
        blob = bucket.blob(filename)
        if blob.exists():
            blob.delete()
        safe_print(f"[ROLE] Deleted {filename}")
        return jsonify({'success': True})
    except Exception as e:
        safe_print(f"[ROLE DELETE ERROR] {str(e)}")
        return jsonify({'success': True})


# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5003))
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'

    print(f"\n{'='*50}")
    print(f"  BriteTalent - Job Description Generator")
    print(f"  Port: {port}")
    print(f"  Debug: {debug}")
    print(f"  Claude: {'Ready' if claude_client else 'NOT AVAILABLE'}")
    print(f"  GCS: {'Ready' if gcs_client else 'NOT AVAILABLE'}")
    print(f"  OAuth: {'Configured' if os.environ.get('GOOGLE_CLIENT_ID') else 'Disabled (local dev)'}")
    print(f"{'='*50}\n")

    app.run(host='0.0.0.0', port=port, debug=debug)
