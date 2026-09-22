# -*- coding: utf-8 -*-
from PIL import Image, ImageDraw, ImageFont
import os

# ========== Data ==========
schedule = {
    "1-2节\n08:30-10:05": {
        "Mon": [("Java面向对象程序设计", "1-5周,7-18周", "10-501")],
        "Tue": [],
        "Wed": [("计算机网络", "1-4周", "4-402a"), ("计算机网络", "12-17周", "8-601")],
        "Thu": [("Python程序设计", "1-4周,6-16周", "8-504")],
        "Fri": [("Java面向对象程序设计", "1-3周,10-17周", "8-505")],
        "Sat": [],
        "Sun": [],
    },
    "3-4节\n10:25-12:00": {
        "Mon": [("习近平新时代中国特色社会主义思想概论", "1-5周,7-18周", "2-208")],
        "Tue": [("数字逻辑与数字电路", "1-17周", "4-406a")],
        "Wed": [("大学英语（3）", "1-16周", "2-309")],
        "Thu": [],
        "Fri": [("数字逻辑与数字电路实验", "6-7周", "8-302"), ("数字逻辑与数字电路实验", "8-17周", "8-301")],
        "Sat": [],
        "Sun": [],
    },
    "5-6节\n14:00-15:35": {
        "Mon": [("体育（3）专选", "1-5周,7-18周", "室外网球场0102\n网球（2）")],
        "Tue": [("计算机网络", "1-16周", "4-405")],
        "Wed": [("习近平新时代中国特色\n社会主义思想概论", "1-7周", "2-308")],
        "Thu": [("Python程序设计", "1-4周,6-10周", "8-504")],
        "Fri": [("Java面向对象程序设计", "9-16周", "8-505")],
        "Sat": [],
        "Sun": [],
    },
    "7-8节\n15:55-17:30": {
        "Mon": [],
        "Tue": [("数字逻辑与数字电路", "1-4周,6-16周", "4-508")],
        "Wed": [("走在前列的广东实践", "6-10周", "1-204"), ("走在前列的广东实践", "11-13周", "校内场地"), ("形势与政策（3）", "15-18周", "2-208")],
        "Thu": [("数字逻辑与数字电路", "1-4周,6-16周", "4-508")],
        "Fri": [],
        "Sat": [],
        "Sun": [],
    },
    "9-10节\n19:00-20:35": {
        "Mon": [],
        "Tue": [("大学生职业规划", "1-8周", "4-308")],
        "Wed": [],
        "Thu": [],
        "Fri": [("体育（3）专选", "17周", "室外网球场0102\n网球（2）")],
        "Sat": [],
        "Sun": [],
    },
}

day_names = ["Mon\n星期一", "Tue\n星期二", "Wed\n星期三", "Thu\n星期四", "Fri\n星期五", "Sat\n星期六", "Sun\n星期日"]
day_keys = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

# ========== Layout ==========
# Fonts
font_title = ImageFont.truetype("C:/Windows/Fonts/msyhbd.ttc", 36)
font_sub = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 20)
font_header = ImageFont.truetype("C:/Windows/Fonts/msyhbd.ttc", 18)
font_time = ImageFont.truetype("C:/Windows/Fonts/msyhbd.ttc", 15)
font_course = ImageFont.truetype("C:/Windows/Fonts/msyhbd.ttc", 15)
font_info = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 13)
font_small = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 11)

# Colors
BG_COLOR = (245, 247, 250)
TITLE_COLOR = (26, 54, 93)
HEADER_BG = (43, 108, 176)
HEADER_FG = (255, 255, 255)
TIME_BG = (227, 242, 253)
MORNING_BG = (240, 248, 255)
AFTERNOON_BG = (240, 255, 240)
EVENING_BG = (255, 245, 238)
GRID_COLOR = (200, 210, 220)
COURSE_NAME_COLOR = (26, 54, 93)
WEEK_COLOR = (200, 80, 80)
LOC_COLOR = (60, 100, 160)
EMPTY_COLOR = (180, 185, 190)

# Dimensions
num_cols = 1 + len(day_keys)  # time + 7 days
col_time_w = 130
col_day_w = 175
header_h = 50
row_h = 150
title_area_h = 100
footer_h = 40
margin = 30

