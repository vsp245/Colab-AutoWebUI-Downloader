
# an example of catalog
CATALOG = {

    "models":{# <== "label name", you can add your own like this
        
        "sd1.4":{ # <== "file name", displayed in the dropdown menu
            "link": "https://huggingface.co/CompVis/stable-diffusion-v-1-4-original/resolve/main/sd-v1-4.ckpt",
        },
        
        "Analog Diffusion":{
            "link": "1344", # <== in the "link" field, you can specify any links that the script understands
        },
        
        "stable diffusion v1.5":{
            "link": "https://huggingface.co/runwayml/stable-diffusion-v1-5/resolve/main/v1-5-pruned-emaonly.ckpt", # <== in the link field, you can specify any links that the script understands
            "add": "ft-mse-840000-ema-pruned", # <== "add" is what to download along with the main link
        },
        
    },
    
    
    "other":{
        
        "ft-mse-840000-ema-pruned":{
            "link": "https://huggingface.co/stabilityai/sd-vae-ft-mse-original/resolve/main/vae-ft-mse-840000-ema-pruned.ckpt",
            "dst": "vae", # <== "dst" is where to save the file in "auto" mode
        },
        
    },
    
    
    "for merge": {
        
        "set for merge №1": {
            "add": "1344, sd1.4", # <== "add" can be link or "file name" from this CATALOG, comma delimiter
        },
        
    },
}


# next, all paths that are used in the script
# you can add any path here, respecting the python dictionary markup
PATHS={
"google drive mount" : "/content/drive",
"google drive"  :{
        "gd root"    : "/MyDrive",
        "some dir"   : "/MyDrive/some_dir",
},
"webui images"  :{
        "txt2img"    : "/outputs/txt2img-images",
        "img2img"    : "/outputs/img2img-images",
        "extras"     : "/outputs/extras-images",
        "txt2img-gr" : "/outputs/txt2img-grids",
        "img2img-gr" : "/outputs/img2img-grids",
        "log-images" : "/log/images",
},
"webui files"   :{
        "root"       : "", # don't change it
        "models"     : "/models/Stable-diffusion",
        "vae"        : "/models/VAE",
        "lora"       : "/models/Lora",
        "hypernet"   : "/models/hypernetworks",
        "text.inv."  : "/embeddings",
        "wildcards"  : "/extensions/stable-diffusion-webui-wildcards/wildcards",
},}


# next, is how the script understands civitai.com file types
# needed only for "auto" save path detection
# you can add your own in lowercase
# "civitai type on left" : "script type ('webui files') on right"
civitai_type_map = {
"pruned model"     : "models",
"model"            : "models",
"vae"              : "vae",
"checkpoint"       : "models",
"textualinversion" : "text.inv.",
"hypernetwork"     : "hypernet",
"lora"             : "lora",
"locon"            : "lora",
"wildcards"        : "wildcards",
}

# only these files are seen by the script
EXT = (".ckpt", ".safetensors", ".pt", ".yaml")
IMG = (".png", ".txt", ".jpg")


if 'do_once' not in dir():
    do_once = None
    !pip install --upgrade --no-cache-dir gdown
    import os, re, shutil, requests, gdown
    import subprocess, shlex, contextlib # for Mega
    import ipywidgets as wgt
    from IPython.display import display, HTML
    from google.colab import drive, output, files
    if 'CATALOG' not in dir(): CATALOG = {}
    output.clear()


# ===========================
#   === WebUIDownloader ===
# ===========================

