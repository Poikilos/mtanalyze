@echo off
REM C:\Python27\python minetestmapper.py --input "C:\games\Minetest\worlds\try7amber" --region 0 64 0 64 --output "try7amber.png"
MD chunkymap-genresults
MD chunkymapdata
cls

SET CHUNKYMAP_CHUNK_WIDTH=16
SET CHUNKYMAP_CHUNK_HEIGHT=16
SET CHUNKYMAP_CHUNK_XMIN=0
SET CHUNKYMAP_CHUNK_XMAX=15
SET CHUNKYMAP_CHUNK_ZMIN=0
SET CHUNKYMAP_CHUNK_ZMAX=15

SET CHUNKYMAP_CHUNK_LUID=x%CHUNKYMAP_CHUNK_XMIN%z%CHUNKYMAP_CHUNK_ZMIN%
SET TARGET_GENRESULT_PATH=chunkymap-genresults\chunk_%CHUNKYMAP_CHUNK_LUID%-genresult.txt
SET TARGET_IMAGE_PATH=chunkymapdata\chunk_%CHUNKYMAP_CHUNK_LUID%.png
C:\Python27\python minetestmapper.py --input "C:\games\Minetest\worlds\try7amber" --region %CHUNKYMAP_CHUNK_XMIN%:%CHUNKYMAP_CHUNK_XMAX%,%CHUNKYMAP_CHUNK_ZMIN%:%CHUNKYMAP_CHUNK_ZMAX% --output "%TARGET_IMAGE_PATH%" > "%TARGET_GENRESULT_PATH%"
REM C:\Python27\python minetestmapper.py --input "C:\games\Minetest\worlds\try7amber" --geometry %CHUNKYMAP_CHUNK_XMIN%:%CHUNKYMAP_CHUNK_ZMIN%+%CHUNKYMAP_CHUNK_WIDTH%+%CHUNKYMAP_CHUNK_HEIGHT% --output "%TARGET_IMAGE_PATH%" > "%TARGET_GENRESULT_PATH%"

REM REM C:\Python27\python minetestmapper.py --input "C:\games\Minetest\worlds\try7amber" --geometry -100:-100+16+16 --output "%TARGET_IMAGE_PATH%" > "%TARGET_GENRESULT_PATH%"

start notepad "%TARGET_GENRESULT_PATH%"
start "chunkymapimage" "%TARGET_IMAGE_PATH%"

echo To delete the test output,
pause
del "%TARGET_GENRESULT_PATH%"
del "%TARGET_IMAGE_PATH%"
