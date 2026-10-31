CREATE DATABASE IF NOT EXISTS elanco;
USE elanco;


CREATE TABLE species ( 
  name VARCHAR(100) NOT NULL,
  latin_name VARCHAR(150) NOT NULL,
  CONSTRAINT pk_name PRIMARY KEY(name)
  );
  
CREATE TABLE sightings ( 
  id VARCHAR(50) NOT NULL,
  sighted_at DATETIME NOT NULL,
  location VARCHAR(100) NOT NULL,
  species VARCHAR(100) NOT NULL,
  FOREIGN KEY (species) REFERENCES species(name),
  CONSTRAINT pk_id PRIMARY KEY(id),
  INDEX idx_date (sighted_at),
  INDEX idx_loc_date (location, sighted_at)
  );
  
  