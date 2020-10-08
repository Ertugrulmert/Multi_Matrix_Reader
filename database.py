# -*- coding: utf-8 -*-
"""
Created on Fri Oct  2 09:41:18 2020

@author: User
"""

import psycopg2

from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from  PyQt5 import QtCore

class dataBase(QtCore.QObject):
    

    """
    The class is a simple interface for accessing and manipulating PostgreSQL
    databases. 
    A database creation function is not present, the default database assigned upon 
    installation of PostgreSQL is called "postgres"

    ...


    Signals
    ---------
    could_connect : pyqtSignal(bool)
        Returns whether database connection was succesfully established.
    
    DB_inserted : pyqtSignal(bool)
        Returns whether a new list of datamatrix codes was successfully stored in the database
    
    DB_error : pyqtSignal(str)
        Returns databse error information
        
    Attributes
    ----------
    user : string
        Username to access the database
        
    password : string
        Password to access the database
        
    database_name : string
        Name of the database 
    
    connect : connection
        From Pyscopg2 documentation: Handles the connection to a PostgreSQL database instance. It encapsulates a database session.
   
    cursor : cursor
        From Pyscopg2 documentation: Allows Python code to execute PostgreSQL command in a database session.


    Methods
    -------
        
    login(self,password,database_name,user)
        Carries out the login to a database with username, password and the name of the datbase. 
        Initializes the connect and cursor.
    
    connection(self)
        Used before every database operation to open a connection to the database. 
        Uses the login information was previously obtained from login()
    
    
    close(self)
        Closes the database connection
    
    insert_list(self, table_name, data_list)
        Data saving is organized such that each day corresponds to a new 
        table. The datamatrix codes read in each session are saved in that day's table.
    
    get_data(self, table_name)
        Retrieves the data stored in a given table.
    
    table_exists(self, table_name)
        Finds out whether a table with the given name exists in the database.
    
    get_tables(self)
        Retrieves the public tables created by the user.
    
    delete_table(self, table_name)
        Deletes a table with the given name if it exists.
    
    """    
    
    
    #SIGNALS
    could_connect = QtCore.pyqtSignal(bool)
    DB_inserted = QtCore.pyqtSignal(bool)
    DB_error = QtCore.pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        #no database has been logged into yet
        self.user = ""
        self.password = ""
        self.database_name = ""
        self.connect = None
        self.cursor = None
        
        
    def login(self,password,database_name,user):
        
        """
        Carries out the login to a database with username, password and the name of the datbase. 
        Initializes the connect and cursor.
        Emits signals to notify user of the login success/failure
        
        Parameters
        ----------
        password : str

        database_name : str
            Default database name is "postgres" for PostgreSQL in general
        user : str
            Default username is "postgres" for PostgreSQL in general
        
        Returns
        -------
        None.
        """
        
        self.user = user
        self.password = password
        self.database_name = database_name
        
        # Connect to PostgreSQL database with given credentials
        
        try:           
            self.connect = psycopg2.connect(dbname=self.database_name, user=self.user, password=self.password)
            #notifies user that connection was established
            self.could_connect.emit(True)
            self.connect.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            self.cursor = self.connect.cursor()
            
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)  
            #emits signal to notify user that connection failed
            self.could_connect.emit(False)
            self.user = ""
        finally:
            self.close()
            
    def connection(self):
        """
        Used before every database operation to open a connection to the database. 
        Uses the login information was previously obtained from login()
        
        Returns
        -------
        None.
        """
        
        #if login was successfully completed
        if self.user != "":
            try:           
                self.connect = psycopg2.connect(dbname=self.database_name, user=self.user, password=self.password)
                self.connect.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
                self.cursor = self.connect.cursor()            
            except (Exception, psycopg2.DatabaseError) as error:
                #sending error signal to be displayed to user
                self.DB_error.emit(str(error))
                #closing database connection
                self.close()
            
            
    def close(self):
        """
        Closes the database connection
        Returns
        -------
        None.
        """
        if self.connect is not None:
            if self.cursor is not None:
                self.cursor.close()
            self.connect.close()
            print("Database connection is closed.")
            
    def insert_list(self, table_name, data_list):
        """
        Data saving is organized such that each day corresponds to a new 
        table. The datamatrix codes read in each session are saved in that day's table.

        Parameters
        ----------
        table_name : str
            Name of the table. Naming convenction for tables: day_dd_mm_yy
        data_list : list of str
            List of the datamatrix codes
            
        Returns
        -------
        None.
        """
        #connecting to database
        self.connection()
        
        '''
        The following GS1 DataMatrix code guidelines were taken as reference to determine expected code length:
            source: https://www.gs1.org/docs/healthcare/MC07_GS1_Datamatrix.pdf
            
            Manufacturer Product Code (GTIN) - 14 digits
            Expiry Date - 6 digits (YYMMDD)
            Batch / lot Number - up to 20 alpha-numeric characters
            Unique Serial Number (randomized) - up to 20 alphanumeric characters
            
            ----> In total a maximum of 60 characters can exist in each code.
        '''
        
        try: 
                
            # Creating the table for the current work day (or current session if system is to be changed)
            tablestring = "CREATE TABLE IF NOT EXISTS "+table_name+" (code VARCHAR(60) NOT NULL)"
            self.cursor.execute(tablestring)
            print(len(data_list))
            #inserting each list item one by one
            for data in data_list:
                
                print(data)
                self.cursor.execute("INSERT into "+table_name+" (code) VALUES (%s)",(data,))
                self.connect.commit()
            #signal to notfiy the user that the data was saved
            self.DB_inserted.emit(True)
                
        except (Exception, psycopg2.DatabaseError) as error:
                print(error)   
                #data saving error signal 
                self.DB_inserted.emit(False)
                
        finally:
            #closing database connection
            self.close()
        
    def get_data(self, table_name):
        """
        Retrieves the data in a given table

        Parameters
        ----------
        table_name : str
            Name of the table. Naming convenction for tables: day_dd_mm_yy
            
        Returns
        -------
        list of str
            list of the databse items in string format
            empty list returned if error occurs or table does not exist
        """ 
        
        #connecting to database
        self.connection()
        
        try: 
            if not self.table_exists(table_name): return []
            else:
  
                #Retrieving data
                self.cursor.execute("SELECT * from "+table_name)
                
                result = self.cursor.fetchall();
                self.close()
                #converting items from tuple to string
                result = [str(item) for item in result]
                return result
                
        except (Exception, psycopg2.DatabaseError) as error:
                print(error)  
                #sending error signal to be displayed to user
                self.DB_error.emit(str(error))
                return []
                
        finally:
            #closing database connection
            self.close()
            
            
    
    def table_exists(self, table_name):
        """
        Finds out whether a table with the given name exists in the database.

        Parameters
        ----------
        table_name : str
            name of the table to be searched for

        Returns
        -------
        bool
            whether table exists or not

        """
        if self.cursor is not None:
            #searching for the table name
            self.cursor.execute("select exists(select * from information_schema.tables where table_name=%s)", (table_name,))
            return self.cursor.fetchone()[0]
        else: return False
        
    def get_tables(self):
        """
        Retrieves the public tables created by the user.

        Returns
        -------
        list of string
            list of the table names in the database

        """
        
        #connecting to database
        self.connection()
        
        try:
            #retrieving all table names
            self.cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
            database_list = self.cursor.fetchall()
            
            #closing database connection
            self.close()
            
            return database_list
        
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)     
            #sending error signal to be displayed to user
            self.DB_error.emit(str(error))
            return []
                
        finally:
            #closing database connection
            self.close()
            
    
    def delete_table(self, table_name):
        """
        Deletes a table with the given name if it exists.

        Parameters
        ----------
        table_name : str
            Name of the table to be deleted

        Returns
        -------
        None

        """
        #connecting to database
        self.connection()
        try:
            #deleting table with given name
            self.cursor.execute('DROP TABLE "'+table_name+'";') 
            
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)     
            #sending error signal to be displayed to user
            self.DB_error.emit(str(error))
                
        finally:
            #closing database connection
            self.close()
        
        