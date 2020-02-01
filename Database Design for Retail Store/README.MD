# Normalization

**What is Normalization?**

The process of organizing the columns (attributes) and tables (relations) of relational database to reduce data redundancy and improve data quality. - **Wikipedia**

**Importance Database Design**

1. Understanding thinking to why it was designed a certain way
2. Faster navigation around the database
3. More perspective to potential vulnerability and flaws
4. Easier communication with stakeholders

## Prime and Non-Prime Attributes

[Primary Key](https://searchsqlserver.techtarget.com/definition/primary-key) —> A unique value to each record. A relational database must always have one and only one primary key. Primary keys typically appear as columns in relational database tables.

[Candidate Key](https://blog.sqlauthority.com/2009/10/22/sql-server-difference-candidate-keys-primary-key-simple-words/) —> A Candidate Key can be any column or a combination of columns that can qualify as unique key in database. There can be multiple Candidate Keys in one table. 

[Functional Dependency](https://opentextbc.ca/dbdesign01/chapter/chapter-11-functional-dependencies/) —> is a relationship between two attributes, typically between the PK and other non-key attributes within a table.

[Prime Attributes](https://ashutoshtripathi.com/gate/dbms/normalization-normal-forms/prime-and-non-prime-attributes/) —> Attributes of the relation which exist in at least one of the possible candidate keys, are called prime or key attributes.

[Non-Prime Attribute](https://ashutoshtripathi.com/gate/dbms/normalization-normal-forms/prime-and-non-prime-attributes/) —> Attributes of the relation which does not exist in any of the possible candidate keys of the relation, such attributes are called non prime or non key attributes.


### First Normal Form (1NF)

> No duplicate rows and every cell contains one value.

### Second Normal Form (2NF)

> If it satisfies criteria of 1NF and every non-prime attribute of the table is dependent on the whole of every candidate key.

### Third Normal Form (3NF)

> If it satisfies 2NF and every non-prime attribute is non-transitively dependent on every candidate key.

Every non-prime attribute must provide a fact about the key the whole key and nothing but the key.

About the Key —> First Normal Form. This implies there has to be a key.

Whole Key —> Second Normal Form. Referring to every candidate keys.

Nothing but he Key —> Thirds Normal Form

# EXAMPLE

### Checking for 1NF

Check all the transactions as a count 

    SELECT COUNT(*)
    FROM transactions
    -- 3455 records

Check all transactions are distinct

    SELECT COUNT(*)
    FROM
    (
    	SELECT DISTINCT *
    	FROM TRANSACTIONS
    ) AS temporary_count
    ;
    -- 3455 records

### Checking for 2NF

Looking at the column variables we see that the  no prime attributes are not dependent on the of the whole candidate key. So there will need to be modification to split the data.

Create temporary table with customer information

    -- SEPARATE CUSTOMER-SPECFIC COLUMNS
    CREATE TABLE TMP AS
    SELECT 	customerid,
    		firstname,
    		surname,
    		shipping_state,
    		loyalty_discount
    FROM transactions;

Remove duplicates

    -- REMOVE DUPLICATES
    CREATE TABLE customers AS
    SELECT DISTINCT *
    FROM TMP;
    -- 942 records

From this we can see that only the customerid is the primary key so the remaining non prime attributes need it and meets 2NF requirements.

Drop columns from original transactions tables

    -- Drop customer specific columns in TRANSACTIONS but leave customerid field
    ALTER TABLE transactions
    DROP COLUMN firstname,
    DROP COLUMN surname,
    DROP COLUMN shipping_state,
    DROP COLUMN loyalty_discount
    
    -- Check columns
    SELECT *
    FROM transactions;

Drop TMP table for cleaning purposes

    DROP TABLE TMP;

### Checking for 3NF

Customer Table —> 3NF is confirmed because every non-prime is dependent on the customerid

    -- Check 3NF
    SELECT *
    FROM customers;
    -- 3NF Confirmed

We need to separate Item information since there are duplicates. 

    -- Check 3NF
    SELECT *
    FROM transactions;
    -- Will need to separate the Items columns but keep Item ID

Create TMP table

    -- Create TMP table
    CREATE TABLE TMP AS
    SELECT 	item,
    		description,
    		retail_price
    FROM transactions;
    -- 3455 records

Remove duplicates

    -- Create items table for distinct -- to remove duplicates
    CREATE TABLE items AS
    SELECT DISTINCT *
    FROM TMP;
    -- 126 records

Drop original rows that have been extracted from transaction table. While keeping foreign key.

    -- Drop original columns from Transactions table
    ALTER TABLE transactions
    DROP COLUMN description,
    DROP COLUMN retail_price;

Drop TMP table

    -- Drop TMP table
    DROP TABLE TMP
