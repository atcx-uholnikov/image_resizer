import tkinter
from tkinter import *
from tkinter import filedialog
from tkinter.filedialog import askopenfile
from tkinter import messagebox

from PIL import Image, ImageTk

import statistics

import os

import datetime

import sqlite3

import functools


number_of_img = 0 # number of current Image to show


# UPLOAD IMAGES FROM THE FOLDER
def upload():
    global filename
    file_types = [("jpg files", "*.jpg"), ("jpeg files", "*.jpeg")] # allows to upload only selected file types
    filename_new = filedialog.askopenfilename(filetypes=file_types, multiple=True) # -> tuple of paths

    if len(filename_new)>0:
        filename=filename_new
        btn_resize.config(state=ACTIVE)
    else:
        pass

    # Getting data for Tkinter UPLOADING DETAILS Label
    total_kb = sum([os.stat(x).st_size for x in filename])//1024
    over_target_size = [os.stat(x).st_size for x in filename if os.stat(x).st_size > int(entry.get()) * 1024]
    less_and_more = f"{len(over_target_size)} / {len(filename)-len(over_target_size)}"
    values_info.config(text=f"{len(filename)}\n{less_and_more}\n{total_kb} kB")

    # Deleting data from DB
    if len(filename_new)>0:
        db = sqlite3.connect("resized.db")
        cursor_db = db.cursor()
        cursor_db.execute("""DELETE FROM last_images""")
        db.commit()
        db.close()
    else:
        pass

    return filename


# RESIZE UPLOADED IMAGES
def resize(filename):

    RESIZE_TO = int(entry.get()) * 1024

    # Connect sql db
    db = sqlite3.connect("resized.db")
    cursor_db = db.cursor()

    # Create new folder named by current date and time
    current_datetime = datetime.datetime.now()
    format_datetime = current_datetime.strftime(f"resized(%y.%m.%d_%H.%M.%S)/")
    os.mkdir(format_datetime)

    for file in filename:
        size = os.path.getsize(file)

        image = Image.open(file, 'r')
        file_name = file.split("/")[-1].split(".")[0].replace(" ", "_")
        file_format = image.format

        if size < RESIZE_TO:
            new_image = image.save(f"{format_datetime}{file_name}(resized).{file_format.lower()}")
            check_size = os.stat(f"{format_datetime}{file_name}(resized).{file_format.lower()}").st_size

            cursor_db.execute(f"""INSERT INTO last_images VALUES (
                {filename.index(file)+1},
                '{format_datetime}{file_name}(resized).{file_format.lower()}',
                {size},
                {check_size},
                '{file.split('.')[-1]}',
                '{file_format.lower()}'                                
            )""")
            db.commit()

        else:
            minimum = 0
            maximum = 100

            while True:
                min_max_range = range(int(minimum), int(maximum) + 1)
                quality = int(statistics.median(min_max_range))
                new_image = image.save(f"{format_datetime}{file_name}(resized).{file_format.lower()}", quality=quality, optimize=True, progressive=True)
                check_size = os.stat(f"{format_datetime}{file_name}(resized).{file_format.lower()}").st_size

                if maximum - minimum <= 2 and check_size <= RESIZE_TO:
                    cursor_db.execute(f"""INSERT INTO last_images VALUES (
                        {filename.index(file)+1},
                        '{format_datetime}{file_name}(resized).{file_format.lower()}',
                        {size},
                        {check_size},
                        '{file.split('.')[-1]}',
                        '{file_format.lower()}'                                
                    )""")
                    db.commit()
                    break

                elif check_size > RESIZE_TO and maximum - minimum == 0:
                    messagebox.showwarning(title="NEXT IMAGE IS STILL TO BIG", message=f"Folder: {format_datetime}\nImage: {file_name}(resized)\nCurrent size: {check_size} kB\n\n PLEASE DON`T USE IMAGES GREATER THAN 2000 kB")
                    break

                elif check_size < RESIZE_TO:
                    minimum = quality

                elif check_size > RESIZE_TO:
                    maximum = quality

    global number_of_img
    number_of_img = 1

    # Starts displaying resized Images
    show(None)

    db.close()

    # Getting path to resized images for Tkinter OPEN FOLDER BUTTON
    running_path = os.path.realpath(__file__)
    split_running_path = running_path.rsplit("\\", 1)[0]
    folder_path = fr"{split_running_path}\{format_datetime[:-1]}"
    open_path = functools.partial(os.startfile, folder_path)
    open_folder.config(command=open_path, state=ACTIVE)

    # Disabling Tkinter RESIZE BUTTON
    btn_resize.config(state=DISABLED)


