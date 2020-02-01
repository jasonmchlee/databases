CREATE TABLE transactions (
    transactionid varchar,
    timestampsec timestamp,
    customerid varchar,
    firstname varchar,
    surname varchar,
    shipping_state varchar,
    item varchar,
    description varchar,
    retail_price float(2),
    loyalty_discount float(2)
);

COPY transactions FROM 'C:\Users\jason\Documents\SQL\Udemy\OLTP.csv' DELIMITER ',' CSV HEADER;

SELECT COUNT(*)
FROM transactions
-- 3455

SELECT COUNT(*)
FROM
(
	SELECT DISTINCT *
	FROM TRANSACTIONS
) AS temporary_count
;

-- SEPARATE CUSTOMER-SPECFIC COLUMNS
CREATE TABLE TMP AS
SELECT 	customerid,
		firstname,
		surname,
		shipping_state,
		loyalty_discount
FROM transactions;


-- REMOVE DUPLICATES
CREATE TABLE customers AS
SELECT DISTINCT *
FROM TMP;
-- 942 records


-- Drop customer specific columns in TRANSACTIONS but leave customerid field
ALTER TABLE transactions
DROP COLUMN firstname,
DROP COLUMN surname,
DROP COLUMN shipping_state,
DROP COLUMN loyalty_discount


-- Check columns
SELECT *
FROM transactions;


-- Drop TMP table
DROP TABLE TMP


-- Check 3NF
SELECT *
FROM customers;
-- 3NF Confirmed


-- Check 3NF
SELECT *
FROM transactions;
-- Will need to separate the Items columns but keep Item ID


-- Create TMP table
CREATE TABLE TMP AS
SELECT 	item,
		description,
		retail_price
FROM transactions;
-- 3455 records


-- Create items table for distinct -- to remove duplicates
CREATE TABLE items AS
SELECT DISTINCT *
FROM TMP;
-- 126 records


-- Check
SELECT *
FROM items;


-- Drop original columns from Transactions table
ALTER TABLE transactions
DROP COLUMN description,
DROP COLUMN retail_price;


-- Drop TMP table
DROP TABLE TMP


-- Check Transaction table
SELECT *
FROM transactions;