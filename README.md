# FreshFoodies

## Setup Guide
1. Clone the repo

2. Set up virtual environment
```
py -m venv venv

./venv/Scripts/activate

pip install -r requirements.txt
```

3. (IGNORE THIS STEP FOR NOW) Add FLASK_APP environment variable
```
(Windows) New-Item .flaskenv
(Mac) touch .flaskenv

echo SECRET_KEY=TEST-KEY > .flaskenv
```

3. Run development server

```
flask run
```

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