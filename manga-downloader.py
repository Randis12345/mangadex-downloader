import requests
from os.path import isfile
from PIL import Image
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor

def get_mplus_id(d):
    s = d["attributes"]["externalUrl"]
    return s.split("/")[-1]

def get_urls_data(urls,max_workers):
    responses = []
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        responses = list(pool.map(requests.get,urls))
    
    return responses

def get_chps(manga_id,lang):
    LIMIT = 96
    URL = "https://api.mangadex.org/manga/{manga_id}/feed?limit=96&includes[]=scanlation_group&includes[]=user&order[volume]=asc&order[chapter]=asc&offset={offset}&contentRating[]=safe&contentRating[]=suggestive&contentRating[]=erotica&contentRating[]=pornographic"
    ids = []
    offset = 0
    while True:
        response = requests.get(URL.format(manga_id=manga_id,offset=offset))
        response.raise_for_status()

        jsonchps = response.json()["data"]
        if not jsonchps: break

        for x in jsonchps:
            if not x["attributes"]["translatedLanguage"] == lang: continue 
            if  x["attributes"]["externalUrl"]: ids.append({"id": get_mplus_id(x),"chp_num":x["attributes"]["chapter"],"mplus":True})
            else: ids.append({"id": x["id"],"chp_num":x["attributes"]["chapter"],"mplus":False})
        offset+=LIMIT
        
    return ids


def get_chp_imageurls_md(id):
    URL = f"https://api.mangadex.org/at-home/server/{id}?forcePort443=false"
    response = requests.get(URL)
    response.raise_for_status()

    jsonchps = response.json()

    urls = []
    for x in jsonchps["chapter"]["data"]:
        urls.append(f"{jsonchps["baseUrl"]}/data/{jsonchps["chapter"]["hash"]}/{x}")
    
    return urls


def imageurls_to_pdf(urls,path,max_workers):
    responses = get_urls_data(urls,max_workers)
    
    images = []
    for response in responses:
        img = Image.open(BytesIO(response.content))
        images.append(img)
    
    images[0].save(path, save_all=True, append_images=images[1:])


def download_chp(chp,path,prefix,overwrite,max_workers):

    if path != "" and path[-1] != "/": path+="/"
    path+=f"{prefix}-{chp["chp_num"]}.pdf"

    if (not overwrite) and isfile(path): return
     
    if chp["mplus"]:
        download_chp_mp(chp,path,max_workers)
    else:
        download_chp_md(chp,path,max_workers)


def get_chp_encimageurls_mp(chp):
    URL = "https://jumpg-webapi.tokyo-cdn.com/api/manga_viewer?chapter_id={}&split=no&img_quality=high"
    KEY_PRE = b'\x10\x90\x06\x18\xF9\x08\x2A\x80\x01'
    END_CODE = b'\x0a\x32\x22\x30'
    response = requests.get(URL.format(chp["id"]))

    def get_ind(text,start = None):
        return response.content.find(text,start)

    IMG_URL_PRE = response.content[6:15] # example: '\n\xa6\x02\n\xa3\x02\n\x97\x01' 
    
    url_ind = response.content.find(IMG_URL_PRE) + len(IMG_URL_PRE) 
    
    encimageurls = []
    
    def hex2bin(enc_key):
        out = bytearray()
        
        for i in range(0,len(enc_key),2):
            val = 0
            val+= 16 * b"0123456789abcdef".index(enc_key[i])
            val+= b"0123456789abcdef".index(enc_key[i+1])
            out.append(val)
        
        return out

    ind_end = get_ind(IMG_URL_PRE)
    running = True
    while running:
        ind_start = ind_end + len(IMG_URL_PRE)
        ind_end = get_ind(KEY_PRE,ind_start)
        
        url = response.content[ind_start:ind_end]
        
        ind_start = ind_end + len(KEY_PRE)
        ind_end = get_ind(IMG_URL_PRE,ind_start)
        if ind_end == -1: 
            ind_end = get_ind(END_CODE,ind_start)
            running = False
        
        key = hex2bin(response.content[ind_start:ind_end])
        
        encimageurls.append((url,key))
    
    return encimageurls



def download_chp_mp(chp,path,max_workers):
    URLS_ENC = get_chp_encimageurls_mp(chp)
    
    def decrypt_img(img,key):
        dec_img = bytearray(img)
        keyl = len(key)

        for i in range(len(dec_img)):
            dec_img[i] ^= key[i%keyl]
        
        return Image.open(BytesIO(dec_img))

    responses = get_urls_data([x[0] for x in URLS_ENC],max_workers)

    images = []
    for i in range(len(responses)):
        img = decrypt_img(responses[i].content,URLS_ENC[i][1])
        images.append(img)

    images[0].save(path, save_all=True, append_images=images[1:])   


def download_chp_md(chp,path,max_workers):
    image_urls = get_chp_imageurls_md(chp["id"])
    imageurls_to_pdf(image_urls,path,max_workers)
    

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description="download chapters of manga from mangadex")
    parser.add_argument("--id", type=str, help="mangadex manga id")
    parser.add_argument("--chapter", type=str, help="chapter(s) to download: START,END | CHPNUM | all")
    parser.add_argument("--path",default="" ,type=str, help="path to dir to download files, default: working directory")
    parser.add_argument("--rr",default=50 ,type=int, help="max amount of requests at one time")
    parser.add_argument("--language",default="en" ,type=str, help="language (e.g \"en\" which is default)")
    parser.add_argument("--prefix",default="chapter" ,type=str, help="prefix in pdf names, default is \"chapter\"")
    parser.add_argument('--overwrite', action='store_true',help="overwrite chapters")


    args = parser.parse_args()
    
    chps = get_chps(args.id,args.language)
    
    def download_chp_noargs(chp):
        download_chp(chp,args.path,args.prefix,args.overwrite,args.rr)
    
    if args.chapter == "all":
        for x in chps: 
            download_chp_noargs(x)

    elif "," in args.chapter:
        ind = args.chapter.index(",")
        start = float(args.chapter[:ind])
        end = float(args.chapter[ind+1:])

        for x in chps: 
            chpnum = float(x["chp_num"])
            if chpnum < start or chpnum > end: continue
            download_chp_noargs(x)
    
    else:
        for x in chps: 
            if x["chp_num"] != args.chapter: continue
            download_chp_noargs(x)
            break


