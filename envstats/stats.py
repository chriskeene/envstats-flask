from io import BytesIO
import os 
import time
from flask import Blueprint, flash, g, redirect, render_template, request, url_for, jsonify
from datetime import datetime, date, timedelta
from decimal import Decimal
import click
import time
# for matplotlib
import matplotlib
from matplotlib.figure import Figure
from matplotlib import pyplot as plt
import base64
# for Sheffield solar stats
from pvlive_api import PVLive
#import numpy as np
import pandas as pd
#import requests
from envstats.db import query_db
matplotlib.use('agg')

stats = Blueprint("stats", __name__, url_prefix="/stats")

#create a df for each year
def split_years(dt):
    return [dt[dt['year'] == y] for y in dt['year'].unique()]


@stats.route("/listdb")
def listdb():
    output = {
        "title": "LIST",
    }
    query = "SELECT * from solar ORDER BY date"
    output["posts"] = query_db(query)
    latest_query = "SELECT date FROM public.solar ORDER BY date DESC limit 1"
    output["latest"] = query_db(latest_query)
    return render_template("stats/index.html", output=output)


def get_solar_data():
    """Get solar data from our db and add to a dataframe df"""
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
    plt.title("UK Solar output since 2021", size = 15)
    plt.ticklabel_format(style='plain', axis='y')
    plt.savefig('envstats/static/images/solar1.png')
    plt.close() 

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
    plt.close() 

#create a df for each year
def split_years(dt):
    return [dt[dt['year'] == y] for y in dt['year'].unique()]



def create_solar_table1(df):
    df4 = split_years(df)
    df5 = pd.DataFrame(columns=['Total', 'Jan', 'Feb', 'Mar', 'Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'])
    #df4 is a list of dataframes, each one being one years worth of data
    for yeardf in df4:
        # look at year value(1) in the first row
        thisyear = yeardf.iat[0, 1]
        #make a list of each month's solar output for this year
        thistotlist = yeardf['solartotal'].tolist()
        # the current year wont have 12 months worth of values
        while len(thistotlist) < 12:
            thistotlist.append(0)
        # add a total to the front on the list 
        thistotlist.insert(0,sum(thistotlist))
        #add this year and its list to new df
        df5.loc[thisyear] = thistotlist
    return df5

@stats.route('/')
@stats.route("/solar")
def solarstats():
    output = {
        "title": "UK PV Solar every output",
    }
    df = get_solar_data()
    # print table 
    df5 = create_solar_table1(df)
    # the following takes df5 and converts it to html, most of the code is for converting to floats so that we can add thousand seperators
    output["table1"] = [df5.astype('float64',errors='ignore').to_html(float_format=lambda x: format(x,',.0f'),classes='table table-hover data')]
    output["table1json"] = df5.to_json(orient='records')
    # Convert the DataFrame to a dictionary for Chart.js
    data_dict = df5.to_dict(orient='list')
    output["tjson2"] = jsonify(data_dict)
    # the most recent date collected
    latest_query = "SELECT date FROM public.solar ORDER BY date DESC limit 1"
    output["latest"] = query_db(latest_query)
    return render_template("stats/solar.html", output=output)


# for running from command line. only retrieves solar data from api
# for those days with no data. by default check the last 30 days
def add_historic(start_date = None):
    pvl = PVLive(domain_url="api.pvlive.uk")
    def daterange(start_date, end_date):
        for n in range(int((end_date - start_date).days)):
            yield start_date + timedelta(n)

    # if we were passed a date just process for that date
    if start_date:
        end_date = (start_date+timedelta(days=1))  
    else:   
        #otherwise process for last 35 days
        start_date = date(2023, 7, 1)
        end_date = date(2023, 8, 1)
        end_date = date.today()  
        start_date = (date.today()-timedelta(days=20))
    for single_date in daterange(start_date, end_date):
        # check if we have stats already...
        # TODO this should only be one query not one for each date!
        print ("checking " + str(single_date))
        checksql = "SELECT * from solar where date = %s;"
        existingdata = query_db(checksql, (single_date,))
        # if we have this date in the database (and hence a non empty list) we don't need to fetch
        if not existingdata:
            # collect stats from api
            tmpdatestring = single_date.strftime("%Y--%m--%d")
            tmpdatestring2 = single_date.strftime("%Y%m%d")
            daysolartotal = pvl.day_energy(single_date, entity_type="pes", entity_id=0)
            # reduce to 2 decimal places
            daysolartotal = round(daysolartotal,2)
            addsql = "INSERT INTO solar (id, date, solartotal) VALUES(%s, %s, %s);"
            query_db(addsql, (tmpdatestring2, tmpdatestring, daysolartotal))
            print("adding..." + tmpdatestring2)
            time.sleep(1)
    # generate_solar_pmg()
    df = get_solar_data()
    create_solar_chart1(df)
    create_solar_chart2(df)

# command line function to check historic values 
def check_historic():
    pvl = PVLive()
    def daterange(start_date, end_date):
        for n in range(int((end_date - start_date).days)):
            yield start_date + timedelta(n)

    start_date = date(2024, 3, 1)
    end_date = date(2024, 3, 17)
    #end_date = date.today()  
    #start_date = (date.today()-timedelta(days=30))
    for single_date in daterange(start_date, end_date):
        # check if we have stats already...
        # TODO this should only be one query not one for each date!
        checksql = "SELECT * from solar where date = %s;"
        existingdata = query_db(checksql, (single_date,))
        # if we have this date in the database (and hence a non empty list) we can compare
        if existingdata:
            existingsolartotal = existingdata[0][2]
            existingsolarid = existingdata[0][0]
            # collect stats from api
            tmpdatestring2 = single_date.strftime("%Y%m%d")
            daysolartotalfloat = pvl.day_energy(single_date, entity_type="pes", entity_id=0)
            print(daysolartotalfloat)
            tmpsolarstring = str(daysolartotalfloat)
            print(tmpsolarstring)
            daysolartotal = Decimal(tmpsolarstring)
            # reduce to 2 decimal places
            daysolartotal = round(daysolartotal,2)
            existingsolartotal = round(existingsolartotal,2)
            if daysolartotal == existingsolartotal:
                print("MATCH : " + tmpdatestring2 + " api " + str(daysolartotal) + " db " + str(existingsolartotal))
            else:
                difference = abs(daysolartotal-existingsolartotal)
                print("INCORRECT! : " + tmpdatestring2 + " api " + str(daysolartotal) + " db " + str(existingsolartotal) + " diff:" + str(difference))
                #log the difference
                addsql = "INSERT INTO solar_check_log (\"current_date\", date, orig_value, new_value, difference) VALUES(%s, %s, %s, %s, %s);"
                query_db(addsql, (date.today(), single_date,existingsolartotal, daysolartotal, difference))
                #now update the db
                updatesql = "UPDATE solar SET solartotal = '%s' where id = %s;"
                query_db(updatesql, (daysolartotal,existingsolarid))
            time.sleep(1)
        else:
            print("not in db: ", single_date )
            add_historic(single_date)



@click.command('add-solar-history')
def add_solar_history_command():
    """Adding older solar data."""
    add_historic()
    click.echo("done")

@click.command('check-solar-data')
def check_solar_data_command():
    """Adding older solar data."""
    check_historic()
    click.echo("done")    


def init_app(app):
    app.cli.add_command(add_solar_history_command)
    app.cli.add_command(check_solar_data_command)
