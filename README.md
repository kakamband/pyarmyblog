## Steps to initialize database

* from app import db
* db.create_all()

* from werkzeug.security import generate_password_hash
* from app import User
* pj = User(username='pjdude', password=generate_password_hash("pawan@431"))
* db.session.add(pj)
* db.session.commit()

#### Additional

* insert into User (username) values ('Pawan')
