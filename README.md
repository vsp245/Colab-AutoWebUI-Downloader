<h1>What is it and how to use it?</h1>
This is the Python script of a simple file manager with GUI; working with "AUTO111 SD WebUI" in the Google Colab environment.
<br><br>

Usage:
<ol>
<li>Clone "AUTO111 SD WebUI" from github:</li>
<span>
<ul>
!git clone <a href="#!">https://github.com/AUTOMATIC1111/stable-diffusion-webui</a><br>
%cd stable-diffusion-webui
</ul>
</span>
<li>Then copy\past the full content from "<b>Colab_AutoWebUI_Downloader.ipynb</b>" to any cell in your Colab sheet and run this cell.</li>
</ol>

<h1>What can it do?</h1>

<b>Downloading files from</b>
<ul>
<li>Google Drive</li>
<li>HuggingFace</li>
<li>Civitai</li>
<li>Mega</li>
</ul>

<b>Uploading files to</b>
<ul>
<li>Google Drive</li>
<li>Mega</li>
</ul>

<b>File Catalog</b>
<ul>
<li>You can list all your files and models links, group them for flexible access.</li>
</ul>

<b>File Manager</b>
<ul>
<li>Copying\Moving files within "AUTO111 SD WebUI" and Google Drive.</li>
</ul>

<b>Download Images</b>
<ul>
<li>A standard feature that just has to be here.</li>
<li>Pack all images from a specific folder and download using a browser.</li>
<li>Copy images to Google Drive.</li>
</ul>
<br>
<h1>Link types</h1>
Format of the links that the script understands.
<br><br>

<b>Google Drive</b>
<ul>
<li>link    : https<i></i>://drive.google.com/file/d/xxxxxxxx-33characters-xxxxxxxxxxx/</li>
<li>file id : xxxxxxxx-33characters-xxxxxxxxxxx</li>
</ul>

<b>HuggingFace</b>
<ul>
<li>link    : https<i></i>://huggingface.co/CompVis/stable-diffusion-v-1-4-original/resolve/main/sd-v1-4.ckpt</li>
</ul>

<b>Civitai</b>
<ul>
<li>link    : https<i></i>://civitai.com/models/12345/some-name-here</li>
<p><ul>The latest available "model version" will be downloaded.</ul></p>
<li>model version    : 54321</li>
<p><ul>This is the number that appears when you hover over the "Download" button on the model page.</ul></p>
</ul>

<b>Mega</b>
<ul>
<li>link    : https<i></i>://mega.nz/file/xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx</li>
</ul>
<br>

<h1>Other stuff</h1>

The main interface and features of the script are quite obvious. There are only two things that needs to be explained is the catalog structure and "download to auto" mode.
<br><br>
<h3>Catalog</h3>
The Catalog is a regular Python dictionary, and its looks like this:

```Python 
CATALOG = {

    "models":{ # <== "label"
        
        "Analog Diffusion":{ # <== "file name"
            "link": "1344", },
        
        "stable diffusion v1.5":{ # <== "file name"
            "link": "https://huggingface.co/runwayml/stable-diffusion-v1-5/resolve/main/v1-5-pruned-emaonly.ckpt",
            "add": "ft-mse-840000-ema-pruned",},
    },
    
    "other":{ # <== "label"
    
        "ft-mse-840000-ema-pruned":{ # <== "file name"
            "link": "https://huggingface.co/stabilityai/sd-vae-ft-mse-original/resolve/main/vae-ft-mse-840000-ema-pruned.ckpt",
            "dst": "vae", },
    },
    
    "for merge": { # <== "label"
    
        "set for merge №1": { # <== "file name"
            "add": "1344, stable diffusion v1.5",}, # download model from civitai and "stable diffusion v1.5" from "models" label
    },
}
```

As you can see, the Catalog consists of <b>Labels</b>, which consist of <b>File Names</b>, which can contain three types of fields: <b>"link"</b>, <b>"add"</b> and <b>"dst"</b> 
<br>

Graphically it looks like this:
<br><br>
![s_001](/scr/s_001.jpg)

<b>Labels</b><br>
Label is a dropdown menu. Feel free to add your Labels and they will also appear in the interface.
<ul><p>
<b>File Names</b><br>
This is items in the dropdown menu.
<p></p>
<ul>
<b>"link"</b><br>
In this field you can specify any link that the script understands.
</p><p>
<b>"add"</b><br>
In this field you can specify other <b>File Names</b> from Catalog or <b>links</b> that will be downloaded next in turn automatically. Must be separated by commas.
</p>
<b>"dst"</b><br>
In this field you can specify where to save file in "auto" mode, explained below.
<br>
</ul>
</ul>


<br><br>
<h3>Download to auto</h3>
Relative paths to different WebUI folders are written inside the script and have the <b>short name</b> abbreviation.
<br>You can easily add your own paths; for now the following <b>short names</b> available:<br>

```Python 
models, vae, lora, hypernet, wildcards, text.inv.
```

When you download a file, you can choose from paths <b>short names</b> where to save it. Or you can leave the "auto" option. In this case, the following logic will be used:
<ul>
<p>If the <b>Label</b> matches the path <b>short name</b>, then everything from this <b>Label</b> will be saved to this path.<br>
For example, if the <b>Label</b> is named "<b>models</b>" and "auto" mode selected, then all files downloaded from this <b>Label</b> will be saved to "<b>/models/Stable-diffusion</b>" path. If the <b>Label</b> is named "<b>text.inv.</b>" and "auto" mode selected, then all files downloaded from this <b>Label</b> will be saved to "<b>/embeddings</b>" path.</p>
<p>If the file is downloaded from civitai.com, and "auto" mode selected, then the script will first try to determine saving path according to civitai classification.</p>
<p>If the file has "dst" field specified, and "auto" mode selected, then all previous methods will be ignored and the file will be saved in corresponding path.
 <br>For example, whith "dst":"<b>text.inv.</b>" and "auto" mode selected, the file will be saved to "<b>/embeddings</b>" path.</p>
<p>If the path could not be determined, the file will be saved to the WebUI root folder, from where you can easily move it to where you need it using the file manager.</p>
</ul>
In other words "auto" mode is: "dst" field >> civitai classification >> Label name
