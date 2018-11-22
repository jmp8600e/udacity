# Project: Log Analysis

This README.md explains prerequisites which are needed before running log_analysis.py. The log_analysis.py is the file which user can run after creating SQL views outlined in next section. The log_analysis.py will answer below qestions. 

  - What are the most popular three articles of all time?
  - Who are the most popular article authors of all time?
  - On which days did more than 1% of requests lead to errors?

### Prerequisite
- Download the sql database from [here](https://d17h27t6h515a5.cloudfront.net/topher/2016/August/57b5f748_newsdata/newsdata.zip), then unzip the newsdata.sql file, to load the database, cd into the directory and run below command 
    ```sh
    psql -d news -f newsdata.sql
create following views on provided postgresql database called 'news'  

  - View#1 - creates temporary view called topthree_articles_temp. This extracts the slug name fro the URI for all '200 OK' status code and URI path contains /article*.
    ```sh
    CREATE VIEW top_articles_temp AS select SUBSTRING(path, '[^\/]+$') as slugname , count(*) as count 
    FROM log 
    WHERE status = '200 OK' and path LIKE '\/article%' 
    GROUP BY path 
    ORDER BY count DESC;
  - View#2 - creates final view which provides answer to question#1 and this will be used in log_analysis.py.
    ```sh
    CREATE VIEW top_articles AS SELECT title,count
    FROM (
        SELECT top_articles_temp.slugname,top_articles_temp.count,articles.slug,articles.title 
        FROM top_articles_temp,articles 
        WHERE top_articles_temp.slugname = articles.slug) as resultset ORDER BY count DESC;
- View#3 - this view provides answer to question#2 and this will be used in log_analysis.py.
    ```sh
    CREATE VIEW popular_authors AS SELECT name,title,count
    FROM (
        SELECT T.title, T.count, A.author, A.title AS title2, AU.id, AU.name 
        FROM top_articles AS T 
        JOIN articles A ON T.title = A.title
        JOIN authors AU ON AU.id = A.author 
        ORDER BY T.count DESC) as resultset;
 - View#4 - creates temporary view called perday_stats that is used in next view to answer final question.
    ```sh
    CREATE VIEW perday_stats AS SELECT 
        date(time) as date, count(*) as totalcount,
        count(CASE WHEN status LIKE '200%' THEN 1 END) as success,
        count(CASE WHEN status NOT ILIKE '200%' THEN 1 END) as failed
    FROM
       log
    GROUP BY date;   
- View#5 - this view provides answer to question#3 and this will be used in log_analysis.py.
    ```sh
    CREATE VIEW perday_percentfailed AS SELECT 
        to_char(date,'Mon DD, YYYY') as date,failed,totalcount,
        ROUND(failed * 100.0/totalcount,2) as percentfailed
    FROM perday_stats
    ORDER BY percentfailed DESC;     

### log_analysis.py
User can go ahead and execute this file such as "python ./log_analysis.py" and it will answers the questions outlined above. 
