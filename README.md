## Docker installation
Build the image with:
```shell
docker build -t archive-unzip:latest .
```

run the image with:
```shell
docker run --network host --env MDB_URL='postgres://user:password@host/mdb?sslmode=disable' archive-unzip
```
*Important* the MDB_URL host must accessible from within the container.      

The app should now be ready on port 5000 !

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



## License

MIT