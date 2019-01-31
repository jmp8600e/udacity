# Project: Catalog Project

This project is wev based application created on using Flask Framework, Python as a backend programming language. This also uses a SQLAlchemy as ORM to interface with SQLLite3 database engine.  

The project has following requirements. 
  - Shows users all Categories and Latest Items added
  - Ability to click on particular Categories which then shows Items for that catgories
  - Ability to click on particular Item which give more detailed description about the item
  - Ability to login as Google and Facebook users 
  - Ability to create local accounts
  - Ability to create new item (and new category if needed)
  - Ability to delete item owned by logged in user
  - Ability to updated item owned by logged in user
  - Other users should not be able to udpate/delete items owned by other users
  - JSON endpoint which shows data in JSON format

### Platform Prerequisite

  - Python 2.7.12 and later
  - SQLAlchemy ORM
  - Flask Framework
  
### Files Description
    
  - catalogapp.py: main python file whcih user will execute to start the application
  - database_setup.py: prerequisite before running above py file, this will create an empty SQLLite database with proper schema
  - fb_client_secrets.json and client_secret.json: this is used for FB and Google login, substitute your Google and FB API access information to make this login working
  - templates folder: there are many html files under this folder, user does not need to update these files
  - satic/w3.css: this is the css file, user does not need to update this file. 
  

### Runtime Prerequisite
  - copy all files to a any folder, for example /Catalog go to this folder and run command
    ```sh
    python ./database_setup.py
    
  - confirm that databased catalogapp.db file is created, you can use sqllite3 command to explore the database and its schema
  
  - if you want to have FB and Google login then do ahead and update the JSON files listed in last section. ONLY then this part will work otherwise Google/FB sign in will not work. 
  
  - Now finally run below command 
    ```sh
    python ./catalogapp.py

  - This will start the web application on port 5000. You can access this by goint go http://localhost:5000
  
  - Go through creating local user and creating items. 
  
  - JSON Endpoint can be access using http://localhost:5000/catalog/JSON or http://localhost:5000/catalog.json
  
Happy Testing!! Feel Free to Contribute to the project!! The application is also optimized for mobile and tablet based access. 

Thanks,
-Jatin

  
