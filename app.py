import os, json
from datetime import datetime, timezone
from functools import wraps
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import func

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-only-change-this-secret-before-deploying')
database_url = os.environ.get('DATABASE_URL', 'sqlite:///pragati.db')
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('COOKIE_SECURE', 'false').lower() == 'true'
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    age = db.Column(db.Integer, nullable=True)
    level = db.Column(db.String(80), nullable=False, default='Class 11 (CBSE)')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    is_admin = db.Column(db.Boolean, default=False)

class StudyItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    kind = db.Column(db.String(20), nullable=False) # note, task, progress, test
    title = db.Column(db.String(220), nullable=False)
    content = db.Column(db.Text, nullable=False, default='')
    subject = db.Column(db.String(100), nullable=False, default='General')
    status = db.Column(db.String(40), nullable=False, default='not_started')
    score = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

LEVELS = ['Class 8 (CBSE)','Class 9 (CBSE)','Class 10 (CBSE)','Class 11 (CBSE)','Class 12 (CBSE)','JEE preparation','NEET preparation','Engineering Year 1','Engineering Year 2','Engineering Year 3','Engineering Year 4']
SUBJECTS = ['Physics','Chemistry','Mathematics','Biology','Computer Science','English','General']

def current_user():
    uid = session.get('user_id')
    return db.session.get(User, uid) if uid else None

