## Server Setup
```bash
$ pip install -r requirements.txt
$ export FLASK_APP=autoapp.py
$ flask run
 * Running on http://localhost:5000/
```

## Dependencies

ffmpeg is installed from sources according to
https://trac.ffmpeg.org/wiki/CompilationGuide/Centos

See ./misc/instal_ffmpeg.sh

## API
#### Request
`http://127.0.0.1:5000/uid/[uid]`
#### Response Example
##### Success
`response code: 200`
```json
[
  {
    "path": "[local relative path]",
    "size": "[size in bytes]"
  },
  {
    "path": "target/assets/sketches/2mCaPnNc/heb_o_rav_2017-10-03_lesson_bs-pticha_n1_p2_pic01.jpg",
    "size": 308258
  }
]
``` 
##### Error
`response code: 400`
```json
{"error": "[error message]"}
``` 
