from flask import Blueprint, flash, g, redirect, render_template, request, url_for
from flask import current_app
import os 
import time


home = Blueprint("home", __name__, url_prefix="/")

@home.route("/home2")
def home2():
    cwd = os.getcwd() 
    try:
        #return render_template("home.html")
        solar2date = (os.path.getmtime("/opt/envstats/envstats/static/images/solar2.png"))    
        realsolardate2 = str(time.gmtime(solar2date))
        tmp = time.strftime("%a, %d %b %Y %H:%M",time.gmtime(solar2date))
    except:
        tmp = "unsure."
    return "<p>Hello, add /stats/ to the url " + tmp + cwd

@home.route('/')
def home1():
    return "<p>Hello, add /stats/ to the url, or just go <a href='stats/'>here</a>.</p>"
    #return render_template("home.html")

