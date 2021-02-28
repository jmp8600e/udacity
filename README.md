# Project: Linux Server Configuration

This project is web based application created on using Flask Framework, Python as a backend programming language. This also uses a SQLAlchemy as ORM to interface with Postgresql database engine.   This is running on Amazon Lightsail Platform. 

### Grader Access info    
    - Grader can access the server on IP 18.234.232.231 on port 2200.
    - Web application can be access using: http://18.234.232.231.xip.io
    
### What was done?
    - User account name grader created.
    - Only port 2200 is enabled for SSH.
    - Only using PPK certificate one can acecss the SSH, password based SSH is disabled.
    - Only port 80 and 2200 are enabled.
    - Existing GitHub repo https://github.com/jmp8600e/udacity.git cloned and modifications have been done to make it work with Postgresql instead of sqlite3. See the modification section.

### Modifications to existing catalog project
1. Rename catalogapp.py to __init__.py
2. New DB engine connection to postgresql and removal of connect_args={'check_same_thread': False}) 
3. full paths to the client_sercet files
4. change xrange to range
5. update DB engine connection to postgresql in database_setup.py
6. Flask App is created under /var/www/FlaskApp/CatalogApp
7. change ownershipe of /var/www/FlaskApp to www-data:www-data (user under which apache runs)
8. Change the google client key in login.html
9. created new client_secret.json from google added proper *.xip.io domain and redirects on API account
10. FB Logins will not work as it needs https domains to be added in the API account

### Key Files
    /var/www/FlaskApp/flaskapp.wsgi
    /var/www/FlaskApp/CatalogApp/__init__.py
    /var/www/FlaskApp/CatalogApp/database_setup.py
    /var/log/apache2/error.log
    /etc/apache2/sites-available/FlaskApp.conf
    
### Postgresql Changes
- Creation of User and Database
```sh
    createuser catalogappuser
    createdb catalogapp
```
- Creation of Table Schema
```sh
psql catalogapp
CREATE TABLE "user" (
    id SERIAL PRIMARY KEY,
    name VARCHAR (250) NOT NULL,
    email VARCHAR (250) NOT NULL,
    picture VARCHAR (250),
    password VARCHAR (250)
);
CREATE TABLE "categories" (
    id SERIAL PRIMARY KEY,
    name VARCHAR(250) NOT NULL,
    user_id INTEGER,
    FOREIGN KEY (user_id) REFERENCES "user" (id)
);
CREATE TABLE "items" (
    title VARCHAR(80) NOT NULL,
    id SERIAL PRIMARY KEY,
    description VARCHAR(1000),
    category_id INTEGER,
    user_id INTEGER,
    FOREIGN KEY (category_id) REFERENCES "categories" (id),
    FOREIGN KEY (user_id) REFERENCES "user" (id)
);
```
- Grant peroper permission to user 
```sh
    GRANT SELECT, UPDATE, INSERT, DELETE ON "categories" TO catalogappuser;
    GRANT SELECT, UPDATE, INSERT, DELETE ON "user" TO catalogappuser;
    GRANT SELECT, UPDATE, INSERT, DELETE ON "items" TO catalogappuser;
    GRANT USAGE, SELECT ON SEQUENCE user_id_seq TO catalogappuser;
    GRANT USAGE, SELECT ON SEQUENCE items_id_seq TO catalogappuser;
    GRANT USAGE, SELECT ON SEQUENCE categories_id_seq TO catalogappuser;
```

### Softwares installed     
- First performed update and upgrade of packages
```sh
    sudo apt-get update
    sudo apt-get upgrade
```
- Installed following packages  
 ```sh 
    sudo apt-get install apache2
    sudo apt-get install libapache2-mod-wsgi-py3
    sudo apt-get install git-core
 ``` 
- Enbled mod_wsgi,
```sh    
    sudo a2enmod wsgi
```
 - git clone catalog project repo from GitHug to folder /project
```sh
    git clone https://github.com/jmp8600e/udacity.git
``` 
- Installed following packages  
 ```sh 
    sudo apt-get update
    sudo apt-get upgrade
    sudo pip3 install virtualenv
    sudo virtualenv venv
    sudo pip3 install Flask
    sudo pip3 install Flask-HTTPAuth
    sudo pip3 install Flask-SQLAlchemy
    sudo pip3 install httplib2
    sudo pip3 install Jinja2
    sudo pip3 install oauth2client
    sudo pip3 install requests
    sudo pip3 install Flask-SQLAlchemy
    sudo pip3 install SQLAlchemy
    sudo pip3 install psycopg2
    sudo a2ensite FlaskApp
    sudo apt-get install postgresql
```
- Activate venv
```sh
    source venv/bin/activate
```
- Disable defalt Apache site   
```sh
    sudo a2dissite 000-default
```
- Enable Flask app  
```sh
    sudo a2ensite CatalogApp
```    

### Third-Party Resources

- Udacity Questions and Anwers

    https://knowledge.udacity.com/questions/28071
    https://knowledge.udacity.com/questions/21110
    https://knowledge.udacity.com/questions/28049

- Postgresql resources

    https://www.postgresql.org/docs/9.0/sql-grant.html
    https://www.postgresql.org/docs/9.1/sql-altertable.html
    https://www.postgresql.org/docs/9.1/sql-createtable.html

- SQLAlchemy resources

    https://docs.sqlalchemy.org/en/latest/errors.html#error-dbapi
    https://docs.sqlalchemy.org/en/latest/core/engines.html

- Other resources

    https://chartio.com/resources/tutorials/how-to-list-databases-and-tables-in-postgresql-using-psql/
    https://www.digitalocean.com/community/tutorials/how-to-use-roles-and-manage-grant-permissions-in-postgresql-on-a-vps--2
    https://www.digitalocean.com/community/tutorials/how-to-secure-postgresql-on-an-ubuntu-vps
    http://leonwang.me/post/deploy-flask
    https://stackoverflow.com/questions/9325017/error-permission-denied-for-sequence-cities-id-seq-using-postgres
    https://console.developers.google.com
    https://developers.facebook.com
    https://lightsail.aws.amazon.com
    https://dillinger.io

Thanks,
-Jatin

  