# SHOWS RESIZED IMAGES AND DETAILS
def show(button_press):

    global number_of_img

    db = sqlite3.connect("resized.db")
    cursor_db = db.cursor()

    # Counting total number (quantity) of uploaded images
    total_imgs_quantity = cursor_db.execute(f"""SELECT COUNT(number) FROM last_images""")
    number_of_resized_img =  total_imgs_quantity.fetchone()[0]

    # Actualization properties of Tkinter IMAGE SLIDER BUTTONS
    btn_left = tkinter.Button(slider_buttons, text="<", font=("Helvetica", 12, "bold"), width=5, height=1, command=lambda button_press="<": show(button_press))
    btn_left.grid(column=0, row=0)

    image_number = tkinter.Label(slider_buttons, text=number_of_img, width=15, height=2)
    image_number.grid(column=1, row=0)

    btn_right = tkinter.Button(slider_buttons, text=">", font=("Helvetica", 12, "bold"), width=5, height=1, command=lambda button_press=">": show(button_press))
    btn_right.grid(column=2, row=0)

    # Changing the value of the current number Image to show
    if button_press==">" and number_of_img<(number_of_resized_img):
        number_of_img = number_of_img + 1
        image_number.config(text=number_of_img)
    elif button_press=="<" and number_of_img>1:
        number_of_img = number_of_img - 1
        image_number.config(text=number_of_img)
    else:
        pass

    # Getting the number of current Image to show
    current_number = image_number.cget('text')

    # Changing status of IMAGE SLIDER BUTTONS (if the current number of Image to show out of range)
    if number_of_resized_img < 2:
        btn_right.config(state=DISABLED)
        btn_left.config(state=DISABLED)
    elif current_number == 1 and current_number<number_of_resized_img:
        btn_right.config(state=ACTIVE)
        btn_left.config(state=DISABLED)
    elif current_number > 1 and current_number<number_of_resized_img:
        btn_right.config(state=ACTIVE)
        btn_left.config(state=ACTIVE)
    elif current_number > 1 and current_number==number_of_resized_img:
        btn_right.config(state=DISABLED)
        btn_left.config(state=ACTIVE)

    # Getting the path of Image to show
    get_img = cursor_db.execute(f"""SELECT path FROM last_images WHERE number = {number_of_img}""")
    resized_img = get_img.fetchone()[0]

    # Getting an Image to show
    image = Image.open(resized_img)
    img_size = list(image.size) # -> [width (px), height (px)]

    # Customizing Image size [width (px), height (px)] according dimantions of Tkinter IMAGE TO SHOW LABEL
    w_image = 300
    h_image = int(300*img_size[1]/img_size[0])

    if h_image > 370:
        h_image = 370
        w_image = int(370 * img_size[0] / img_size[1])

    new_image = image.resize((w_image, h_image))

    # Creating background for every Image to show (to fill the Tkinter IMAGE TO SHOW LABEL space)
    bg_show_img = tkinter.Label(show_picture, width=43, height=26, bg="lightgrey")
    bg_show_img.grid(column=0, row=0)

    # Opening a customized Image to show
    image_to_show = ImageTk.PhotoImage(new_image)

    # Creating and setting parameters of Tkinter label with customized Image to show
    draft = tkinter.Label(show_picture)
    draft.grid(column=0, row=0)
    draft.image = image_to_show
    draft["image"] = image_to_show

    # Getting the statistics (Image details) for Tkinter RESIZED IMAGE DETAILS
    numbers_statisctics = cursor_db.execute(f"""SELECT * FROM last_images WHERE number = {number_of_img}""")
    numbers_statisctics_list = numbers_statisctics.fetchone()
    image_name = resized_img.rsplit('/', 1)[-1]

    numbers_statisctics_string = f"\n{round(numbers_statisctics_list[2]/1024, 2)} kB\n{round(numbers_statisctics_list[3]/1024, 2)} kB\n\n{numbers_statisctics_list[4]}\n{numbers_statisctics_list[5]}\n\n{image_name[:28]}\n{image_name[28:56]}\n{image_name[56:86]}"
    details_values.config(text=numbers_statisctics_string)

    db.close()


#==========Tkinter GUI===========

window = Tk()

window.title("IMAGE RESIZER") # TITLE of the window
window.resizable(0, 0) # window resizing is DISABLED

