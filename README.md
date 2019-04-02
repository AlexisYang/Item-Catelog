# Item-Catelog
### Full Stack Web Development NanoDegree
_______________________
## About
This project is a web application that enable users to create/update/delete items under different categories.
## Prerequisites
* Python 2.7.5 [(Download here)](https://www.python.org/downloads/)
* Vagrant [(Download here)](https://www.vagrantup.com/downloads.html)
* VirtualBox [(Download here)](https://www.virtualbox.org/wiki/Downloads)
* PostgreSQL [(Download here)](https://www.postgresql.org/download/)
* Flask [(Reference)](http://flask.pocoo.org)
* SQLAlchemy [(Reference)](https://www.sqlalchemy.org)
* Google OAuth 2.0 [(Reference)](https://developers.google.com/identity/protocols/OAuth2)

## About this repository
This repository contains following files
* database_regen.sh: a script to delete current database and regenerate a new one
* database_setup.py: a script that define the item catelog database
* itemCatelog.py: the file to run the web application
* itemcatelog.db: item catelog database
* lotsofcategories.py: a script to generate an example item catelog database
* /template: a directory that stores all the html templates
* /static: a directory that stores all the webpage styles

## Quick Start
1. Build the item catelog database: ```python database_setup.py```
2. Build default categories data: ```python lotsofcategories.py```
3. Run the webpage: ```python itemCatelog.py```
4. Access the url localhost:5000/

## What's' inside
* The main page contains a column of listed categories, and a column of newly added items. There is a link for google sign in, which enables the access to create/update/delete items. There is also a link to add new items.

![image](https://github.com/AlexisYang/Item-Catelog/blob/master/images/Screen%20Shot%202019-04-02%20at%207.35.34%20PM.png)
* The google login page

![image](https://github.com/AlexisYang/Item-Catelog/blob/master/images/Screen%20Shot%202019-04-02%20at%207.37.23%20PM.png)

* The new item page to add a item with specified category and description. The newly added item would be immediately shown on the main page

![image](https://github.com/AlexisYang/Item-Catelog/blob/master/images/Screen%20Shot%202019-04-02%20at%207.37.59%20PM.png)
* The category page would shown after the user click on random category on the main page

![image](https://github.com/AlexisYang/Item-Catelog/blob/master/images/Screen%20Shot%202019-04-02%20at%207.38.18%20PM.png)
* The item page would shown after the user click on random item on the category page. It is allowed to edit or delete item on the item page, only if the user is logged in.

![image](https://github.com/AlexisYang/Item-Catelog/blob/master/images/Screen%20Shot%202019-04-02%20at%207.39.51%20PM.png)
* The item edit page

![image](https://github.com/AlexisYang/Item-Catelog/blob/master/images/Screen%20Shot%202019-04-02%20at%207.40.00%20PM.png)
* The item delete page

![image](https://github.com/AlexisYang/Item-Catelog/blob/master/images/Screen%20Shot%202019-04-02%20at%207.40.09%20PM.png)
* The user can logout by accessing the page ```localhost:5000/gdisconnect```

![image](https://github.com/AlexisYang/Item-Catelog/blob/master/images/Screen%20Shot%202019-04-02%20at%207.35.19%20PM.png)

* The JSON page shows all the data in the database

![image](https://github.com/AlexisYang/Item-Catelog/blob/master/images/Screen%20Shot%202019-04-02%20at%207.30.28%20PM.png)

## Licience
The content of this repository is licensed under [GPLv3](https://choosealicense.com/licenses/gpl-3.0/) licience.
