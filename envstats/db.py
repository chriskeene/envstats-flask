import psycopg2
import os
import click
from flask import current_app, g


# connect to postrgres on a remote server
# note must use .zshrc file to set env vars.
def get_db2():
    if 'db' not in g:
        if not os.getenv("POSTGRESHOST"):
            raise RuntimeError("POSTGRESHOST is not set")
        
        g.db = psycopg2.connect(
            host=os.getenv("POSTGRESHOST"),
            database=os.getenv("POSTGRESDB"),
            user=os.getenv("POSTGRESUSER"),
            password=os.getenv("POSTGRESPASS"))
        
    return g.db


def query_db(query, args=None):
    """execute query on connection
    stored in g.
    """
    cnx = get_db2()
    cursor = cnx.cursor()
    cursor.execute(query, args)
    try:
        results = cursor.fetchall()
    except: 
        results = 0 
    cnx.commit()
    cursor.close()
    return results

def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()

def init_db():
    db = get_db2()
    #db3 = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT version()')
    db_version = cursor.fetchone()
    print(db_version)
    with current_app.open_resource('schema.sql') as f:
        cursor.execute(f.read().decode('utf8'))
        db.commit()

    


@click.command('init-db')
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo('Initialized the database.')

def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)