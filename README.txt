To connect w/ pgAdmin:

host:127.0.0.1
port:5432
maintenance db: postgres
user: turboquant
pwd: devpassword


Regular user:
email:cg94301@gmx.com
pwd:justdoit
username:cg94301

Colors:
#fe6271
254,98,113

#2dd7ff
45,215,255

Check DB with PSQL in docker:

docker exec -ti turboquant_postgresql_1 /bin/bash
su postgres
psql turboquant

turboquant=# SELECT * FROM strategies;
SELECT * FROM strategies;
          created_on          |          updated_on           | id | user_id |  
  name     |                           execution_arn                           
------------------------------+-------------------------------+----+---------+--
-----------+-------------------------------------------------------------------
 2018-08-02 16:39:45.62873+00 | 2018-08-02 16:39:45.628761+00 |  1 |       1 | 1
-519112808 | arn:aws:states:us-west-2:188444798703:execution:tqml5:1-519112808
(1 row)


turboquant=# select * from strategies;
select * from strategies;
          created_on           |          updated_on           | id | user_id | 
   name     |                           execution_arn                           
-------------------------------+-------------------------------+----+---------+-
------------+-------------------------------------------------------------------
 2018-08-02 16:39:45.62873+00  | 2018-08-02 16:39:45.628761+00 |  1 |       1 | 
1-519112808 | arn:aws:states:us-west-2:188444798703:execution:tqml5:1-519112808
 2018-08-02 18:08:08.160145+00 | 2018-08-02 18:08:08.160174+00 |  2 |       1 | 
1-6CWZiUYh  | arn:aws:states:us-west-2:188444798703:execution:tqml5:1-6CWZiUYh
(2 rows)


Colors:

orignal light-red #fe6271 replaced by greenish #00dd99
orignal faded light-red #fe8995
