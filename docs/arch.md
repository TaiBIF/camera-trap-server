# Arch

## Settings

Increase upload memory size, default is 2.5MB.

Each image annotation cost ~1KB, maximal number of images in a folder is 9999 (Camera SD card limit?), consider all image annotations are duplicated, double it, increase maximal number to: `1000*2*10000`

```
DATA_UPLOAD_MAX_MEMORY_SIZE = 20000000
```
