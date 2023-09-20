from io import BytesIO
from flask import Blueprint, flash, g, redirect, render_template, request, url_for
from datetime import datetime, date, timedelta
import click
import time

# for matplotlib
import matplotlib
from matplotlib.figure import Figure
from matplotlib import pyplot as plt
import base64
matplotlib.use('agg')
# for Sheffield solar stats
from pvlive_api import PVLive
#
import numpy as np
import pandas as pd
from envstats.db import query_db

bp = Blueprint("stats", __name__, url_prefix="/stats")

#create a df for each year
def split_years(dt):
    return [dt[dt['year'] == y] for y in dt['year'].unique()]


@bp.route("/listdb")
def listdb():
    query = "SELECT * from solar"
    posts = query_db(query)
    return render_template("stats/index.html", rows=posts)

def get_solar_data():
    query = """SELECT concat(date_part('year', date), '/', date_part('month', date)) as "Date", 
        date_part('year', date) as "Year",
        date_part('month', date) as "Month",
        trunc(sum(solartotal) ) as "Solar"
        from solar 
        group by date_part('year', date), date_part('month', date)
        order by date_part('year', date), date_part('month', date);"""
    dbdata = query_db(query)
    #
    column_names = ['date', 'year', 'month', 'solartotal']
    tuples_list = dbdata
    # Now we need to transform the list into a pandas DataFrame:
    df = pd.DataFrame(tuples_list, columns=column_names)
    df['month'] = df['month'].astype(int)
    df['year'] = df['year'].astype(int)
    df['solartotal'] = df['solartotal'].astype(int)
    return df

def create_solar_chart1(df):
    df = df[['date','solartotal']]
    ax = df.plot(kind='line', grid=1, fontsize=10, x="date")
    plt.xlabel("Month",  size = 10)
    plt.legend(fontsize="8", loc ="lower left")
    plt.ylabel("solar energy output", size = 10)
    plt.title("Solar electical output", size = 15)
    plt.ticklabel_format(style='plain', axis='y')
    plt.savefig('envstats/static/images/foo.png')

def create_solar_chart2(df):
    df4 = split_years(df)
    plt.style.use('ggplot') 
    plt.xlabel('Month')
    plt.ylabel('solar output')
    for y in df4:
        y.name = y['year'].iloc[[0]].to_string(index=False)
        plt.plot(y['solartotal'].tolist(),label= y.name)
    plt.legend(loc='best')
    plt.title('Solar output per year')
    plt.ticklabel_format(style='plain', axis='y')
    plt.xticks([0,1,2,3,4,5,6,7,8,9,10,11], ['Jan', 'Feb', 'Mar', 'Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'],rotation=20)
    plt.savefig('envstats/static/images/solar2.png')


@bp.route("/solar")
def solarstats():
    output = {
        "title": "solar output",
    }
    df = get_solar_data()
    #create_solar_chart1(df)
    #create_solar_chart2(df)
    # print table 
    output["table1"] = [df.to_html(classes='data')]
    output["table1titles"] = df.columns.values
    return render_template("stats/solar.html", output=output)


# for running from command line. only retrieves solar data from api
# for those days with no data. by default check the last 30 days
def add_historic():
    pvl = PVLive()

    def daterange(start_date, end_date):
        for n in range(int((end_date - start_date).days)):
            yield start_date + timedelta(n)

    start_date = date(2023, 7, 1)
    end_date = date(2023, 8, 1)
    end_date = date.today()  
    start_date = (date.today()-timedelta(days=30))
    for single_date in daterange(start_date, end_date):
        # check if we have stats already...
        # TODO this should only be one query not one for each date!
        checksql = "SELECT * from solar where date = %s;"
        existingdata = query_db(checksql, (single_date,))
        # if we have this date in the database (and hence a non empty list) we don't need to fetch
        if not existingdata:
            # collect stats from api
            tmpdatestring = single_date.strftime("%Y--%m--%d")
            tmpdatestring2 = single_date.strftime("%Y%m%d")
            daysolartotal = pvl.day_energy(single_date, entity_type="pes", entity_id=0)
            addsql = "INSERT INTO solar (id, date, solartotal) VALUES(%s, %s, %s);"
            query_db(addsql, (tmpdatestring2, tmpdatestring, daysolartotal))
            print("adding..." + tmpdatestring2)
            time.sleep(1)
        #else:
         #   print("already have: ", existingdata[0] )
    # generate_solar_pmg()
    df = get_solar_data()
    create_solar_chart1(df)
    create_solar_chart2(df)

@click.command("add-solar-history")
def add_solar_history_command():
    """Adding older solar data."""
    add_historic()
    click.echo("done")


def init_app(app):
    app.cli.add_command(add_solar_history_command)
