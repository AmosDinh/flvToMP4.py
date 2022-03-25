from pathlib import Path
import os 
import xml.etree.ElementTree as ET
import datetime
import uuid
import shutil
from mutagen.mp3 import MP3

class KTVIDEO:
    
    
    
    def __init__(self,folder_for_temp_files):
        self.TEMP_FOLDER = folder_for_temp_files
        
        
    
    def create_fullvideo_from_folder(self,folder,destfilepath):
        
        print("""
              \n
              \n
              \n
              \n
              ______________________________________________
              
              converting """+folder+"""
              ______________________________________________
              \n
              \n
              \n
              \n
              """)
        self.clear_tempfolder()
        
        videos_to_be_merged = []
        video_audio_timings = self.get_video_audio_timings(folder)
        
        if len(video_audio_timings['mainstream'])>1 or len(video_audio_timings['audio'])>1:
            print('error, too many mainstream or audio', video_audio_timings)
            return
        main_start = video_audio_timings['mainstream'][0]['startdt']
        
        main_end = video_audio_timings['mainstream'][0]['enddt']
        
        audio = video_audio_timings['audio'][0]
        audio_start = main_start + audio['start_timedelta']
        audio_end = audio_start + audio['duration_timedelta']
        
        print(video_audio_timings)
        first_vid = video_audio_timings['ordered_video'][0]
        first_vid_start = first_vid['startdt']
        first_vid_url = first_vid['flvpath']
        
        # this code gets the gaps between videos, and creates fillers for those gaps
        
        overlay_startend_list = [] # for overlays at the end
        
        if audio_start< first_vid_start: # need to create filler black video
            fillerpath = self.create_blackscreen_flv(first_vid_start-audio_start,first_vid_url)
            videos_to_be_merged.append(fillerpath)
            overlay_startend_list.append([self.datetime_to_timestr_from_delta(audio_start,audio_start),self.datetime_to_timestr_from_delta(audio_start,first_vid_start)])
        
        if len(video_audio_timings['ordered_video']) == 1:
            videos_to_be_merged.append(video_audio_timings['ordered_video'][0]['flvpath'])
            
        else:
            for i,video in enumerate(video_audio_timings['ordered_video'][:-1]):
                videos_to_be_merged.append(video['flvpath'])
                print(video_audio_timings['ordered_video'][i+1]['startdt'],video['enddt'],video_audio_timings['ordered_video'][i+1], video )
                timedelta = video_audio_timings['ordered_video'][i+1]['startdt']-video['enddt']
                
                if timedelta < datetime.timedelta(seconds=0):
                    print("---Videos overlap---")
                    print(video['enddt'],video_audio_timings['ordered_video'][i+1]['startdt'])
                    print(video['flvpath'],video_audio_timings['ordered_video'][i+1]['flvpath'])
                    print("--------------------")
                else:
                    
                       
                    fillerpath = self.create_blackscreen_flv(timedelta,first_vid_url)
                    videos_to_be_merged.append(fillerpath)
                    overlay_startend_list.append([self.datetime_to_timestr_from_delta(audio_start,video['enddt']),self.datetime_to_timestr_from_delta(audio_start,video_audio_timings['ordered_video'][i+1]['startdt'])])
                
        
            videos_to_be_merged.append(video_audio_timings['ordered_video'][-1]['flvpath'])
        
        timedelta = audio_end - video_audio_timings['ordered_video'][-1]['enddt']
        if timedelta>datetime.timedelta(seconds=0): # add filler video at the end, if audio is longer than video
            
            fillerpath = self.create_blackscreen_flv(timedelta,first_vid_url)
            videos_to_be_merged.append(fillerpath)
        
            overlay_startend_list.append([self.datetime_to_timestr_from_delta(audio_start,video_audio_timings['ordered_video'][-1]['enddt']),self.datetime_to_timestr_from_delta(audio_start,audio_end)])
        
        for vid in videos_to_be_merged:
            print('foll',vid)
        
        print(destfilepath)
        print(overlay_startend_list)

        # combine the normal videos and filler videos into one video
        fullvideo = self.concatenate_flv(videos_to_be_merged)
        
        
        #mp3_128k = self.mp3_change_bitrate(audio['audiopath'])
        #aac = self.mp3_to_aac(audio['audiopath'])
       
        # combine the video and mp3 / or other format / audio file
        srcpath0 = self.merge_flv_mp3(fullvideo,audio['audiopath'])
        
        # filler videos where added with concatenate_flv(fillers are the first video cut to the right length), now overlay those sections with a image,
        # why this overly complicated approach?: I experienced multiple errors trying to add simple ffmpeg-generated filler-videos 
        
        path_overlayed = srcpath0
        
        if len(overlay_startend_list) >0:
            path_overlayed = self.add_overlays(overlay_startend_list,srcpath0)
        
        # copys flv to mp4
        mp4 = self.flv_to_mp4(path_overlayed)
        
        print('fullvideo',mp4,overlay_startend_list)
        
        shutil.copyfile(mp4,destfilepath)
        
    
    
    def flv_to_mp4(self,path):
        filename = str(uuid.uuid4()) +'.mp4'
        filename = Path.joinpath(Path(self.TEMP_FOLDER),filename)
        
        command = 'ffmpeg -i '+str(path)+' -c copy -copyts -strict -1 '+str(filename)
        os.system(command)
        print(command)

        return filename
           
    def add_overlays(self,startend_list,path):
        #filename_last = path
        # for startend in startend_list:
        #     filename = str(uuid.uuid4()) +'.flv'
        #     filename = Path.joinpath(Path(self.TEMP_FOLDER),filename)
        #     #-vcodec mpeg4
            
            
        #     command = """ffmpeg -i """+filename_last+''' -i stillimage_placeholder.png -filter_complex "[1:v]scale=1800:1800 [ovrl],[0:v][ovrl]overlay=0:0:enable='between(t,'''+startend[0]+''','''+startend[1]+''')'"  -c:v libx264 -crf 0 '''+str(filename.resolve()) #libx264
        #     os.system(command)
        #     filename_last = str(filename.resolve())
            
       # ffmpeg -i C:\ffmpeg_temp\51317b05-60f9-4b13-9546-da6193676669.flv -i stillimage_placeholder.png -filter_complex "[1:v]scale=1800:1800 [ovrl],[0:v][ovrl]overlay=0:0:enable='between(t,0.0,21.406)' [temp1]; [1:v]scale=1800:1800 [ovrl],[temp1][ovrl]overlay=0:0:enable='between(t,449.105,453.406)' [out]" -map [out] -c:v libx264 -crf 0 C:\ffmpeg_temp\4fd5cdd4-7643-414a-a427-70808df85a55.flv
        filename = str(uuid.uuid4()) +'.flv'
        filename = str(uuid.uuid4()) +'.flv'
        filename = Path.joinpath(Path(self.TEMP_FOLDER),filename)
        
        overlays = ''
        last_tempname = '0:v'
        for i,startend in enumerate(startend_list):
            tempname='temp'+str(i)
            overlays +=  "[1:v]scale=1800:1800 [ovrl],["+last_tempname+"][ovrl]overlay=0:0:enable='between(t,"+startend[0]+","+startend[1]+")' ["+tempname+"];"
            last_tempname = tempname
        
        overlays = overlays[:-1]
        command = """ffmpeg -i """+path+''' -i stillimage_placeholder.png -filter_complex "'''+overlays+'''" -map ['''+last_tempname+"]  -c:v libx264 -map 0:a:? -crf 0 "+str(filename) #libx264
        print(command)
        
        os.system(command)  

        return str(filename) 
        
    def datetime_to_timestr_from_delta(self, audiostart, time):
        #dt0 = datetime.datetime(1,1,1)
        # return (dt0+(time-audiostart)).strftime('%H:%M:%S.%f')
        return str((time-audiostart).total_seconds())
        
    
    def create_blackscreen_flv(self, duration_timedelta, firstvideourl):
        
            
        print(duration_timedelta)
        dt0 = datetime.datetime(1,1,1)
        duration_timedelta = (dt0+duration_timedelta).strftime('%H:%M:%S.%f')
        filename = str(uuid.uuid4()) +'.flv'
        filename = Path.joinpath(Path(self.TEMP_FOLDER),filename)
        #command= 'ffmpeg -t '+duration_timedelta+' -f lavfi -i color=c=black:s=1600x1200:r=30 '+str(filename) # r is frames, "precision" for duration, 
        #command = 'ffmpeg -f lavfi -i color=c=black:s=1600x1200:r=25/1 -f lavfi -i anullsrc=cl=mono:r=11025 -c:v h264 -c:a pcm_s16be -t '+duration_timedelta+' '+str(filename)
        
        #command = 'ffmpeg -f lavfi -i color=c=black:s=1600x1200:r=24000/1001 -t '+duration_timedelta+' "'+str(filename)+'"'
        # command = 'ffmpeg -t '+duration_timedelta+' -s 640x480 -f rawvideo -pix_fmt rgb24 -r 25 -i'
        #placeholder = 'C:/stillimage_placeholder.png'
        #ffmpeg -i placeholder_long.flv -c copy -t 00:00:20.2 output.flv
        #command = 'ffmpeg -t '+duration_timedelta+' -f lavfi -i color=c=black:s=1600x1200 -c:v libx264 -tune stillimage -pix_fmt yuv420p '+str(filename)
        #command = 'ffmpeg -loop 1 -i '+placeholder+' -c:v libx264 -t '+duration_timedelta+' -pix_fmt yuvj422p -vf scale=320:240 '+str(filename)
        
        
        #use first video as filler
        print(firstvideourl,filename)
        command = 'ffmpeg -i "'+firstvideourl+'" -c copy -t "'+duration_timedelta+'" '+str(filename) #
        
        os.system(command)
        # filename2 = str(uuid.uuid4()) +'.flv'
        # filename2 = Path.joinpath(Path(self.TEMP_FOLDER),filename2)
        # command2 = """ffmpeg -i """+str(filename)+''' -i stillimage_placeholder.png -filter_complex "[1:v]scale=1800:1800 [ovrl],[0:v][ovrl]overlay=0:0'" '''+str(filename2) #:enable='between(t,'''+startend[0]+''','''+startend[1]+''')
        # os.system(command2)
        
        # filename2 = str(uuid.uuid4()) +'.flv'
        # filename2 = Path.joinpath(Path(self.TEMP_FOLDER),filename2)
        # #overlay video with placeholder
        # command2 = """ffmpeg -i """+str(filename)+""" -vf "drawtext=text='No video available for this section':fontcolor=white:fontsize=24:box=1:boxcolor=black@0.5:boxborderw=5:x=(w-text_w)/2:y=(h-text_h)/2" -c:a copy """+str(filename2)
        # os.system(command2)
        
        
        #command2 = 'ffmpeg -i '+str(filename)+""" -i stillimage_placeholder.png -filter_complex "[0:v][1:v] overlay=1000:1000:enable='between(t,0,20)'" -c:a copy """+str(filename2)
        
        
        # command2 = 'ffmpeg -i '+str(filename)+' -c:v libx264 -crf 19 '+str(filename).replace('.mp4','.flv')
        # os.system(command2)
        print('duration',duration_timedelta)
        
        return filename#str(filename).replace('.mp4','.flv')
    
    
    def mp3_change_bitrate(self,path):
        filename = str(uuid.uuid4()) +'.mp3'
        filename = str(Path.joinpath(Path(self.TEMP_FOLDER),filename).resolve())
        
        command ='ffmpeg -i "'+str(path)+'" -ab 32k '+filename
        os.system(command)
        return filename
    
    def mp3_to_aac(self,path):
        filename = str(uuid.uuid4()) +'.m4a'
        filename = str(Path.joinpath(Path(self.TEMP_FOLDER),filename).resolve())
        
        #command ='ffmpeg -i "'+str(path)+'" -codec:a aac '+filename
        command = 'ffmpeg -i "'+str(path)+'" -c:a aac -b:a 32k '+filename
        os.system(command)
        
        return filename
    
    def merge_flv_mp3(self,flv,mp3):
        
        filename = str(uuid.uuid4()) +'.flv'
        filename = str(Path.joinpath(Path(self.TEMP_FOLDER),filename).resolve())
        
        #fixflv = str(uuid.uuid4()) +'.flv'
        #fixflv = str(Path.joinpath(Path(self.TEMP_FOLDER),fixflv).resolve())
        
        
        #os.system('ffmpeg -n -loglevel error -i '+flv+' -vcodec libx264 -crf 28 -preset faster -tune film '+fixflv)
        #print(fixflv)
        #command = 'ffmpeg -i '+mp4+' -i '+mp3+' -c:v copy -c:a aac -map 0:v:0 -map 1:a:0 '+filename
        
        # copy mp3 to folder without spaces
        

        command = 'ffmpeg -i "'+str(Path(mp3).resolve())+'" -i "'+flv+'" -c:a aac -strict -2 -c:v libx264 -crf 18 '+filename
        os.system(command)
        print(command)
        #ffmpeg -i ffmpeg_temp/06eaff47-2d4b-4390-a4e3-0cf3901accf5.flv test4.mp4 
        return filename
    
    def clear_tempfolder(self):
            
        # delete temp folder contents
        for file in os.listdir(self.TEMP_FOLDER):
            os.remove(self.TEMP_FOLDER +'/'+file)
    
    def concatenate_flv(self,videos):

        
        #fix, ffmpeg cant deal with spaces in file / foldernames, so copy in temp folder
        copied_videos = []
        for file in videos:
            print(file)
            file = Path(file)
            new_path = Path.joinpath(Path(self.TEMP_FOLDER),file.name)
            copied_videos.append(new_path)
            if (file == new_path):# for fillervideos, already in temp_folder
                continue 
            else:
                shutil.copyfile(file, new_path)
                
            
       
        
        # new_videos = []
        
        # # flv to mp4
        
        # for file in copied_videos:
        #     unique_filename = self.TEMP_FOLDER+'/'+ str(uuid.uuid4())+'.mp4'
        #     new_videos.append(unique_filename)
        #     os.system('ffmpeg -i '+str(file.resolve())+' -c:v mpeg4 -crf 19 -strict experimental '+unique_filename)
        # # mpeg4 faster than good compression: libx264
        # #concatenate
        
        #using concat demuxer
        concat_file = Path.joinpath(Path(self.TEMP_FOLDER),'inputs.txt')
        print(concat_file)
        with open(concat_file,'w') as f:
            
            stringa = ""
            for file in copied_videos:
                fixed_file = str(file.resolve()).replace("\\","/").replace('.','') + ".flv" # fix for "Non-monotonous DTS in output stream 0:0 This may result in incorrect timestamps in the output file." error
                os.system('ffmpeg -i '+str(file.resolve()).replace("\\","/")+' -c copy '+fixed_file)
            
                stringa += "file "+fixed_file+ "\n"
                # os.system('ffmpeg -i '+file+' -map 0 -c copy -f mpegts -bsf h264_mp4toannexb '+unique_filename)
            f.write(stringa)
            
        # print(stringa)
        # stringa = stringa[:-1]
        # print('ffmpeg -i "concat:'+stringa +'" -codec copy output.mp4')
        
        unique_filename = self.TEMP_FOLDER+'/'+ str(uuid.uuid4())+'.flv'
        # os.system('ffmpeg -i "concat:'+stringa +'" -codec copy '+unique_filename)
        command = "ffmpeg -f concat -safe 0 -i "+str(concat_file.resolve())+" -c copy "+unique_filename
        os.system(command)
        print(command)
        
        
        
        return unique_filename
    
    
    def get_video_audio_timings(self,folder):
        video_audio_data_dict = {
            'audio':[],
            'mainstream':[],
            'ordered_video': []
            
            
        }
        

    
        unsorted_videodata = []
        tempaudio = []
        for file in os.listdir(folder): # get audios
            p = Path.joinpath(Path(folder),Path(file))
            if p.suffix == '.mp3':
                tempaudio.append(str(p.resolve()))

        
        for file in os.listdir(folder):
            p = Path.joinpath(Path(folder),Path(file))
            
            if file == 'mainstream.xml': # check audios
                tree = ET.parse(p)
                root = tree.getroot()
                for xmltag in root.iter(): # get audio urls
                    if xmltag.tag == "Message":
                        for xmltag2 in xmltag.iter():
                            if xmltag2.tag == 'Object':
                                for xmltag3 in xmltag2.iter():
                                    if xmltag3.tag =='fileName':
                                        if xmltag3.text and xmltag3.text.endswith('mp3'):
                                            audiourl = xmltag3.text
                                            not_in_flag = True
                                            for tempurl in tempaudio:
                                                if audiourl in tempurl:
                                                    audio = MP3(tempurl)
                                                    end = audio.info.length
                                                    video_audio_data_dict['audio'].append({'start_timedelta':datetime.timedelta(milliseconds=int(xmltag.attrib['time'])),'duration_timedelta':datetime.timedelta(milliseconds=int(end*1000)),'audiopath':tempurl})
                                                    tempaudio.remove(tempurl)
                                                    not_in_flag = False
                                                    
                                            if not_in_flag:
                                                print('audio not found',audiourl,p,folder)  
                                                return

                                                
            
            if p.suffix == '.xml':
            
                print(str(p))
                
                if file.startswith('ftcontent') or file.startswith('screenshare') or file.startswith('mainstream'):
                
                    tree = ET.parse(p)
                    root = tree.getroot()
                    
                    for element in root.iter():
                    
                        if element.tag == 'Flag' and element.text == 'video data' or \
                            file.startswith('mainstream') and element.find('fileName') != None and element.find('fileName').text != None and '.mp3' in element.find('fileName').text:
                            # we want this file, is ftcontent.xml video strucutre
                            startdt = None
                            last_time_milliseconds = 0
                            enddt = None
                            
                            for element2 in root.iter():
                                # get first message element with str attribute, get startdate from it
                                if element2.tag == 'Message' and 'time' in element2.attrib.keys() and element2.attrib['time'] == '0'\
                                    and not element2.find('Array') is None\
                                    and len(element2.find('Array').findall('String'))>0: # fix for when the first message does not have the time
                                    
                                   
                                    for msg_e in element2.iter():
                                        
                                        if msg_e.tag == 'String':
                                            startdt = msg_e.text # get start time of video
                                            
                                    
                                    
                                    if startdt is None:
                                        print('startdt in none line 243 err',file, folder)
                                        return 
                                    
                                    startdt = datetime.datetime.strptime(startdt,'%a %b %d %H:%M:%S %Y')
                                    break
                        
                            
                            for element2 in root.iter():
                                if element2.tag == "Message" and 'time' in element2.attrib.keys():
                                    last_time_milliseconds = int(element2.attrib['time'])
                                    
                            # fix: case mainstream.xml has no date entry (older version? ~ 2010 files)
                            if not startdt is None:
                                enddt = startdt + datetime.timedelta(milliseconds=last_time_milliseconds)
                            else:
                                enddt = datetime.timedelta(milliseconds=last_time_milliseconds)
                                
                            # if file.startswith('ftcontent'):
                            #     unsorted_videodata.append({'path':p,'start':startdt,'end':enddt,'duration':(enddt-startdt)})

                            if file.startswith('main'):
                                
                                    
                                video_audio_data_dict['mainstream'] = [{'path':str(p.resolve()),'startdt':startdt,'enddt':enddt}]
                            
                            elif file.startswith('ftcontent') or file.startswith('screenshare'):
                                # find correspoing flv
                                for fileflv in os.listdir(folder):
                                    if fileflv == file.replace('.xml','.flv'):
                                        flv = Path.joinpath(Path(folder),Path(fileflv))
                                        unsorted_videodata.append({'flvpath':str(flv.resolve()),'xmlpath':str(p.resolve()),'startdt':startdt,'enddt':enddt})
                                        break
            
        
        if len(tempaudio) != 0:
            print('there was an error with audio',tempaudio,p,folder) 
            return
                                        
        unsorted_videodata.sort(key=lambda x: int(x['startdt'].timestamp()*1000))
        
        video_audio_data_dict['ordered_video'] = unsorted_videodata
        print('timedelta',video_audio_data_dict['mainstream'][0]['enddt'])     
        # fix: case mainstream.xml has no date entry (older version? ~ 2010 files)
        # get startdate of first.xml,  and enddate of last.xml: map them to the endtime of mainstream
        # and thereby get date for mainstream
        # shift mainstream startdate forward so that mp3 and enddate of last.xml align
        
        if video_audio_data_dict['mainstream'][0]['startdt'] is None:
            #startdateoffirst = video_audio_data_dict['ordered_video'][0]['startdt']
            enddateoflast = video_audio_data_dict['ordered_video'][-1]['enddt']
            
            # videoduration = enddateoflast-startdateoffirst
            
            duration_ofmainstream = video_audio_data_dict['mainstream'][0]['enddt']
            
            startdate_mainstream = enddateoflast - duration_ofmainstream
            
            
            #startdt = video_audio_data_dict['ordered_video'][0]['startdt']
            #startdt -= video_audio_data_dict['audio'][0]['start_timedelta']
            video_audio_data_dict['mainstream'][0]['startdt'] = startdate_mainstream
            video_audio_data_dict['mainstream'][0]['enddt'] = enddateoflast
            
        # print(json.dumps(video_audio_data_dict,indent=4))
        print(video_audio_data_dict)
       
        return video_audio_data_dict