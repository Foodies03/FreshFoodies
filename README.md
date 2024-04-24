# FreshFoodies

## Setup Guide
1. Clone the repo

2. Set up virtual environment
```
py -m venv venv

./venv/Scripts/activate

pip install -r requirements.txt
```

3. Run development server

```
flask run
```

## Schema

1. **Fridge**

2. **Food**

## Endpoint Documentation

1. `/api/receipt/`
This endpoint takes `content-type: image/jpeg`, and a base64 encoded jpg image as `data`.

A successful response contains:
- `img_color`, the given image with bounding boxes drawn where text was found, base64 encoded.
- `img_bw`, the given image after black and white color processing which is used for text reading,
base64 encoded.
- `text`, the text read from the given image processed into black and white, as a list of strings
(each string represents text read in a single horizontal line, top down, from the given image)

The `test_client.py` file can be used to test this endpoint, it sends the `rc.jpg` file in the same
directory to the endpoint, saves the bounding box image as `test.jpg` in the same directory, and
prints the received text.

To test:
run `flask run` in the repo root in one terminal
run `py core/receipt/test_client.py` in another terminal in the repo root

Example request made in Javascript using Fetch:

```
var myHeaders = new Headers();
myHeaders.append("Content-Type", "image/jpeg");

var raw; // image encoded into a b64 string

var requestOptions = {
  method: 'POST',
  headers: myHeaders,
  body: raw,
  redirect: 'follow'
};

fetch("http://127.0.0.1:5000/api/receipt", requestOptions)
  .then(response => response.text())
  .then(result => console.log(result))
  .catch(error => console.log('error', error));
```

2. `/api/signup` -  POST

Create a new account on the app

**Request Body**
```json
{
    "email": "",
    "name": "",
}
```

3. `/api/login` -  POST

Logs into existing account

**Request Body**
```json
{
    "email": "",
}
```

**Response Body**
```json
{
    "name": "",
    "email": "",
    "foods": [],
    "fridge_ids": [],
}
```

4. `/api/me` - GET

Returns information about specified user

**Request Body**
```json
{
    "email": "",
}
```

**Response Body**
```json
{
    "name": "",
    "email": "",
    "foods": [],
    "fridge_ids": [],
}
```

5. `/api/fridge` - POST

Creates a new shared fridge

**Request Body**
```json
{
    "email": "fridge_owner_email",
    "slug": "name_of_fridge"
}
```

**Response Body**
```json
{
    "_id":"24-digit-object_id",
    "foods":[],
    "slug":"name_of_fridge",
    "users":["fridge_owner_email"]
}
```

The `_id` is important, as it will be used as the "link" to access this fridge in the other endpoints. `foods` will be initialized as an empty array

6. `/api/fridge/<id>` - GET/DELETE

Using a fridge's `_id`, we can `GET` a JSON representation of a fridge. To delete a fridge, send a DELETE request to this same endpoint with no request body

**Response Body**

```json
{
  "_id": "______",
  "foods": [{}, {}, {}, ...],
  "slug": "____",
  "users": ["user1@mail.com", "..."]
}
```

7. `/api/fridge/<id>/foods` - PUT

Send a PUT request to add or remove food(s) from a fridge. If attempting to add food(s), the request body should look as follows:

**Request Body - Add Foods**

```json
{
  "action": "add",
  "foods": [
    {"category":"vegetables","date_added":"2023-02-10T08:00:00","expiration_date":"2023-02-17T08:00:00","location":"outside","name":"onions","price":2.99,"quantity":3,"slug":"onions"},
    {},
    {}]
}
```
A `slug` is just a representation of the food's name that can be used in a URL. Usually it will be exactly the same as the name, unless the name has spaces (in which case the spaces should be dashes in the slug).

If trying to remove food(s), just pass the slugs of the foods instead and the approximate percentage that was eaten (the rest will be assumed as waste)

**Request Body - Remove Foods**
```json
{
  "action": "remove",
  "foods": ["onions", "steak"],
  "percentage_eaten": "x%"
}
```

8. `/api/fridge/<id>/foods/<slug>` - GET/PUT

 Send a GET request to get the information about a specific food in a fridge. Send a PUT request with a food object to modify the food instead.

**Response Body**
```json
{
  "category":"meat","date_added":"2023-02-10T08:00:00","expiration_date":"2023-02-17T08:00:00","location":"freezer","name":"grilled steak","price":10.99,"quantity":1,"slug":"grilled-steak"
}
```

9. `/api/fridge/<string:id>/users` - PUT

Send a PUT request to add or remove user(s) from a fridge

**Request Body**
```json
{
    "email": "",
    "name": "",
    "action": "remove/add"
}
```

10. `/api/user/entries` - GET

 Send a GET request to get the discard entries associated with a user within a specified time frame.

 **Request Body**

```json
{
    "email": "",
    "time_frame": ""
}
```

**Response Body**
```json
{
  entries: []
}
```

11. `/api/user/add_entry` - PUT

 Send a PUT request to add a used or discarded entry to a user's history once when they indicate that they use/discarded an item.

 **Request Body**

```json
{
    "email": "",
    "entry_details": {
      "food_name": "",
      "category": "",
      "entry_type: "",
      "amount": "",
      "cost_per_unit": "",
      "creation_time": ""
    }
}
```

**Response Body**
```json
{
  "new_entry": {
    "food_name": "",
    "category": "",
    "entry_type: "",
    "amount": "",
    "cost_per_unit": "",
    "creation_time": ""
  }
}
```


