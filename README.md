# transaction

## Requirements
* Python 3.11
* MySQL 8.0.27
* FastAPI


## To run:

Create DB on MySQL and add credentials to config.py
```sh
SQLALCHEMY_DATABASE_URI = "mysql+mysqlconnector://{username}:{password}@localhost/{dbname}"
```
Then run following commands

```sh
$ pip install -r requirements.txt
$ python3 main.py
```

Go **http://127.0.0.1:8000** on your browser. 

## Swagger

Go **http://127.0.0.1:8000/docs** on your browser. 

## API Docs

Go **http://127.0.0.1:8000/redoc** on your browser. 


## Postman Collection to test all APIs

Go file (transaction-postman-collection.json) and import to postman 

## Features

* Register
* Login
* Cards
  * List cards
  * Add card
  * Update card
  * Delete card
* Transaction
  * Perform transaction
  * Search transaction
  * Get transaction statistics