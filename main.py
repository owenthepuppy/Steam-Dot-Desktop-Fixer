import vdf
import os
from pathlib import Path
import questionary
from pyfiglet import Figlet

library_folders = []
apps = {}

figlet = Figlet()

print(figlet.renderText("Steam .desktop Fixer"))

if not questionary.confirm(
    "This app will (probably) add a ton of files to your applications folder, you should probably back it up before continuing... (it should normally be at ~/.local/share/applications)"
).ask():
    print("(that was probably a good idea tbh)")
    exit()

DESKTOP_FOLDER = os.path.join(os.path.expanduser("~"), ".local/share/applications")

if not os.path.exists(DESKTOP_FOLDER):
    print(
        "how the heck do you not even have a .desktop folder? ur system is too crazy for me."
    )
    exit()

LIBRARY_FOLDER_VDF_LOCATION = os.path.join(
    os.path.expanduser("~"), ".local/share/Steam/config/libraryfolders.vdf"
)
LIBRARY_FOLDER_VDF_LOCATION = (
    questionary.text(
        "Please enter the location of the steam libraryfolders.vdf file (nothing or default should work for normal installations, not flatpak):",
        default=LIBRARY_FOLDER_VDF_LOCATION,
    ).ask()
    or LIBRARY_FOLDER_VDF_LOCATION
)

if not os.path.exists(LIBRARY_FOLDER_VDF_LOCATION):
    print(
        "The file location you gave does not exist, exiting... (searching on google for the location on a flatpak install may help you)"
    )
    exit()

IGNORE_APPS = [
    lambda app: "steam" in app["name"].lower(),
    lambda app: "proton" in app["name"].lower(),
    lambda app: "dedicated server" in app["name"].lower(),
    lambda app: "soundtrack" in app["name"].lower(),
    lambda app: "runtime" in app["name"].lower(),
    lambda app: "steamvr" in app["name"].lower(),
    lambda app: "tool" in app["name"].lower(),
    lambda app: "authoring" in app["name"].lower(),
    lambda app: "sdk" in app["name"].lower(),
    lambda app: "are you ready for valve index?" in app["name"].lower(),
]

print("Generating apps list...")

library_folders_vdf = vdf.load(open(LIBRARY_FOLDER_VDF_LOCATION, "r"))

for steam_library_info in library_folders_vdf["libraryfolders"].values():
    if isinstance(steam_library_info, dict):
        library_folders.append(steam_library_info["path"])

for steam_library in library_folders:
    steamapps_dir = os.path.join(steam_library, "steamapps")
    for file in os.listdir(steamapps_dir):
        if Path(file).suffix == ".acf" and file.startswith("appmanifest_"):
            app_manifest = vdf.load(open(os.path.join(steamapps_dir, file)))
            app_info = app_manifest["AppState"]
            apps.update({app_info["appid"]: app_info["name"]})

print("Done...")

choices = []
for id, name in apps.items():
    app_dict = {"id": id, "name": name}
    if any(rule(app_dict) for rule in IGNORE_APPS):
        choices.append(questionary.Choice(name, value=app_dict, checked=False))
    else:
        choices.insert(0, questionary.Choice(name, value=app_dict, checked=True))


selected_apps = questionary.checkbox(
    "Please select the games you want to add...", choices
).ask()

if any(
    app["name"] + ".desktop" not in os.listdir(DESKTOP_FOLDER) for app in selected_apps
):
    print("Creating .desktop files...")
    for app in selected_apps:
        name = app["name"]
        id = app["id"]
        desktop_name = name + ".desktop"
        if not desktop_name in os.listdir(DESKTOP_FOLDER):
            with open(os.path.join(DESKTOP_FOLDER, desktop_name), "w") as f:
                f.write(f"""[Desktop Entry]
Name={name}
Comment=Play this game on Steam
Exec=steam steam://rungameid/{id}
Icon=steam_icon_{id}
Terminal=false
Type=Application
Categories=Game;""")
    print("Successfully added all the applications (that didn't exist already)!")
else:
    print(
        "You don't have any apps that need a .desktop to be generated (if you are having a problem, it's probably something else)!"
    )
