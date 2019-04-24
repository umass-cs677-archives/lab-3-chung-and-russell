CREATE TABLE books(
	ID INT PRIMARY KEY NOT NULL,
	TOPIC TEXT COLLATE NOCASE NOT NULL,
 	NAME TEXT COLLATE NOCASE NOT NULL,
  	QUANTITY INT NOT NULL, 
	COST REAL NOT NULL
);

INSERT INTO books VALUES(
	1, 
	'Distributed Systems', 
	'How to get a good grade in 677 in 20 minutes a day', 
	300, 
	120
);

INSERT INTO books VALUES(
	2, 
	'Distributed Systems', 
	'RPCs for Dummies', 
	10, 
	160
);

INSERT INTO books VALUES(
	3, 
	'Graduate School', 
	'Xen and the Art of Surviving Graduate School', 
	30, 
	100
);

INSERT INTO books VALUES(
	4, 
	'Graduate School', 
	'Cooking for the Impatient Graduate Student', 
	70, 
	120
);

INSERT INTO books VALUES(
	5, 
	'Graduate School', 
	'Spring in the Pioneer Valley', 
	50, 
	210
);

INSERT INTO books VALUES(
	6, 
	'Graduate School', 
	'SWhy theory classes are so hard', 
	15, 
	75
);

INSERT INTO books VALUES(
	7, 
	'Distributed Systems', 
	'How to finish Project 3 on time', 
	15, 
	75
);



