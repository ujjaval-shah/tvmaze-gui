import tkinter as tk
import ttkbootstrap as tb
import requests
from threading import Thread
import urllib.parse
# from test_data import test_data
from PIL import Image, ImageTk
from io import BytesIO
import os
from bs4 import BeautifulSoup
import json


DB_PATH = "db.json"


class MainWindow(tb.App):
    WINDOW_SIZE = (1500, 980)
    WINDOW_TITLE = "TVMaze GUI"
    WINDOW_POSITION = (200, 0)

    def __init__(self):
        super().__init__(
            title=MainWindow.WINDOW_TITLE,
            size=MainWindow.WINDOW_SIZE,
            position=MainWindow.WINDOW_POSITION
        )
        self.resizable(False, False)

        self.tb_style = tb.Style()
        self.tb_style.configure("TButton", font=("Helvetica", 15))

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        nav_bar = tb.Frame(self, bootstyle="primary")
        nav_bar.grid(row=0, column=0, sticky="nsw")

        home_button = tb.Button(
            nav_bar,
            text="Home",
            command=self.render_home_page,
            bootstyle="primary"
        )
        home_button.grid(row=0, column=0, sticky="ew", padx=10, pady=10)

        liked_shows_button = tb.Button(
            nav_bar,
            text="Liked Shows",
            command=self.render_liked_shows_page,
            bootstyle="primary"
        )
        liked_shows_button.grid(row=1, column=0, sticky="ew", padx=10, pady=10)

        self.page_container = tb.ScrolledFrame(self)
        self.page_container.grid(row=0, column=1, sticky="nsew")

        self.liked_shows = self.fetch_liked_shows()
        self.home_page = None
        self.liked_shows_page = None

        self.render_home_page()

    def fetch_liked_shows(self):
        file_path = os.path.join(os.path.dirname(__file__), DB_PATH)
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as file:
                data = json.load(file)
        else:
            data = []
            with open(file_path, "w", encoding="utf-8") as file:
                json.dump(data, file, indent=4)

        return data

    def sync_db(self):
        print(">> Syncing DB:", [(show["id"], show["name"]) for show in self.liked_shows])
        file_path = os.path.join(os.path.dirname(__file__), DB_PATH)
        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(self.liked_shows, file, indent=4)

    def like_a_show(self, show_data):
        self.liked_shows = [show_data, *self.liked_shows]
        self.sync_db()

    def unlike_a_show(self, show_id):
        self.liked_shows = [show for show in self.liked_shows if show["id"] != show_id]
        self.sync_db()

    def is_a_liked_show(self, show_id):
        return any(show["id"] == show_id for show in self.liked_shows)

    def render_home_page(self):
        if self.home_page:
            return
        if self.liked_shows_page:
            self.liked_shows_page.destroy()
            self.liked_shows_page = None
        self.home_page = HomePage(self.page_container, self)
        self.home_page.pack(fill=tk.BOTH, expand=True, padx=150)

    def render_liked_shows_page(self):
        if self.home_page:
            self.home_page.destroy()
            self.home_page = None
        if self.liked_shows_page:
            self.liked_shows_page.destroy()
        self.liked_shows_page = LikedShowsPage(self.page_container, self)
        self.liked_shows_page.pack(fill=tk.BOTH, expand=True, padx=150)


