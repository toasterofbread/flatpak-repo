from argparse import ArgumentParser
import os
from os import path
import xmltodict
from bs4 import BeautifulSoup
import re
import minify_html

STATIC_CONTENT = """
<div style='display: flex; flex-direction: column; gap: 10px;'>
    <h1 id="toastbits-flatpak-repository">Toastbits Flatpak repository</h1>

    <br>
    <br>
    <h2>Installation</h2>

    <p>To add this repository to your Flatpak setup, run the following command:</p>
    <p><code>flatpak remote-add toastbits https://flatpak.toastbits.dev/index.flatpakrepo</code></p>

    <p>Alternatively, download the <a href="https://flatpak.toastbits.dev/index.flatpakrepo">repo file</a> and add it manually:</p>
    <p><code>flatpak remote-add toastbits ./index.flatpakrepo</code></p>

    <br>
    <br>
    <h2>Available packages</h2>

    <p>To install a package:</p>
    <p style="margin-bottom: 20px"><code>flatpak install &lt;&#8203;package id&gt;</code></p>
</div>
"""

def generatePackageInfoContent(info: dict) -> str:
    style = """
        <style>
            p, h1, h2, h3, h4, h5, h6 {
                margin: 0px;
            }

            .center {
                margin-top: auto;
                margin-bottom: auto;
            }
        </style>
    """

    content = style + "<div style='display: flex; gap: 10px;'>"

    id = info.get("id")
    license = info.get("project_license")
    name = info.get("name") or "(No name)"
    summary = info.get("summary") or "(No summary)"
    icon = info.get("icon")

    vcs_url = None
    for url in info.get("url") or []:
        if url["@type"] == "vcs-browser":
            vcs_url = url["#text"]
            break

    if icon is not None:
        url = icon["#text"]
        content += f"<img src='{url}' width=70 height=70 class='center'>"

    content += "<div style='display: flex; flex-direction: column; gap: 10px;'>"

    title = f"<a href='{vcs_url}'>" if (vcs_url is not None) else ""
    title += f"<h2>{name}</h2>"
    title += "</a>" if (vcs_url is not None) else ""

    content += f"""
        <div style='display: flex; gap: 10px; justify-content: center;'>
            {title}
            <h5 class='center'>id={id}</h5>
            <h5 class='center'>license={license}</h5>
        </div>
    """

    content += f"<p>{summary}</p>"

    content += "</div></div>"

    return content

def generatePackageListPageContent(package_domain: str, packages_path: str):
    page = "<div style='display: flex; flex-direction: column; gap: 20px;'>"

    for package in os.listdir(packages_path):
        manifest_path = path.join(packages_path, package, package_domain + "." + package + ".yml")
        if not path.isfile(manifest_path):
            continue

        info_path = path.join(packages_path, package, package_domain + "." + package + ".metainfo.xml")
        if not path.isfile(info_path):
            page += generatePackageInfoContent({"id": package_domain + "." + package})
            continue

        f = open(info_path, "r")
        info_content = xmltodict.parse(f.read())
        f.close()

        page += generatePackageInfoContent(info_content["component"])

    page += "</div>"

    return page

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("package_domain", type=str)
    parser.add_argument("packages_path", type=str)
    parser.add_argument("html_path", type=str)

    args = parser.parse_args()

    list_content = generatePackageListPageContent(args.package_domain, args.packages_path)

    page = f"""
    <html>
        <head>
            <title>Toastbits Flatpak repository</title>
        </head>
        <body>
            {STATIC_CONTENT}
            {list_content}
        </body>
    </html>
    """

    page = minify_html.minify(page, minify_css = True)
    page = BeautifulSoup(page, "lxml").prettify()
    r = re.compile(r'^(\s*)', re.MULTILINE)
    page = r.sub(r'\1\1\1\1', page).strip()

    f = open(args.html_path, "w")
    f.write(page)
    f.close()
