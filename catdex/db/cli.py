import argparse
import csv

import pkg_resources
import sqlalchemy as sqla

import catdex.db


### "load" command

def load(connection):
    """Create the database from scratch."""

    print('Creating tables...')
    catdex.db.TableBase.metadata.create_all(connection)

    print('Loading tables...')
    for table in catdex.db.TableBase.metadata.sorted_tables:
        print('  - {}...'.format(table.name))
        load_table(table, connection)

def load_table(table, connection):
    """Load data into an empty table from a CSV."""

    csv_path = 'db/data/{0}.csv'.format(table.name)
    csv_path = pkg_resources.resource_filename('catdex', csv_path)

    with open(csv_path, encoding='UTF-8', newline='') as table_csv:
        reader = csv.DictReader(table_csv)
        rows = list(preprocess_rows(table, reader))

    connection.execute(table.insert(), rows)

def preprocess_rows(table, reader):
    """Yield from a CSV dict reader, and as we go, tweak certain values that
    SQLA won't get right on its own.
    """

    for row in reader:
        for column_name, value in row.items():
            column = table.c[column_name]

            if value == '' and column.nullable:
                row[column_name] = None
            elif isinstance(column.type, sqla.types.Boolean):
                if value == 'True':
                    row[column_name] = True
                elif value == 'False':
                    row[column_name] = False

        yield row


### "reload" command

def reload(connection):
    """Tear down and recreate the database."""

    print('Dropping tables...')
    catdex.db.TableBase.metadata.drop_all(connection)

    load(connection)


### "dump" command

def dump(connection):
    """Update the CSVs from the contents of the database."""

    print('Dumping tables...')
    for table in catdex.db.TableBase.metadata.tables.values():
        print('  - {}...'.format(table.name))
        dump_table(table, connection)

def dump_table(table, connection):
    """Dump a table into a CSV."""

    headers = [column.name for column in table.columns]
    primary_key = table.primary_key.columns
    rows = connection.execute(table.select().order_by(*primary_key))

    csv_path = 'db/data/{}.csv'.format(table.name)
    csv_path = pkg_resources.resource_filename('catdex', csv_path)

    with open(csv_path, 'w', encoding='UTF-8', newline='') as table_csv:
        writer = csv.writer(table_csv, lineterminator='\n')
        writer.writerow(headers)
        writer.writerows(rows)


### main method stuff

def make_parser():
    """Create and return a parser for command-line arguments."""

    # Global stuff
    parser = argparse.ArgumentParser(description='Manage the catdex database.')
    parser.add_argument('-s', '--sql', action='store_true',
        help='Echo all SQL queries executed.')
    parser.add_argument('database',
        help='An SQLA URI for the catdex database.')
    subparsers = parser.add_subparsers(title='commands')

    # load command
    load_parser = subparsers.add_parser('load',
        help='Create the database from scratch.')
    load_parser.set_defaults(func=load)

    # reload command
    reload_parser = subparsers.add_parser('reload',
        help='Tear down and recreate the database.')
    reload_parser.set_defaults(func=reload)

    # dump command
    dump_parser = subparsers.add_parser('dump',
        help='Update the data CSVs from the contents of the database.')
    dump_parser.set_defaults(func=dump)

    return parser

def get_engine(db_uri, echo_sql):
    """Create and return an SQLA engine."""

    engine = sqla.create_engine(db_uri, echo=echo_sql)
    catdex.db.DBSession.configure(bind=engine)
    return engine

def main(argv=None):
    """Parse arguments and run the appropriate command."""

    parser = make_parser()
    args = parser.parse_args(argv)
    engine = get_engine(args.database, args.sql)

    with engine.begin() as connection:
        args.func(connection)