class HomePage(tb.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        self.grid_columnconfigure(0, weight=1)

        heading = tb.Label(self, text="Home Page", font=("Helvetica", 25, "bold"))
        heading.grid(row=0, column=0, columnspan=2, pady=(25, 10))

        info_label = tb.Label(
            self,
            text="You can search TV shows here.",
            font=("Helvetica", 15)
        )
        info_label.grid(row=1, column=0, columnspan=2, pady=15)

        self.search_query = tb.StringVar()
        self.search_entry = tb.Entry(self, textvariable=self.search_query,font=("Helvetica", 15))
        self.search_entry.grid(row=2, column=0, sticky="ew", padx=5, pady=15)
        self.search_entry.bind("<Return>", lambda event: self.on_search())
        self.search_entry.focus()

        self.search_btn = tb.Button(self, text="Search", command=self.on_search)
        self.search_btn.grid(row=2, column=1, sticky="ew", padx=5, pady=15)

        self.shows_list = None

    def fetch_shows(self):
        # For quick testing
        # return test_data
        query = self.search_query.get()
        base_url = "https://api.tvmaze.com/search/shows"

        response = requests.get(f"{base_url}?q={urllib.parse.quote(query)}")
        return response.json()

    def on_search(self):
        print(f">> User searched: {self.search_query.get()}")
        if self.search_query.get().strip() == "":
            return
        if self.shows_list:
            self.shows_list.destroy()
        self.shows_list = ShowsList(self, self, "Fetching results with the TVmaze API...")
        self.shows_list.grid(row=3, column=0, columnspan=2)
        Thread(target=self.fetch_and_populate_data).start()

    def fetch_and_populate_data(self):
        shows_data = self.fetch_shows()
        self.shows_list.populate_data([sh_data["show"] for sh_data in shows_data])        


class LikedShowsPage(tb.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        self.grid_columnconfigure(0, weight=1)

        heading = tb.Label(self, text="Liked Shows Page", font=("Helvetica", 25, "bold"))
        heading.grid(row=0, column=0, pady=(25, 10))

        info_label = tb.Label(
            self,
            text="Your liked shows will appear here.",
            font=("Helvetica", 15)
        )
        info_label.grid(row=1, column=0, pady=15)

        separator = tb.Separator(self, orient="horizontal")
        separator.grid(row=2, column=0, sticky="ew", pady=5)

        self.shows_list = None

        self.populate_data()

    def populate_data(self):
        self.shows_list = ShowsList(self, self, "Fetching data from database...")
        self.shows_list.grid(row=3, column=0)
        self.shows_list.populate_data(self.controller.liked_shows)


class ShowsList(tb.Frame):
    def __init__(self, parent, controller, initial_status):
        super().__init__(parent)
        self.controller = controller

        self.columnconfigure(0, weight=1)

        self.status = tb.Label(self, text=initial_status, font=("Helvetica", 15))
        self.status.grid(row=0, column=0, pady=40)

        # Save tk_image references
        # Don't let Python GC free the image
        self.tk_images = []

    def populate_data(self, data):
        self.status.config(text=f"{len(data)} result(s) found.")
        for i, show_data in enumerate(data):
            self.populate_a_show(i, show_data)

    def populate_a_show(self, i, show_data):
        show = ShowCard(self, self, show_data)
        show.grid(row=i+1, column=0, sticky="ew", pady=20)


class ShowCard(tb.Frame):
    def __init__(self, parent, controller, data):
        super().__init__(parent)
        self.controller = controller
        self.data = data

        self.grid_columnconfigure(2, weight=1)

        if data["image"]:
            Thread(target=lambda: self.load_image(data["image"]["medium"])).start()
        else:
            Thread(target=self.load_default_image).start()

        heading = tb.Label(self, text=data["name"], font=("Helvetica", 15, "bold"))
        heading.grid(row=0, column=1, columnspan=2, sticky="nw")

        subheading_text = (
            f'({data["network"]["name"] if data["network"] else data["webChannel"]["name"]}, '
            f'{data["premiered"][:4]}-'
            f'{data["ended"][:4] if data["status"] == "Ended" else "Now"})'
        )
        subheading = tb.Label(self, text=subheading_text, font=("Helvetica", 12))
        subheading.grid(row=1, column=1, sticky="nw", columnspan=2)

        like_label = tb.Label(self, text="Liked:", font=("Helvetica", 12, "bold"))
        like_label.grid(row=2, column=1, sticky="nw")

        self.liked_state = window.is_a_liked_show(data["id"])

        self.like_btn = tb.Button(
            self,
            icon="heart-fill" if self.liked_state else "heart",
            bootstyle="primary ghost",
            command=self.on_like_click
        )
        self.like_btn.grid(row=2, column=2, sticky="nw", ipadx=0, ipady=0)

        fields = [
            ("Rating:", data["rating"]["average"] if data["rating"]["average"] else "(Not enough votes)"),
            ("Runtime:", f'{data["runtime"]} minutes' if data["runtime"] else "-"),
            ("Genres:", ", ".join(data["genres"])),
            ("Status:", data["status"]),
            (
                "Summary:", 
                BeautifulSoup(data["summary"], "html.parser").get_text(" ", strip=True) if data["summary"] else "-"
            ),
        ]

        for row, (key, value) in enumerate(fields):
            key_label = tb.Label(self, text=key, font=("Helvetica", 12, "bold"))
            key_label.grid(row=row+3, column=1, sticky="nw")

            value_label = tb.Label(
                self, text=value,
                wraplength=600, justify="left",
                font=("Helvetica", 12)
            )
            value_label.grid(row=row+3, column=2, sticky="nw")

    def display_image(self, tk_image):
        image_label = tb.Label(self, image=tk_image)
        image_label.grid(row=0, column=0, sticky="n", rowspan=10, padx=(0, 10))
        # save tk_image reference
        self.controller.tk_images.append(tk_image)

    def load_default_image(self):
        default_img = os.path.join(os.path.dirname(__file__), "assets", "default-image.png")
        tk_image = ImageTk.PhotoImage(Image.open(default_img))
        self.display_image(tk_image)

    def load_image(self, img_url):
        response = requests.get(img_url)
        tk_image = ImageTk.PhotoImage(Image.open(BytesIO(response.content))) 
        self.display_image(tk_image)

    def on_like_click(self):
        print(">> Like button clicked:", self.data["name"])
        if self.liked_state:
            self.liked_state = False
            window.unlike_a_show(self.data["id"])
        else:
            self.liked_state = True
            window.like_a_show(self.data)
        self.like_btn.config(icon="heart-fill" if self.liked_state else "heart")


if __name__ == "__main__":
    window = MainWindow()
    window.mainloop()