def login_required(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        if not current_user():
            if request.path.startswith('/api/'):
                return jsonify(error='Please sign in again.'), 401
            return redirect(url_for('home'))
        return fn(*args, **kwargs)
    return wrapped

def item_dict(x):
    return {'id':x.id,'kind':x.kind,'title':x.title,'content':x.content,'subject':x.subject,'status':x.status,'score':x.score,'created_at':x.created_at.isoformat() if x.created_at else None}

@app.get('/')
def home():
    return render_template('index.html', levels=LEVELS, subjects=SUBJECTS, user=current_user())

@app.post('/auth/register')
def register():
    data = request.get_json(silent=True) or request.form
    name = str(data.get('name','')).strip()
    email = str(data.get('email','')).strip().lower()
    password = str(data.get('password',''))
    level = str(data.get('level','Class 11 (CBSE)'))
    try: age = int(data.get('age')) if data.get('age') else None
    except (TypeError, ValueError): age = None
    if len(name) < 2 or len(name) > 100 or '@' not in email or len(password) < 8:
        msg = 'Enter your name, a valid email and a password of at least 8 characters.'
        return (jsonify(error=msg), 400) if request.is_json else (flash(msg, 'error') or redirect(url_for('home')))
    if level not in LEVELS: level = LEVELS[3]
    if User.query.filter_by(email=email).first():
        msg = 'An account with this email already exists. Please sign in.'
        return (jsonify(error=msg), 409) if request.is_json else (flash(msg, 'error') or redirect(url_for('home')))
    admin_email = os.environ.get('ADMIN_EMAIL','').strip().lower()
    u = User(name=name,email=email,password_hash=generate_password_hash(password),age=age,level=level,is_admin=bool(admin_email and email==admin_email))
    db.session.add(u); db.session.commit(); session.clear(); session['user_id']=u.id
    return jsonify(ok=True, user={'name':u.name,'email':u.email,'level':u.level}) if request.is_json else redirect(url_for('home'))

@app.post('/auth/login')
def login():
    data = request.get_json(silent=True) or request.form
    email = str(data.get('email','')).strip().lower(); password = str(data.get('password',''))
    u = User.query.filter_by(email=email).first()
    if not u or not check_password_hash(u.password_hash,password):
        return (jsonify(error='Email or password is incorrect.'),401) if request.is_json else (flash('Email or password is incorrect.','error') or redirect(url_for('home')))
    session.clear(); session['user_id']=u.id
    return jsonify(ok=True,user={'name':u.name,'email':u.email,'level':u.level}) if request.is_json else redirect(url_for('home'))

@app.post('/auth/logout')
def logout():
    session.clear(); return jsonify(ok=True)

@app.get('/api/me')
@login_required
def me():
    u=current_user()
    return jsonify(user={'id':u.id,'name':u.name,'email':u.email,'age':u.age,'level':u.level,'is_admin':u.is_admin})

@app.patch('/api/profile')
@login_required
def update_profile():
    u=current_user(); data=request.get_json(silent=True) or {}
    if data.get('name'): u.name=str(data['name']).strip()[:100]
    if data.get('level') in LEVELS: u.level=data['level']
    if data.get('age') not in (None,''):
        try: u.age=max(5,min(100,int(data['age'])))
        except (ValueError,TypeError): pass
    db.session.commit(); return jsonify(ok=True)

@app.get('/api/items')
@login_required
def get_items():
    kind=request.args.get('kind')
    q=StudyItem.query.filter_by(user_id=current_user().id)
    if kind in ('note','task','progress','test'): q=q.filter_by(kind=kind)
    return jsonify(items=[item_dict(x) for x in q.order_by(StudyItem.updated_at.desc()).all()])

@app.post('/api/items')
@login_required
def create_item():
    d=request.get_json(silent=True) or {}
    kind=str(d.get('kind','task'))
    if kind not in ('note','task','progress','test'): return jsonify(error='Unsupported item type.'),400
    title=str(d.get('title','')).strip()[:220]
    if not title: return jsonify(error='A title is required.'),400
    content=str(d.get('content',''))[:100000]
    subject=str(d.get('subject','General'))[:100]
    status=str(d.get('status','not_started'))[:40]
    score=d.get('score')
    try: score=max(0,min(100,int(score))) if score is not None else None
    except (ValueError,TypeError): score=None
    x=StudyItem(user_id=current_user().id,kind=kind,title=title,content=content,subject=subject,status=status,score=score)
    db.session.add(x); db.session.commit(); return jsonify(item=item_dict(x)),201

@app.patch('/api/items/<int:item_id>')
@login_required
def patch_item(item_id):
    x=StudyItem.query.filter_by(id=item_id,user_id=current_user().id).first_or_404(); d=request.get_json(silent=True) or {}
    for key,limit in [('title',220),('content',100000),('subject',100),('status',40)]:
        if key in d: setattr(x,key,str(d[key])[:limit])
    if 'score' in d:
        try: x.score=max(0,min(100,int(d['score']))) if d['score'] is not None else None
        except (ValueError,TypeError): pass
    x.updated_at=datetime.now(timezone.utc); db.session.commit(); return jsonify(item=item_dict(x))

@app.delete('/api/items/<int:item_id>')
@login_required
def delete_item(item_id):
    x=StudyItem.query.filter_by(id=item_id,user_id=current_user().id).first_or_404(); db.session.delete(x); db.session.commit(); return jsonify(ok=True)

@app.get('/api/dashboard')
@login_required
def dashboard():
    uid=current_user().id
    items=StudyItem.query.filter_by(user_id=uid).all()
    tasks=[x for x in items if x.kind=='task']; tests=[x for x in items if x.kind=='test']; notes=[x for x in items if x.kind=='note']
    scores=[x.score for x in tests if x.score is not None]
    return jsonify(stats={'tasks':len(tasks),'tasks_done':sum(x.status=='completed' for x in tasks),'notes':len(notes),'tests':len(tests),'average_score':round(sum(scores)/len(scores)) if scores else 0,'completed_topics':sum(x.kind=='progress' and x.status=='completed' for x in items)}, recent=[item_dict(x) for x in sorted(items,key=lambda x:x.updated_at or x.created_at,reverse=True)[:8]])

@app.post('/api/ai')
@login_required
def ai_coach():
    data=request.get_json(silent=True) or {}; prompt=str(data.get('prompt','')).strip()[:8000]
    if not prompt: return jsonify(error='Write a question first.'),400
    key=os.environ.get('OPENAI_API_KEY')
    if not key: return jsonify(error='AI is not connected yet. Add OPENAI_API_KEY in your hosting environment to enable the AI Study Coach. Other PRAGATI features still work.'),503
    try:
        import requests
        u=current_user()
        r=requests.post('https://api.openai.com/v1/responses',headers={'Authorization':f'Bearer {key}','Content-Type':'application/json'},json={'model':os.environ.get('OPENAI_MODEL','gpt-4.1-mini'),'instructions':f'You are PRAGATI Study Coach for a student studying {u.level}. Explain clearly, step by step, encourage learning, and do not just give unexplained answers. If solving a problem, show method and final answer. Do not claim syllabus details are official unless certain.','input':prompt,'max_output_tokens':1200},timeout=45)
        if r.status_code>=400: return jsonify(error='The AI provider returned an error. Check your API key and billing settings.'),502
        payload=r.json(); answer='\n'.join(block.get('text','') for block in payload.get('output',[]) if block.get('type')=='message' for block in block.get('content',[]) if block.get('type')=='output_text')
        return jsonify(answer=answer or 'No response was returned.')
    except Exception:
        app.logger.exception('AI coach request failed'); return jsonify(error='Could not reach the AI service. Please try again.'),502

@app.get('/api/admin/summary')
@login_required
def admin_summary():
    u=current_user()
    if not u.is_admin: return jsonify(error='Admin access is not enabled for this account.'),403
    return jsonify(users=User.query.count(),items=StudyItem.query.count(),students=[{'name':x.name,'email':x.email,'level':x.level,'created_at':x.created_at.isoformat()} for x in User.query.order_by(User.created_at.desc()).limit(100)])

@app.get('/manifest.webmanifest')
def manifest(): return send_from_directory('static','manifest.webmanifest',mimetype='application/manifest+json')
@app.get('/service-worker.js')
def service_worker():
    resp=send_from_directory('static','service-worker.js',mimetype='application/javascript'); resp.headers['Service-Worker-Allowed']='/'; return resp
@app.get('/health')
def health(): return jsonify(status='ok',app='PRAGATI')

with app.app_context(): db.create_all()

if __name__ == '__main__':
    app.run(host='0.0.0.0',port=int(os.environ.get('PORT',5000)),debug=False)
