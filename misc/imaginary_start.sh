#!/usr/bin/env bash
exec /sites/imaginary/imaginary -p 8082 -cors -concurrency 20 -mount /sites/assets -enable-url-source localhost,cdn.kabbalahmedia.info,archive.kbb1.com,new-archive.kbb1.com,kabbalahmedia.info
