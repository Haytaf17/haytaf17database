import os
import sys

import psycopg2 as dbapi2


INIT_STATEMENTS = ["""
CREATE TABLE users(
  UserID 		SERIAL PRIMARY KEY,
  email 		VARCHAR(255) NOT NULL UNIQUE,
  password 		VARCHAR(255) NOT NULL,
  isAdmin 		INTEGER NOT NULL
);
"""
,"""
CREATE TABLE company(
	CompanyName 		VARCHAR(100) PRIMARY KEY,
    NumOfProducts	 	INTEGER,
   	AverageScore 		NUMERIC(5,2)
);
""","""
CREATE TABLE product(
	ProductNo		SERIAL PRIMARY KEY,
   	ProductName 	VARCHAR(100) NOT NULL,
   	CompanyName		VARCHAR(100) NOT NULL,
   	Score			NUMERIC(5,2),
   	numberOfVotes	INTEGER,
   	CategoryName	VARCHAR(100),
	FOREIGN KEY (CompanyName) REFERENCES Company (CompanyName)
		ON DELETE CASCADE    ON UPDATE CASCADE
);
""","""
CREATE TABLE companyaccount(
	CompanyAccountID 	SERIAL PRIMARY KEY,
    CompanyName 		VARCHAR(100) NOT NULL,
  	email 			    VARCHAR(100) NOT NULL UNIQUE,
    password 		VARCHAR(100) NOT NULL,
    FOREIGN KEY (CompanyName) 	REFERENCES Company (CompanyName)
		ON DELETE CASCADE    ON UPDATE CASCADE
);
""","""
CREATE TABLE evaluation (
  EvaluationID 		SERAIAL PRIMARY KEY,
  UserID 		    INTEGER ,
  ProductNo 		INTEGER ,
  Vote 			    INTEGER ,
  Comment 		    VARCHAR(200) ,
  Reply 			VARCHAR(200),
  FOREIGN KEY (UserID)	REFERENCES USERS (UserID)
    ON DELETE CASCADE,
  FOREIGN KEY (ProductNo) REFERENCES Product (ProductNo)
    ON DELETE CASCADE
);""",

]


def initialize(url):
    with dbapi2.connect(url) as connection:
        cursor = connection.cursor()
        for statement in INIT_STATEMENTS:
            cursor.execute(statement)
        cursor.close()


if __name__ == "__main__":
    url = os.getenv("DATABASE_URL")
    if url is None:
        print("Usage: DATABASE_URL=url python dbinit.py", file=sys.stderr)
        sys.exit(1)
    initialize(url)
