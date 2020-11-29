from flask import Flask, render_template, send_from_directory, redirect, request, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy 
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, LoginManager, login_required, logout_user, login_user, current_user
from urllib.parse import urlparse, urljoin
from flask_admin import Admin, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from flask_admin.contrib.fileadmin import FileAdmin
from flask_ckeditor import CKEditor
from os.path import dirname, join


app = Flask(__name__)
app.config.from_pyfile('config.cfg')

# Configure an insecure connection since we are using an
# insecure CockroachDB cluster
connect_args = {'sslmode' : 'disable'}
engine_options = {"connect_args" : connect_args}

# Bind the ORM to this specific Flask application,
# using the specified engine options
db = SQLAlchemy(app,engine_options=engine_options)

login_manager = LoginManager(app)
login_manager.login_view = 'login'

path =  join(dirname(__file__), 'static/images/')

ckeditor = CKEditor(app)

def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc

tagged_posts = db.Table("tagged_posts", 
    db.Column("post_id", db.Integer, db.ForeignKey("blogpost.id")),
    db.Column("tag_id", db.Integer, db.ForeignKey("blogtag.id"))
)

class blogpost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(50), nullable=False)
    slug = db.Column(db.String(50), nullable=False)
    subtitle = db.Column(db.String(50), nullable=False)
    author = db.Column(db.String(10), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False)
    description = db.Column(db.Text, nullable=False)
    content = db.Column(db.Text, nullable=False)
    image = db.Column(db.String(50), nullable=False)
    tags = db.relationship("blogtag", secondary=tagged_posts, backref=db.backref("post", lazy="dynamic"))

    def __repr__(self):
        return '<blogpost %r' % (self.id)

class blogtag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tag = db.Column(db.String(50))

    def __repr__(self):
        return '<blogptag %r' % (self.id)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(15), unique=True)
    password = db.Column(db.String(100))

    def __repr__(self):
        return '<User %r' % (self.username)

class UserView(ModelView):
    column_exclude_list = ['password']
    column_display_pk = True
    can_export = True

    def is_accessible(self):
        return current_user.is_authenticated

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login'))

class MyAdminView(AdminIndexView):
    def is_accessible(self):
        return current_user.is_authenticated

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login'))

admin = Admin(app, template_mode='bootstrap3', index_view=MyAdminView())
admin.add_view(UserView(User, db.session))
admin.add_view(UserView(blogpost, db.session))
admin.add_view(UserView(blogtag, db.session))
admin.add_view(FileAdmin(path, '/static/images/',name='Uploads'))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Rediction section for production server only
'''
@app.route('/')
def root():
    return redirect(new_url, code=302)

@app.route('/<path:page>')
def anypage(page):
    return redirect('{new_url}/{page}'.format(page=page, new_url=new_url), code=302)
'''

# Remaining endpoints
@app.route("/")
def home():
    posts = blogpost.query.order_by(blogpost.date_posted.desc()).all()
    return render_template('index.html', posts=posts)

@app.route("/article/")
@app.route("/article")
def article():
    return redirect(url_for('home'))

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/login", methods=["POST"])
def login_post():
    if request.method == 'POST':
        username = request.form.get("user")
        password = request.form.get("password")
        user = User.query.filter_by(username=username).first()

        if not user or not check_password_hash(user.password, password):
            flash("Invalid credentials")
            return redirect(url_for("login"))

        login_user(user, remember=True)

        if 'next' in session:
            next = session['next']

            if is_safe_url(next):
                return redirect(next) 

    session['next'] = request.args.get('next')
    return redirect(url_for("home"))

@app.route('/article/<string:slug>/')
def post(slug):
    post = blogpost.query.filter_by(slug=slug).one()
    tags = blogtag.query.filter(blogtag.post.any(slug=slug)).all() 
    return render_template('article.html', post=post, tags=tags)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))

@app.route("/delete/<int:id>", methods=['GET', 'POST'])
@login_required
def delete(id):
    post = blogpost.query.filter_by(id=id).first()
    db.session.delete(post)
    db.session.commit()
    return redirect(url_for('home'))

@app.route('/tutorials/<string:tag>/')
def tagged(tag):
    posts = blogpost.query.filter(blogpost.tags.any(tag=tag)).order_by(blogpost.date_posted.desc()).all()
    return render_template('tutorial.html', posts=posts, tag=tag.capitalize())

@app.route('/add')
@login_required
def add():
    return render_template('add.html')

@app.route('/addpost', methods=['POST'])
@login_required
def addpost():
    title = request.form['title']
    slug = request.form['slug']
    subtitle = request.form['subtitle']
    author = request.form['author']
    description = request.form['description']
    image = request.form['image']
    content = request.form['ckeditor']
    tags = (request.form['tag']).split(' ')

    post = blogpost(title=title, slug=slug, subtitle=subtitle, author=author, description=description, image=image, content=content, date_posted=datetime.now())

    db.session.add(post)
    db.session.commit()

    for i in tags:
        tag_id = db.session.query(blogtag.id).filter_by(tag=i).scalar()

        # unique tags
        if tag_id is None:
            tag = blogtag(tag=i)
            tag.post.append(post)                                                                                                         
            db.session.commit()  
                                                                                                                                
        # duplicate tags
        else:
            tag = blogtag.query.filter_by(id=tag_id).one()
            post.tags.append(tag)
            db.session.commit() 

    return redirect(url_for('home'))

@app.route("/edit/<int:id>", methods=['GET', 'POST'])
@login_required
def edit(id):
    post = blogpost.query.filter_by(id=id).first()

    if request.method == 'POST':
        post.title = request.form['title']
        post.slug = request.form['slug']
        post.subtitle = request.form['subtitle']
        post.author = request.form['author']
        post.description = request.form['description']
        post.image = request.form['image']
        post.content = request.form['content']

        db.session.commit()
        return redirect('/article/' + post.slug+ '/')

    else:
        return render_template('edit.html', post=post)

    return redirect(url_for('home'))

@app.route("/search", methods=["GET", "POST"])
def search_get():
    search_info = request.form["search_box"]
    all_posts = blogpost.query.filter((blogpost.description.like(f"%{search_info}%"))|(blogpost.slug.like(f"%{search_info}%"))).order_by(blogpost.date_posted.desc()).all()
    return render_template("search.html", posts=all_posts)


@app.route("/about")
def about():
    return render_template('about.html')

@app.route("/thanks")
def thank():
    return render_template('thank.html')

@app.route("/tutorials/")
def tut_redirect():
    return redirect(url_for('tuts'))


@app.route("/tutorials/all/")
def tuts():
    return render_template('tutorial.html')

@app.route('/sitemap.xml')
def static_from_root():
    return send_from_directory(app.static_folder, 'sitemap.xml')

@app.route('/robots.txt')
def static_from_roots():
    return send_from_directory(app.static_folder, 'robots.txt')

@app.errorhandler(404)
def not_found(e):
  return render_template('error.html')

if __name__ == '__main__':
    app.config["TEMPLATES_AUTO_RELOAD"] = True
    app.run(debug=True)
