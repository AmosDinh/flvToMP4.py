import os
from pathlib import Path
DEST_replace = 'LMD_Content_dest_compressed'
SOURCE_replace = 'LMD_Content_dest'

SOURCE_FOLDER = r'LMD_Content_dest'
SOURCE_FOLDER = Path(SOURCE_FOLDER)

def compress_rec(p):
    if str(p).endswith('.mp4'):
        print(str(p))
        
        dest = str(p).replace(SOURCE_replace,DEST_replace)
        command = 'ffmpeg -i "'+str(p)+'" -vcodec libx265 -crf 24 "'+str(dest)+'"'
        os.system(command)
    else:
        if not os.path.exists(str(p).replace(SOURCE_replace,DEST_replace)):
            os.mkdir(str(p).replace(SOURCE_replace,DEST_replace))
        
        for file in os.listdir(p):
            compress_rec(Path.joinpath(p,file))
    
    
compress_rec(SOURCE_FOLDER)