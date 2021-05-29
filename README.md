<h1 align="center">WhatsApp Clone Using Javascript, Python and Redis</h1>

<p align="center"><img width="100%" src="https://github.com/triple07even/Whatsapp_full_clone/blob/main/private_chat_screenshot.png" alt="Private chat screenshot"></p>

This project is a Whatsapp clone using JavaScript and Python
The python framework used in this build in Django

<h5> Warning: This app is not a production </h5>

Note: Make sure you have Redis Installed

Linux/ Unix Installation
Make sure your apt package is up to date `sudo apt update`
Install Redis Server `sudo apt-get install redis-server`
Check version and ensure your version is up to >=6 `redis-cli -v`

Installation
* Create a python virtual env `python3 -m venv env`
* Activate the virtual enviroment `source env/bin/activate`
* Downloading the repo
* cd to the directry `cd Whatsapp_full_clone/`
  * Install all dependencies required: `pip install -r requirements.txt`
  * Open two command line window
    * For the first window `python manage.py runserver 0:8000`
    * On the second window `celery -A mysite worker -l INFO`
* Open your browser and enter `http://localhost.com:8000`
