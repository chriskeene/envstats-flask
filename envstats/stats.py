from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)

from datetime import datetime, date, timedelta
import time
import click
from envstats.db import get_db2
from envstats.db import query_db
from datetime import datetime, date, timedelta
# for postgres
import psycopg2
# for matplotlib
import base64
from io import BytesIO

# for Sheffield solar stats
from pvlive_api import PVLive

bp = Blueprint('stats', __name__, url_prefix='/stats')

@bp.route('/listdb')
def listdb():
    query = 'SELECT * from solar'
    posts = query_db(query)
    return render_template('stats/index.html', rows=posts)
   


def add_historic():
    pvl = PVLive()
    def daterange(start_date, end_date):
        for n in range(int((end_date - start_date).days)):
            yield start_date + timedelta(n)

    start_date = date(2021, 1, 1)
    end_date = date(2022, 6, 5)
    for single_date in daterange(start_date, end_date): 
        # check if we have stats already...
        checksql = 'SELECT * from solar where date = %s;'

        existingdata = query_db(checksql, (single_date,))
        # if we have this date in the database (and hence a non empty list) we don't need to fetch
        if not existingdata:
            # collect stats from api
            tmpdatestring = single_date.strftime("%Y--%m--%d")
            tmpdatestring2 = single_date.strftime("%Y%m%d")
            daysolartotal = pvl.day_energy(single_date, entity_type="pes", entity_id=0)
            addsql = "INSERT INTO solar (id, date, solartotal) VALUES(%s, %s, %s);"
            query_db(addsql, (tmpdatestring2, tmpdatestring, daysolartotal ))
            print("adding..." + tmpdatestring2)
            time.sleep(1)
        else:
            print ("already have:")
            print (existingdata[0])

@click.command('add-solar-history')
def add_solar_history_command():
    """Adding older solar data."""
    add_historic()
    click.echo('done')

def init_app(app):
    app.cli.add_command(add_solar_history_command)










