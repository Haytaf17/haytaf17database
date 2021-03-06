import os
import sys

import psycopg2 as dbapi2


INIT_STATEMENTS = ["""
CREATE TABLE IF NOT EXISTS users(
  UserID 		SERIAL PRIMARY KEY,
  email 		VARCHAR(255) NOT NULL UNIQUE,
  password 		VARCHAR(255) NOT NULL,
  isAdmin 		INTEGER NOT NULL
);
"""
,"""
CREATE TABLE IF NOT EXISTS company(
	CompanyName 		VARCHAR(100) PRIMARY KEY,
    	NumOfProducts	 	INTEGER,
   	AverageScore 		NUMERIC(5,2),
	numberofevaluations	INTEGER
);
""","""
CREATE TABLE IF NOT EXISTS product(
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
CREATE TABLE IF NOT EXISTS companyaccount(
	CompanyName 		VARCHAR(100) NOT NULL,
	email 			    VARCHAR(100) NOT NULL UNIQUE,
    	password 		VARCHAR(255) NOT NULL,
	CompanyAccountID 	SERIAL PRIMARY KEY,
    	FOREIGN KEY (CompanyName) 	REFERENCES Company (CompanyName)
		ON DELETE CASCADE    ON UPDATE CASCADE
);
""","""
CREATE TABLE IF NOT EXISTS evaluation (
  EvaluationID 		SERIAL PRIMARY KEY,
  UserID 		    INTEGER ,
  ProductNo 		INTEGER ,
  Vote 			    INTEGER ,
  Comment 		    VARCHAR(200) ,
  Reply 			VARCHAR(200),
  FOREIGN KEY (UserID)	REFERENCES USERS (UserID)
    ON DELETE CASCADE,
  FOREIGN KEY (ProductNo) REFERENCES Product (ProductNo)
    ON DELETE CASCADE
);""","""INSERT INTO users(email,password,isadmin) VALUES('admin@admin.com','$pbkdf2-sha256$29000$CEGodQ6BMIZwzplzDiHk/A$M9NpnfbQ5QLipNBaJFiiVR9beI4P0p.Vk7AsFOMils8',1);""",

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