img_w = margin * 2 + col_time_w + col_day_w * len(day_keys)
img_h = title_area_h + header_h + row_h * 5 + footer_h + margin

img = Image.new("RGB", (img_w, img_h), BG_COLOR)
draw = ImageDraw.Draw(img)

# ========== Draw Title ==========
title_y = 20
draw.text((margin, title_y), "余慧琳课表", fill=TITLE_COLOR, font=font_title)
sub_text = "2026-2027学年第1学期    学号：5225210102604"
sub_bbox = draw.textbbox((0, 0), sub_text, font=font_sub)
sub_w = sub_bbox[2] - sub_bbox[0]
draw.text((img_w - margin - sub_w, title_y + 8), sub_text, fill=(100, 110, 120), font=font_sub)

# ========== Draw Header ==========
y_start = title_area_h
x = margin

# Time column header
draw.rectangle([x, y_start, x + col_time_w, y_start + header_h], fill=HEADER_BG, outline=GRID_COLOR, width=2)
draw.text((x + 15, y_start + 12), "节次/时间", fill=HEADER_FG, font=font_header)
x += col_time_w

# Day headers
for i, name in enumerate(day_names):
    draw.rectangle([x, y_start, x + col_day_w, y_start + header_h], fill=HEADER_BG, outline=GRID_COLOR, width=2)
    lines = name.split("\n")
    for j, line in enumerate(lines):
        draw.text((x + col_day_w//2 - len(line)*8, y_start + 8 + j*20), line, fill=HEADER_FG, font=font_header)
    x += col_day_w

# ========== Draw Rows ==========
time_slots = list(schedule.keys())
period_colors = [MORNING_BG, MORNING_BG, AFTERNOON_BG, AFTERNOON_BG, EVENING_BG]

for row_idx, (time_key, day_data) in enumerate(schedule.items()):
    y = y_start + header_h + row_idx * row_h
    bg = period_colors[row_idx]

    # Time column
    x = margin
    draw.rectangle([x, y, x + col_time_w, y + row_h], fill=TIME_BG, outline=GRID_COLOR, width=2)
    lines = time_key.split("\n")
    for j, line in enumerate(lines):
        draw.text((x + 15, y + row_h//2 - 20 + j*22), line, fill=TITLE_COLOR, font=font_time)
    x += col_time_w

    # Day columns
    for day_idx, day_key in enumerate(day_keys):
        courses = day_data[day_key]
        draw.rectangle([x, y, x + col_day_w, y + row_h], fill=bg, outline=GRID_COLOR, width=2)

        if not courses:
            # Empty cell
            draw.text((x + col_day_w//2 - 10, y + row_h//2 - 8), "—", fill=EMPTY_COLOR, font=font_time)
        else:
            cell_y = y + 8
            for ci, (cname, weeks, loc) in enumerate(courses):
                if ci > 0:
                    # Separator line
                    draw.line([x + 5, cell_y - 4, x + col_day_w - 5, cell_y - 4], fill=GRID_COLOR, width=1)

                # Course name (handle multiline)
                name_lines = cname.split("\n")
                for nl in name_lines:
                    draw.text((x + 8, cell_y), nl, fill=COURSE_NAME_COLOR, font=font_course)
                    cell_y += 20

                # Weeks
                draw.text((x + 8, cell_y), f"📅 {weeks}", fill=WEEK_COLOR, font=font_info)
                cell_y += 18

                # Location
                loc_lines = loc.split("\n")
                for ll in loc_lines:
                    draw.text((x + 8, cell_y), f"📍 {ll}", fill=LOC_COLOR, font=font_info)
                    cell_y += 18

                cell_y += 4

        x += col_day_w

# ========== Draw Footer ==========
footer_y = y_start + header_h + 5 * row_h + 10
draw.text((margin, footer_y), "打印时间: 2026-09-04", fill=(150, 155, 160), font=font_small)

# ========== Save ==========
proj_dir = "C:/Users/A7705/AppData/Roaming/TRAE SOLO CN/ModularData/ai-agent/work-mode-projects/6a9ab4260cc0275fcdd24032"
out_path = os.path.join(proj_dir, "余慧琳课表_2026-2027-1.png")
img.save(out_path, "PNG")
print(f"Saved: {out_path} ({img.width}x{img.height})")