class WebUIDownloader:
    
    @classmethod
    def __init__(cls):
        cls.reg = {}
        cls.gd_PATHS = dict(("[ gdrive ] "+k, v) for k, v
                            in PATHS.get("google drive",{}).items())
        for w in os.walk(os.getcwd()):
            if w[0].endswith('/stable-diffusion-webui'):
                cls.root = w[0]
                mp = !findmnt -S 'drive' -o 'target' -n
                if mp:
                    cls.mountpoint = mp[0]
                else:
                    cls.mountpoint = PATHS["google drive mount"]
                return
        raise Exception("ERROR: can't find WebUI path, get WebUI from github first")
    
    @classmethod
    def get_files_menu(cls, gd=False):
        out = [('', None)]
        all_l = list(PATHS.get("webui files", []))
        if gd:
            all_l += list(cls.gd_PATHS)
        for lbl in all_l:
            files = cls.reg.get(lbl)
            if files is not None:
                lbl = f' {lbl} '.rjust(20+len(lbl)//2,'-').ljust(40,'-')
                out.append((lbl, None))
                for _, obj in sorted(files.items()):
                    size = f'{obj.size} mb '.ljust(10, '>') # WIP
                    out.append((f'{size} {obj.filename}', obj))
        return out
    
    @classmethod
    def upd_reg(cls, gd=False, r=None, P=PATHS.get("webui files", {})):
        r = r or cls.root
        for label, pth in P.items():
            try:
                ldir = os.listdir(r + pth)
            except:
                continue
            files = cls.reg.get(label, [])
            for filename in list(files):
                if filename not in ldir:
                    del cls.reg[label][filename]
            for new in ldir:
                if new.endswith(EXT) and new not in files:
                    WebUIDownloaderFile(r + pth, new, label).file_add()
            if type(files) is dict and not cls.reg[label]:
                del cls.reg[label]
        if gd:
            cls.upd_reg(r=cls.mountpoint, P=cls.gd_PATHS) # hook wip


class WebUIDownloaderFile(WebUIDownloader):
    ''' class for files that are already in dirs '''
    
    def __init__(self, dir, filename, label):
        self.dir = dir
        self.filename = filename
        self.label = label
        self.size = self.get_size()
    
    def file_add(self):
        self.reg.setdefault(self.label, {})[self.filename] = self
        
    def move(self, dst_label):
        old_label = self.label
        dst, self.label = self.new_dir_and_label(dst_label)
        if dst == self.dir:
            return
        os.makedirs(dst, exist_ok=True)
        shutil.move(self.dir+os.sep+self.filename,
                    dst+os.sep+self.filename)
        del self.reg[old_label][self.filename]
        if not self.reg[old_label]:
            del self.reg[old_label]
        self.dir = dst
        self.reg.setdefault(self.label, {})[self.filename] = self
        
    def copy(self, dst_label):
        dst, new_label = self.new_dir_and_label(dst_label)
        if dst == self.dir:
            return
        os.makedirs(dst, exist_ok=True)
        shutil.copy2(self.dir+os.sep+self.filename,
                    dst+os.sep+self.filename)
        new_obj = type(self)(dst, self.filename, new_label)
        self.reg.setdefault(new_label, {})[self.filename] = new_obj
        
    def new_dir_and_label(self, dst_label):
        
        # self.label point where the file should be saved for new downloaded files
        # then self.label is the dictionary key pointer
        
        if dst_label == "auto":
            # only for new downloaded files
            if self.label:
                pth = PATHS.get("webui files", {}).get(self.label)
                if pth is not None:
                    return self.root + pth, self.label
            print("> can't determine where to save")
        elif dst_label in PATHS.get("webui files", []):
            pth = PATHS["webui files"][dst_label]
            return self.root + pth, dst_label
        elif dst_label in self.gd_PATHS:
            pth = self.gd_PATHS[dst_label]
            return self.mountpoint + pth, dst_label
        return self.root, "root"
        
    def get_size(self):
        size = os.stat(self.dir+os.sep+self.filename).st_size
        return self.bytes_to_mb(size)
        
    @staticmethod
    def bytes_to_mb(file_bytes):
        size = file_bytes/1048576
        size = int(size) if size >= 1 else float(str(size)[:5])
        return size


class WebUIDownloaderImages(WebUIDownloader):
        
    @classmethod
    def copy(cls, src_label, dst_label):
            
        src = PATHS["webui images"].get(src_label)
        if src:
            src = cls.root + src
        dst = cls.gd_PATHS.get(dst_label)
        if dst:
            dst = cls.mountpoint + dst
            
        if not src or not dst:
            raise Exception(f"> wrong path\nscr: {src}\ndst: {dst}")
        if not os.path.isdir(src):
            raise Exception(f"> src error\nscr: {src}")
        
        _copy = {}
        for dir, _, files in os.walk(src):
            _p = dst + os.sep + os.path.basename(dir)
            for _f in files:
                if _f.endswith(IMG):
                    _f = os.sep + _f
                    _copy.setdefault(_p, []).append((dir+_f, _p+_f))
        for _p in sorted(_copy, reverse=True):
            os.makedirs(_p, exist_ok=True)
            for f in _copy[_p]:
                shutil.copy2(f[0], f[1])
            
        if not _copy:
            raise Exception("> files not found")
                
    @classmethod
    def zip_and_download(cls, src_label):
        src = PATHS["webui images"].get(src_label)
        if src:
            src = cls.root + src
        else:
            raise Exception(f'> wrong path\nscr: {src}')
        !zip -rq "/content/img.zip" $src
        files.download("/content/img.zip")


class WebUIDownloaderNew(WebUIDownloaderFile):
    ''' class for new downloaded files '''
    
    queue = []
    queue_done = []
    
    def __init__(self, input_):
        input_ = input_.strip()
        
        if input_ in self.queue_done:
            self.link, self.add = None, None
            return
        for k, v in CATALOG.items():
            item = v.get(input_)
            if item is not None:
                self.filename = item.get("filename")
                # self.short = input_ if input_ != self.filename else None
                self.link = item.get("link")
                self.destination = item.get("dst")
                self.add = item.get("add")
                if self.destination in PATHS.get("webui files", []):
                    self.label = self.destination
                else:
                    self.label = k
                break
        else:
            self.filename = None
            # self.short = None # wip
            self.link = input_ or None
            self.destination = None
            self.label = None
            self.add = None
        self.dir = None
        self.size = None
        self.queue_done.append(input_)
        
    def verify_filename(self, new_filename):
        ''' check name and extension of the downloaded file;
            only for files from CATALOG which have the expected name '''
        
        if self.filename is None:
            return
        if not new_filename.endswith(EXT):
            print("> Attention: not expected file extension\n"+
                  f"> File: {new_filename}\n")
        if self.filename.endswith(EXT):
            self.filename = self.filename.rsplit('.', 1)[0]
        if self.filename.lower() != new_filename.rsplit('.', 1)[0].lower():
            raise Exception(f"> filename error" +
                            f"expect: {self.filename}\nname: {new_filename}")
        
    def get_dir(self, dst=None, colab_root_check=True):
        ''' check that the file exists at the destination path
            save path to self.dir variable
            in colab getcwd() sometimes return "/root" instead of "/content" '''
        
        if dst is None:
            self.dir = os.getcwd()
            if colab_root_check:
                if (self.dir+"/").startswith("/root/"):
                    self.dir = "/content" + self.dir[5:]
        else:
            self.dir = dst
        if not os.path.isfile(self.dir + os.sep + self.filename):
            raise Exception(f"> file not found\n"+
                            f"path: {self.dir}{os.sep}{self.filename}")
        
    def download(self, dst_label, **kw):
        ''' main download method '''
        
        new_filename, size, dst = self.download_switch(self.link,
                                                       dst_label, **kw)
        if new_filename is not None:
            self.verify_filename(new_filename)
            self.filename = new_filename
            self.get_dir(dst)
            self.size = self.get_size() if size is None else size
            self.file_add()
            self.queue_done.append(self.link)
            print(f"> {self.dir}{os.sep}{self.filename}",
                  "> download done\n\n", sep="\n")
        if self.add is not None:
            self.queue.extend(self.add.split(","))
        if self.queue:
            type(self)(self.queue.pop(0)).download("auto")
        else:
            self.queue_done.clear()
        
    def download_switch(self, link, dst_label, **kw):
        ''' recognize the link and send it further for downloading '''
        
        if link is None:
            return None, None, None
        elif kw and 'type' in kw:
            return self.d_civitai(id_=link, dst_label=dst_label,
                                  forced_download=True, **kw)
        elif 1<=len(link)<=5 and link.isdigit(): # civitai id: 5 digits
            return self.d_civitai(id_=link, dst_label=dst_label)
        elif 25<=len(link)<=33 or link.startswith('https://drive.google.com/'):
            return self.d_google_drive(link, dst_label)
        elif link.startswith('https://civitai.com/'):
            return self.d_civitai(link=link, dst_label=dst_label)
        elif link.startswith('https://huggingface.co/'):
            return self.d_huggingface(link, dst_label)
        elif link.startswith('https://mega.nz/'):
            return self.d_mega(link, dst_label)
        else:
            raise Exception(f'unknown link type:\n{link}')
        
    def d_huggingface(self, link, dst_label):
        print ('\n> download from huggingface.co\n')
        dst, self.label = self.new_dir_and_label(dst_label)
        hf_token = WebUIDownloaderGUI.hf_token.value.strip()
        if not hf_token:
            print('> no Hugging Face token')
        h = {"Authorization": f"Bearer {hf_token}"}
        return self.d_requests_get_file(link, dst=dst, headers=h)
        
    def d_google_drive(self, id_, dst_label):
        print ('\n> download from google drive\n')
        dst, self.label = self.new_dir_and_label(dst_label)
        output=dst
        if output and not output.endswith(os.sep):
            output += os.sep
        if len(id_) > 33:
            tmp = re.search('[\w-]{25,33}', id_)
            if tmp is not None:
                id_ = tmp.group()
            else:
                raise Exception(f'> google drive link error:\n{id_}')
        print(f'> save to: {self.label}')
        filename = gdown.download(id=id_, output=output)
        filename = filename.rsplit(os.sep, 1)[-1]
        print()
        return filename, None, dst
        
    def d_mega(self, link, dst_label):
        print ("\n> download from mega.nz\n")
        dst, self.label = self.new_dir_and_label(dst_label)
        print(f"> save to   : {self.label}\n")
        MegaD.download(link, dst)
        type(self).upd_reg()
        print("\n")
        return None, None, None
         
    def d_civitai(self, id_=None, link=None, dst_label=None,
                        type=None, prm=None, forced_download=False):
            
        if not forced_download:
            print ('\n> download from civitai.com\n')
            
        if link is not None:
            # get civitai "model" id, 5 digits from url
            idl = re.search("(?<=/)\d{1,5}(?=/)", link)
            if idl is not None:
                idl = idl.group()
            else:
                raise Exception(f"> civitai link error:\n{link}")
            
            civitai_model = self.d_requests_get_json(
                            f"https://civitai.com/api/v1/models/{idl}")
            id_ = str(civitai_model["modelVersions"][0]["id"])
            files = civitai_model["modelVersions"][0]["files"]
            type = civitai_model["type"].lower()
            
        elif id_ is not None and not forced_download:
            civitai_file = self.d_requests_get_json(
                           f"https://civitai.com/api/v1/model-versions/{id_}")
            files = civitai_file["files"]
            type = civitai_file["model"]["type"].lower()
            
        if not forced_download and len(files) > 1:
            to_popup_menu = []
            for f in files:
                kb = f["sizeKB"]
                dst_type = f["type"].lower()
                if type and type != "checkpoint" and dst_type == "model":
                    dst_type = civitai_type_map.get(type) or "root"
                else:
                    dst_type = civitai_type_map.get(dst_type) or "root"
                to_popup_menu.append({
                    "id"    : id_,
                    "name"  : f["name"],
                    "size"  : int(kb/1024) if kb >= 1024 else round(kb/1024, 3),
                    "type"  : f["type"],
                    "params": {"type": f["type"], "format": f["format"]},
                    "dst"   : dst_type,},)
            WebUIDownloaderGUI.popup_menu(to_popup_menu)
            return None, None, None
            
        print (f"> civitai model version id : {id_}",
               f"> civitai model type       : {type}\n", sep="\n")
        if dst_label == "auto" and self.destination is None:
            dst_label = civitai_type_map.get(type) or dst_label
        dst, self.label = self.new_dir_and_label(dst_label)
        link = f"https://civitai.com/api/download/models/{id_}"
        return self.d_requests_get_file(link, dst=dst, params=prm)
        
    def d_requests_get_json(self, link):
        r = requests.get(link)
        if r.status_code != 200:
            raise Exception(f'> status code: {r.status_code}\n'+
                            str(r.content)[:150])
        return r.json()
        
    def d_requests_get_file(self, link, dst=None, headers=None, params=None):
        r = requests.get(link, headers=headers, stream=True, params=params)
        if r.status_code != 200:
            raise Exception(f"> status code: {r.status_code}\n"+
                            str(r.content)[:150])
            
        filename = r.headers.get("content-disposition")
        tmp = re.search('(?<=filename=")[^"]+', filename)
        if tmp is not None:
            filename = tmp.group()
        else:
            raise Exception("> requests > can't find filename\n"+
                            str(filename))
        if dst:
            os.makedirs(dst, exist_ok=True)
            out = dst + os.sep + filename
        else:
            out = filename
        file_bytes = int(r.headers.get("content-length"))
        size = self.bytes_to_mb(file_bytes)
            
        chunk = 10485760 # 10 mb
        tik = 100/(file_bytes/chunk) if file_bytes > chunk else 0
        progress, display_at = 0, 5
        
        print(f'> file name : {filename}', f"> save to   : {self.label}",
              f"> size      : {size} mb", sep="\n")
        with open(out, "wb") as file:
            for block in r.iter_content(chunk_size = chunk):
                if block:
                    file.write(block)
                    progress += tik
                    if progress > display_at:
                        display_at += 5
                        print(f"\r{int(progress)}%", end="")
            else:
                print('\r100%')
        return filename, size, dst


# ===========================
#       === GUI ===
# ===========================

class WebUIDownloaderGUI:

    gd_state = None
    disabled = []
    
    @classmethod
    def __init__(cls):
            
        # --- input ---
        
        cls.ui_input = []
        cls.ui_input.append(wgt.Text(description = "link:"))
        for u in CATALOG.keys():
            cls.ui_input.append(
                wgt.Dropdown(
                    options = ("",) + tuple(CATALOG[u]),
                    description = f"{u}:",)
                )
        cls.rb_input = wgt.RadioButtons(
                       options = tuple(u for u in cls.ui_input),
                       layout={'width': '25px'}
                       )
        if len(cls.ui_input) == 1:
            cls.rb_input.layout.visibility = 'hidden'
            
        cls.files = wgt.Dropdown(
                    options = WebUIDownloader.get_files_menu(),
                    value = None,
                    description = "File:"
                    )
            
        cls.images= wgt.Dropdown(
                    options = ("",) + tuple(PATHS.get("webui images", ())),
                    description = "Folder:"
                    )
            
        cls.dst_d = wgt.Dropdown(
                    options = ("auto",) + tuple(PATHS.get("webui files", ())),
                    description = "Download to:"
                    )
            
        cls.dst_m = wgt.Dropdown(
                    options = tuple(PATHS.get("webui files", ())),
                    description = "Destination:"
                    )
                
        cls.dst_i = wgt.Dropdown(
                    options = ("",) + tuple(WebUIDownloader.gd_PATHS),
                    description = "Copy to:"
                    )
                    
        cls.mega_login = wgt.Text(description = "Login:")
        cls.mega_password = wgt.Password(description = "Password:")
        cls.hf_token = wgt.Text()
            
        # --- buttons ---
            
        lyt = wgt.Layout(display           = "flex",
                         justify_content   = "center",
                         margin            = "5px 0 10px 90px")
        stl = wgt.ButtonStyle(button_color = "#e0e0e0")
         
        btn_Download    = wgt.Button(description = "Download",
                                     layout = lyt, style = stl)
        btn_Refresh     = wgt.Button(description = "Refresh files",
                                     layout = lyt, style = stl )
        btn_Move        = wgt.Button(description = "Move",
                                     layout = lyt, style = stl )
        btn_Copy        = wgt.Button(description = "Copy",
                                     layout = lyt, style = stl )
        btn_Zip         = wgt.Button(description = "Zip and download",
                                     layout = lyt, style = stl,
                                     tooltip= "Zip folder and download")
        cls.btn_M_login = wgt.Button(description = "Mega login",
                                     layout = lyt, style = {'button_color':"#e0e0e0"})
        cls.btn_M_upld  = wgt.Button(description = "Upload to Mega",
                                     layout = lyt, style = stl,
                                     tooltip= "Login to Mega first")
        cls.btn_Dwnld_p = wgt.Button(description = "Download",
                                     layout = lyt, style = stl)
        cls.btn_Copy_i  = wgt.Button(description = "Copy images",
                                     layout = lyt, style = stl,
                                     tooltip= "Google drive must be mounted")
        cls.btn_GDrive  = wgt.Button(description = "g",
                                     layout = wgt.Layout(
                                              display = "flex",
                                              justify_content = "center",
                                              margin = "5px 0 10px 10px",
                                              width = "55px"),
                                     style  = wgt.ButtonStyle(
                                              button_color = "#e0e0e0"),
                                     tooltip= "Mount Google drive" )
        
        btn_Download.on_click(cls.download_click)
        btn_Refresh.on_click(cls.reset_click)
        btn_Move.on_click(cls.move_click)
        btn_Copy.on_click(cls.copy_click)
        btn_Zip.on_click(cls.zip_and_download_click)
        cls.btn_M_login.on_click(cls.mega_login_click)
        cls.btn_M_upld.on_click(cls.mega_upload_click)
        cls.btn_Dwnld_p.on_click(cls.download_popup_click)
        cls.btn_Copy_i.on_click(cls.copy_img_click)
        cls.btn_GDrive.on_click(cls.google_drive_mount)
            
        # --- containers ---
        
        cls.to_dis  = [cls.btn_GDrive, cls.btn_Copy_i, btn_Zip,
                       cls.btn_Dwnld_p, btn_Download, btn_Refresh,
                       btn_Move, btn_Copy, cls.btn_M_login, cls.btn_M_upld]
        cls.key_hf  = wgt.Accordion(children = [cls.hf_token],
                                    selected_index = None,
                                    layout = wgt.Layout(
                                             width = "340px",
                                             margin = "15px 0 0 0"))
        
        box_dwnld  = wgt.VBox([wgt.HBox([wgt.VBox(cls.ui_input),
                                         wgt.VBox([cls.rb_input])]),
                               cls.dst_d, btn_Download, cls.key_hf])
        box_files  = wgt.VBox([wgt.HBox([btn_Refresh,cls.btn_GDrive]),
                               cls.files, cls.dst_m, btn_Move, btn_Copy])
        box_images = wgt.VBox([wgt.HBox([btn_Zip, cls.btn_GDrive]),
                               cls.images, cls.dst_i, cls.btn_Copy_i])
        box_mega   = wgt.VBox([btn_Refresh, cls.files, cls.btn_M_upld,
                               wgt.HTML(value="<br>"), cls.mega_login,
                               cls.mega_password, cls.btn_M_login])
            
        cls.key_hf.set_title(0, "Hugging Face token")
        cls.tab = wgt.Tab()
        for i, t in enumerate(("download", "files", "images", "mega")):
            cls.tab.set_title(i, t)
        cls.tab.children = [box_dwnld, box_files, box_images, box_mega]
        
        # --- add style ---
        
        stl = "{margin: 3px 0 0 5px; height: 29px; font-size: 0;}"
        cls.add_style = HTML(f"<style>.widget-radio-box label{stl}</style>")
        
        # --- init state ---
        
        cls.google_drive_state_switch()
        WebUIDownloader.upd_reg(gd=cls.gd_state)
        cls.upd_files_menu()
        if os.path.exists("/root/.megaCmd/session"):
            cls.btn_M_login.style.button_color="#80baff"
            cls.btn_M_upld.tooltip = ""
        else:
            cls.btn_M_login.style.button_color="#e0e0e0"
            cls.btn_M_upld.disabled = True
        
        
    # --- popup menu ---
    
    @classmethod
    def popup_menu(cls, files_list):
        cls.popup_files = files_list
        cls.popup_dropdown = []
        opt = ("> DO NOT DOWNLOAD <",)+tuple(PATHS.get("webui files",()))
        for f in files_list:
            tmp_info = wgt.HTML(
                        description = "File:",
                        value = f'<b>{f["name"]}</b><br>'+
                                f'size: {f["size"]} mb,  '+
                                f'civitai type: {f["type"]}',)
            val = f["dst"]
            tmp_dd   = wgt.Dropdown(
                        options = opt,
                        value = val if val in opt else "root",
                        description = "Download to:",
                        layout = wgt.Layout(margin = "0 0 40px 0"))
            display(tmp_info, tmp_dd)
            cls.popup_dropdown.append(tmp_dd)
        display(cls.btn_Dwnld_p)
        print()
        
    # --- actions ---
    
    @classmethod
    def download_click(cls, b):
        f = cls.rb_input.value.value.strip()
        if f:
            output.clear()
            cls.display()
            cls.btn_disabled(True)
            try:
                WebUIDownloaderNew(f).download(cls.dst_d.value)
            except Exception as ex:
                print(ex)
            cls.upd_files_menu()
            cls.btn_disabled(False)
        
    @classmethod
    def download_popup_click(cls, b):
        cls.btn_disabled(True)
        for i, dst in enumerate(cls.popup_dropdown):
            if dst.value == '> DO NOT DOWNLOAD <':
                continue
            f = cls.popup_files[i]
            try:
                WebUIDownloaderNew(f["id"]).download(dst.value,
                                                     prm=f["params"],
                                                     type=f["type"])
            except Exception as ex:
                print(ex)
        cls.upd_files_menu()
        cls.btn_disabled(False)

    @classmethod
    def move_click(cls, b):
        if not cls.files.value:
            return
        output.clear()
        cls.display()
        cls.btn_disabled(True)
        print ('\n> move file...')
        try:
            cls.files.value.move(cls.dst_m.value)
            print ('\n> move done')
        except Exception as e:
            print (e)
        cls.upd_files_menu()
        cls.btn_disabled(False)
        
    @classmethod
    def copy_click(cls, b):
        if not cls.files.value:
            return
        output.clear()
        cls.display()
        cls.btn_disabled(True)
        print ('\n> copy file...')
        try:
            cls.files.value.copy(cls.dst_m.value)
            print ('\n> copy done')
        except Exception as e:
            print (e)
        cls.upd_files_menu()
        cls.btn_disabled(False)
        
    @classmethod
    def copy_img_click(cls, b):
        if not cls.images.value:
            return
        cls.btn_disabled(True)
        print ('\n> img copy...')
        try:
            WebUIDownloaderImages.copy(cls.images.value, cls.dst_i.value)
            print ('\n> img copy done')
        except Exception as e:
            print (e)
        cls.btn_disabled(False)
    
    @classmethod
    def zip_and_download_click(cls, b):
        if not cls.images.value:
            return
        cls.btn_disabled(True)
        print ('\n> zip img...')
        try:
            WebUIDownloaderImages.zip_and_download(cls.images.value)
            print ('\n> zip done')
        except Exception as e:
            print (e)
        cls.btn_disabled(False)
        
    @classmethod
    def reset_click(cls, b):
        output.clear()
        cls.btn_disabled(True)
        #cls.google_drive_state_switch()
        WebUIDownloader.upd_reg(gd=cls.gd_state)
        cls.upd_files_menu()
        cls.display()
        cls.btn_disabled(False)

    @classmethod
    def google_drive_mount(cls, b):
        if not os.path.isdir(WebUIDownloader.mountpoint):
            cls.btn_disabled(True)
            print ('> mount google drive')
            try:
                drive.mount(WebUIDownloader.mountpoint)
            except Exception as e:
                print(e)
            cls.btn_disabled(False)
            if not os.path.isdir(WebUIDownloader.mountpoint):
                cls.google_drive_state_switch(False)
                return
        cls.google_drive_state_switch(True)
        
    @classmethod
    def google_drive_state_switch(cls, state=None):
        if state is None:
            if os.path.isdir(WebUIDownloader.mountpoint):
                state = True
            else:
                state = False
        if state and not cls.gd_state:
            cls.gd_state = True
            cls.btn_Copy_i.disabled = False
            cls.btn_GDrive.style.button_color='#80baff'
            cls.upd_move_menu()
        elif not state and cls.gd_state != False:
            cls.gd_state = False
            cls.btn_Copy_i.disabled = True
            cls.btn_GDrive.style.button_color='#e0e0e0'
            cls.upd_move_menu()
        
    @classmethod
    def mega_login_click(cls, b):
        l = cls.mega_login.value.strip()
        p = cls.mega_password.value.strip()
        if not l or not p:
            return
            
        output.clear()
        cls.display()
        cls.btn_disabled(True, skip=cls.btn_M_upld)
        if os.path.exists("/root/.megaCmd/session"):
            print ('\n> mega relogin...\n')
            MegaD.logout()
            cls.btn_M_login.style.button_color='#e0e0e0'
            cls.btn_M_upld.disabled = True
        else:
            print ('\n> mega login...\n')
        if MegaD.login(l, p) == 0:
            cls.btn_M_login.style.button_color='#80baff'
            cls.btn_M_upld.disabled = False
            print ('\n> login done')
        cls.btn_disabled(False)
        
    @classmethod
    def mega_upload_click(cls, b):
        if not cls.files.value:
            return
        output.clear()
        cls.display()
        cls.btn_disabled(True)
        print ('\n> upload file to mega...\n')
        try:
            f = cls.files.value.dir+os.sep+cls.files.value.filename
            MegaD.upload(f)
            print ('\n> upload done')
        except Exception as e:
            print (e)
        cls.btn_disabled(False)
        
    @classmethod
    def btn_disabled(cls, state, skip=None):
        ''' disables all objects from "to_dis" list that are enabled
            skip - do not add object to the "disabled" list '''
            
        if state:
            if skip is not None:
                if not skip.disabled:
                    skip.disabled = state
            for b in cls.to_dis:
                if not b.disabled:
                    b.disabled = state
                    cls.disabled.append(b)
        else:
            for b in cls.disabled:
                b.disabled = state
            cls.disabled = []
        
    @classmethod
    def upd_files_menu(cls):
        cls.files.options = WebUIDownloader.get_files_menu(gd=cls.gd_state)
        
    @classmethod
    def upd_move_menu(cls):
        cls.dst_m.options = tuple(PATHS.get("webui files", ()))
        if cls.gd_state:
            cls.dst_m.options += tuple(WebUIDownloader.gd_PATHS)
        
    @classmethod
    def display(cls):
        display(cls.add_style, cls.tab)


# ===========================
#       === Mega ===
# ===========================

class MegaD:
    ''' thanks for this part to: github.com/menukaonline '''
        
    @classmethod
    def runSh(cls, args, *, output=False, cd=None):
        if output:
            proc = subprocess.Popen(
                    shlex.split(args), stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT, cwd=cd )
            while True:
                output = proc.stdout.readline()
                if output == b"" and proc.poll() is not None:
                    return proc.returncode
                if output:
                    print(output.decode("utf-8").strip())
        return subprocess.run(shlex.split(args), cwd=cd).returncode
        
    @classmethod
    def installing(cls, pkl=False):
        if not os.path.exists("/usr/bin/mega-cmd"):
            print("Installing MEGA ...")
            cls.runSh('sudo apt-get -y update')
            cls.runSh('sudo apt-get -y install libmms0 libc-ares2 libc6 libcrypto++6 libgcc1 libmediainfo0v5 libpcre3 libpcrecpp0v5 libssl1.1 libstdc++6 libzen0v5 zlib1g apt-transport-https')
            cls.runSh('sudo curl -sL -o /var/cache/apt/archives/MEGAcmd.deb https://mega.nz/linux/MEGAsync/Debian_9.0/amd64/megacmd-Debian_9.0_amd64.deb', output=True)
            cls.runSh('sudo dpkg -i /var/cache/apt/archives/MEGAcmd.deb')
            print("MEGA is installed.")
            #output.clear()
        elif pkl:
            !pkill mega-cmd
        
    @classmethod
    def logout(cls):
        cls.runSh('mega-logout', output=True)
        os.remove("/root/.megaCmd/session")
        
    @classmethod
    def login(cls, USERNAME, PASSWORD):
        cls.installing(pkl=True)
        return cls.runSh(f"mega-login {USERNAME} {PASSWORD}", output=True)

    @classmethod
    def download(cls, link, dst):
        cls.installing()
        os.makedirs(dst, exist_ok=True)
        cls.transferring(["mega-get", link, dst])
        
    @classmethod
    def upload(cls, localfile):
        cls.transferring(["mega-put", localfile])
    
    @classmethod
    def transferring(cls, cmd):
        proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                # Make all end-of-lines '\n'
                universal_newlines=True, )
        out = []
        for line in cls.unbuffered(proc):
            out.append(line)
            print('\r'+line, end='')
        print(f'\n{out[-2]}')
        
    
    @classmethod
    def unbuffered(cls, proc, stream='stdout'):
        newlines = ['\n', '\r\n', '\r']
        stream = getattr(proc, stream)
        with contextlib.closing(stream):
            while True:
                out = []
                last = stream.read(1)
                # Don't loop forever
                if last == '' and proc.poll() is not None:
                    break
                while last not in newlines:
                    # Don't loop forever
                    if last == '' and proc.poll() is not None:
                        break
                    out.append(last)
                    last = stream.read(1)
                out = ''.join(out)
                yield out
    

# ===========================
#       === Run ===
# ===========================

WebUIDownloader()
WebUIDownloaderGUI()
WebUIDownloaderGUI.display()
