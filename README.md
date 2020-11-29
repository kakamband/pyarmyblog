# Pyarmyblog
Project developed during Who Wants To Be A Hackionaire Hackathon

## In LocalHost with same DB

* Install all dependencies by ```pip install -r requirements.txt```
* Run app.py and head to http://127.0.0.1:5000/

## In LocalHost in own DB
* Install all dependencies by ```pip install -r requirements.txt```
* Delete Database.db

* Open python terminal

```python
* from app import db
* db.create_all()

* from werkzeug.security import generate_password_hash
* from app import User
* pj = User(username='{you_name}', password=generate_password_hash("{password}"))
* db.session.add(pj)
* db.session.commit()
```

### Video 
**CLICK ON IMAGE TO PLAY VIDEO**

[![Project Screen](https://img.youtube.com/vi/G3v-P9-mx5Q/0.jpg)](https://www.youtube.com/watch?v=G3v-P9-mx5Q)