# UPLOADING DETAILS
uploading_info = tkinter.Label(window, width=50, height=5)
uploading_info.grid(column=0, row=0)

descriptions_info = tkinter.Label(uploading_info, text=f"Number of uploaded files:\nLess / More than targeted size:\nWeight of uploaded files:", justify= LEFT, width=25, bg="lightgrey", padx=4)
descriptions_info.grid(column=0, row=0)

values_info = tkinter.Label(uploading_info, text=f"0\n0 / 0\n0 kB", width=25, anchor="nw", justify= LEFT, padx=5)
values_info.grid(column=1, row=0)

# CONTAINER FOR BUTTONS
btn_label = tkinter.Label(window, text="", width=50, height=20, bg="grey", anchor="nw", padx=20)
btn_label.grid(column=1, row=0)

# BUTTONS UPLOAD AND RESIZE
btn_upload= tkinter.Button(btn_label, text="UPLOAD FILES", font=("Helvetica", 12, "bold"), width=15, height=3, command=lambda:upload(), bg="lightgreen")
btn_upload.grid(column=0, row=0)

btn_resize = tkinter.Button(btn_label, text="RESIZE", font=("Helvetica", 12, "bold"), width=15, height=3, command=lambda:resize(filename), state=DISABLED)
btn_resize.grid(column=1, row=0)

# ENTRY BOX (RESIZE TARGET)
entry_label = tkinter.Label(btn_label, text="Resize to (kB):", font=("Helvetica", 9), bg="grey")
entry_label.grid(column=0, row=2)

# Validation for Entry box (only numbers)
def only_numbers(char):
    return char.isdigit()

validation = btn_label.register(only_numbers)

entry = tkinter.Entry(btn_label, font=("Helvetica", 9), width=7, validate="key", validatecommand=(validation, '%S'))
entry.insert(0, "440")
entry.grid(column=1, row=2, pady=10, sticky="w")

# RESIZED IMAGE DETAILS
picture_info = tkinter.Label(window, width=50, anchor="nw", padx=20)
picture_info.grid(column=0, row=2)

details_label = tkinter.Label(picture_info, text=f"IMAGE DETAILS", width=25, height=1, anchor="nw", padx=0)
details_label.grid(column=0, row=0)

details_descriptions = tkinter.Label(picture_info, text="\nOriginal size:\nNew size:\n\nOriginal format:\nNew format: \n\nImage name: ", width=25, height=27, bg="lightgrey", anchor="nw", justify= LEFT, padx=5)
details_descriptions.grid(column=0, row=2)

details_values = tkinter.Label(picture_info, text="\nNone\nNone\n\nNone\nNone\n\nNone", width=25, height=27, anchor="nw", justify= LEFT, padx=5)
details_values.grid(column=1, row=2)

username_label = tkinter.Label(window, width=42, height=25) #height=30, width=50
username_label.grid(column=1, row=2)

# IMAGE TO SHOW LABEL
show_picture = tkinter.Label(username_label, text=f"Some image to show", width=42, height=25, bg="lightgrey")
show_picture.grid(column=0, row=0)

# OPEN FOLDER WITH RESIZED IMAGES
open_folder = tkinter.Button(window, text="OPEN FOLDER", font=("Helvetica", 9), width=15, height=2, command="", state=DISABLED)
open_folder.grid(column=0, row=3)

# IMAGE SLIDER BUTTONS
slider_buttons = tkinter.Label(window, width=50, height=2, anchor="s", padx=5)
slider_buttons.grid(column=1, row=3)

btn_left = tkinter.Button(slider_buttons, text="<", font=("Helvetica", 12, "bold"), width=5, height=1, command=lambda button_press="<": show(button_press))
btn_left.grid(column=0, row=0)

image_number = tkinter.Label(slider_buttons, text=number_of_img, width=15, height=2)
image_number.grid(column=1, row=0)

btn_right = tkinter.Button(slider_buttons, text=">", font=("Helvetica", 12, "bold"), width=5, height=1, command=lambda button_press=">": show(button_press))
btn_right.grid(column=2, row=0)


# Clearing DB after closing the main window
def func():

    db = sqlite3.connect("resized.db")
    cursor_db = db.cursor()
    cursor_db.execute("""DELETE FROM last_images""")
    db.commit()
    db.close()
    window.destroy()

window.protocol("WM_DELETE_WINDOW", func)

window.mainloop()