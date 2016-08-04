#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
   :platform: Unix
   :synopsis: Insert time diagnostic to SQLite database.

"""

import sqlite3

from constants import *


def connect(db_file):
    """
    Open connexion to a database. The database is created if not exists.

    When a database is accessed by multiple connections, and one of the processes modifies the database, the SQLite
    database is locked until that transaction is committed. The timeout parameter specifies how long the connection
    should wait for the lock to go away until raising an exception. The default for the timeout parameter is 5.0 sec.

    More info here => http://www.sqlite.org/faq.html#q5

    We increase the timeout so we are able to use sqlite3 to run manual query without stopping the script.

    By default, sqlite is in autocommit mode but the sqlite3 python module is not in autocommit mode by default. We
    don't want autocommit mode, so we leave it at its default, which will result in a plain "BEGIN" statement.
    If you want autocommit mode, then set isolation_level to None.

    :param str db_file: The destination file database to connect
    :returns: The database connector
    :rtype: *sqlite3.connect*

    """
    connexion = sqlite3.connect(db_file, TIMEOUT)
    # By name columns indexing
    connexion.row_factory = sqlite3.Row
    return connexion


def close(connexion):
    """
    Close database connexion.

    :param sqlite3.connect connexion: A ``sqlite3.connect`` instance

    """
    if is_connected(connexion):
        connexion.close()


def is_connected(connexion):
    """
    Test database connexion.

    :param sqlite3.connect connexion: A ``sqlite3.connect`` instance
    :returns: True if connexion is already established with the database
    :rtype: *boolean*

    """
    if connexion is None:
        return False
    else:
        return True


def create(db_file):
    """
    Creates the destination database.

    :param str db_file: The destination file database to create

    """
    # Open database connection
    connexion = connect(db_file)
    # Create destination table
    connexion.execute(
            """
            CREATE TABLE IF NOT EXISTS time_axis
            (id INTEGER PRIMARY KEY,
            project TEXT,
            realm TEXT,
            frequency TEXT,
            freq_units TEXT,
            variable TEXT,
            filename TEXT,
            start TEXT,
            end TEXT,
            last TEXT,
            length INT,
            file_units TEXT,
            status TEXT,
            file_ref TEXT,
            ref_units TEXT,
            calendar TEXT,
            is_instant INT,
            has_bounds INT,
            new_checksum TEXT,
            full_path TEXT,
            creation_date TEXT)
            """
    )
    # Commit changes
    connexion.commit()
    # Close database connexion
    close(connexion)


def insert(db_file, data):
    """
    Insert time diagnostic to database.

    :param str db_file: The destination file database
    :param dict data: The serialized data to persist into the database

    """
    # Open database connection
    connexion = connect(db_file)
    # Insert a new entry
    connexion.execute(
            """
            INSERT INTO time_axis VALUES
            (NULL,
            :project,
            :realm,
            :frequency,
            :funits,
            :variable,
            :filename,
            :start_date,
            :end_date,
            :last_date,
            :length,
            :time_units,
            :status,
            :ref,
            :tunits,
            :calendar,
            :is_instant,
            :has_bounds,
            :new_checksum,
            :ffp,
            :creation_date)
            """, data
    )
    # Commit changes
    connexion.commit()
    # Close database connexion
    close(connexion)
