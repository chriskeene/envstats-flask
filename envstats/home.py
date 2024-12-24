from flask import Blueprint, flash, g, redirect, render_template, request, url_for
from flask import current_app

home = Blueprint("home", __name__, url_prefix="/")

@home.route("/home2")
def home2():
    #return render_template("home.html")
     return "<p>Hello, World!</p>"

@home.route('/')
def home1():
    return "<p>Hello, World!</p>"
    #return render_template("home.html")

