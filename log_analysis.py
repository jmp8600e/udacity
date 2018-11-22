#! /usr/bin/env python
# Author: Jatin M. Patel
# Please see README.md before running this file. There are prerequisitea before executing this file. 
# This file log_analysis.py contains the code for "Project: Log Analysis". Run this file using "python log_analysis.py" command.  
# The la.py will provide answers to three questions that is asked in the project. 

import psycopg2 # import module to connnect the the postgresql database
import sys # for exiting the code if error occurs in try/except block
 
DBNAME = "news" # name of the database

# This fuction executes db query against above database and returns variable called response
def get_dbinfo(DBNAME,query):
    try:
        db = psycopg2.connect(database=DBNAME)
    except psycopg2.Error as e:
        print("Unable to connect to the database --- EXITING")
        sys.exit(1)
    else:    
        c = db.cursor()
        c.execute(query)
        response =  c.fetchall()
        db.close
        return response

#this function displays answers, it takes list and also takes prefix, middle and postfix seperators 
def print_answer(response,prefix,middle,postfix):
    for val in response:
        val1 = val[0]
        val2 = str(val[1])
        print(prefix + val1 + middle + val2 + postfix)
    
# Answer to question#1  What are the most popular three articles of all time?
q1_query = "SELECT * FROM top_articles LIMIT 3;"
response = get_dbinfo(DBNAME,q1_query)
print('\nWhat are the most popular three articles of all time?\n')
print_answer(response,'\t"','" - ', ' views')

# Answer to question#2  Who are the most popular article authors of all time?
q2_query = "SELECT name, SUM (count) as count FROM popular_authors GROUP BY name ORDER BY count DESC;"
response = get_dbinfo(DBNAME,q2_query)
print('\nWho are the most popular article authors of all time?\n')
print_answer(response,'\t',' - ', ' views')

    
# Answer to question#3  On which days did more than 1% of requests lead to errors?
q3_query = "SELECT date, percentfailed FROM perday_percentfailed WHERE percentfailed > 1;"
response = get_dbinfo(DBNAME,q3_query)
print('\nOn which days did more than 1% of requests lead to errors?\n')
print_answer(response,'\t',' - ', '% errors')


    
