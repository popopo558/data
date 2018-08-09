# coding=utf8
import os
import MySQLdb
import time
import traceback
import requests

db_config = {
    "host": "39.108.53.90",
    "user": "root",
    "passwd": "lupin2008cn",
    "db": "dy-video"
}

RETRY = 5
RETRY_SLEEP = 5
TIMEOUT = 30

HEADERS = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'accept-encoding': 'gzip, deflate, br',
    'accept-language': 'zh-CN,zh;q=0.9',
    'pragma': 'no-cache',
    'cache-control': 'no-cache',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1',
}


def db_select(sql):
    db = MySQLdb.connect(
        host=db_config['host'],
        user=db_config['user'],
        passwd=db_config['passwd'],
        db=db_config['db'],
        charset='utf8'
    )
    cur = db.cursor()
    cur.execute(sql)

    ret = []
    for row in cur.fetchall():
        ret.append(row)
    db.close()
    return ret


def db_update(sql):
    db = MySQLdb.connect(
        host=db_config['host'],
        user=db_config['user'],
        passwd=db_config['passwd'],
        db=db_config['db'],
        charset='utf8'
    )
    cur = db.cursor()
    cur.execute(sql)
    db.commit()
    db.close()
    return None

def download(uri, medium_type, medium_url, target_folder='download/video/'):
        file_name = uri
        if medium_type == 'video':
            file_name += '.mp4'
        elif medium_type == 'image':
            file_name += '.jpg'
            file_name = file_name.replace("/", "-")
        else:
            return

        file_path = os.path.join(target_folder, file_name)
        if not os.path.isfile(file_path):
            print("Downloading %s from %s.\n" % (file_name, medium_url))
            retry_times = 0
            while retry_times < RETRY:
                try:
                    resp = requests.get(medium_url, headers=HEADERS, stream=True, timeout=TIMEOUT)
                    print resp
                    if resp.status_code == 403:
                        retry_times = RETRY
                        print("Access Denied when retrieve %s.\n" % medium_url)
                        raise Exception("Access Denied")
                    with open(file_path, 'wb') as fh:
                        for chunk in resp.iter_content(chunk_size=1024):
                            fh.write(chunk)
                    break
                except:
                    traceback.print_exc()
                    pass
                retry_times += 1
                time.sleep(RETRY_SLEEP)
            else:
                try:
                    os.remove(file_path)
                except OSError:
                    pass
                print("Failed to retrieve %s from %s.\n" % (file_name, medium_url))
        return file_name


if __name__ == '__main__':
    while True:
        videos = db_select("select * from videos where is_mark=1 and is_mark_finish=0")
        if videos:
            for video in videos:
                download_url = 'https://aweme.snssdk.com/aweme/v1/play/?{0}'
                download_params = {
                    'video_id': video[4],
                    'line': '0',
                    'ratio': '720p',
                    'media_type': '4',
                    'vr_type': '0',
                    'test_cdn': 'None',
                    'improve_bitrate': '0'
                }
                download_url = download_url.format(
                    '&'.join(
                        [key + '=' + download_params[key] for key in download_params]
                    )
                )
                filename = download(video[4], 'video', download_url)
                filename_pos = os.path.join(os.getcwd(), 'download/video/', filename) 
                outfilename_pos = os.path.join(os.getcwd(), 'download/video/out', filename) 
                titlefilename_pos = os.path.join(os.getcwd(), 'download/video/v1.srt') 

                cmd = "ffmpeg -y -i %s -vf subtitles=%s %s" % (filename_pos, titlefilename_pos, outfilename_pos)
                os.system(cmd)

                sql = "update videos SET is_mark_finish=1, video_url2='%s' WHERE id=%s" % ('download/video/out/'+filename, video[0]) 
                db_update(sql)
                print('视频%s转码完成' % filename)
                time.sleep(5)
        else:
            print('没有需要转码的视频')
        time.sleep(60)

