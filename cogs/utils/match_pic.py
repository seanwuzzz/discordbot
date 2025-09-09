import requests
from selectolax.parser import HTMLParser
import pandas as pd
import json
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO


def gen_pic(url):

    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0",
    }

    url = url
    resp = requests.get(url, headers= headers)
    html = HTMLParser(resp.text)
    status = resp.status_code

    maps = []


    # 總結果資料擷取
    box = html.css_first(".match-header-super")
    event_name = box.css_first('div[style*="font-weight"]').text(strip=True)
    event_stage = box.css_first('.match-header-event-series').text(strip=True).replace('\t', '').replace('\n', '')


    vs = html.css_first(".match-header-vs")
    team1_tag = vs.css_first('a.match-header-link.wf-link-hover.mod-1')
    team1_name =team1_tag.css_first('.wf-title-med ').text().replace('\t', '').replace('\n', '').strip()
    team1_icon = team1_tag.css_first('img').attributes.get('src')

    team2_tag = vs.css_first('a.match-header-link.wf-link-hover.mod-2')
    team2_icon = team2_tag.css_first('img').attributes.get('src')
    team2_name =team2_tag.css_first('.wf-title-med ').text().strip()

    status = html.css_first('.match-header-vs-score')
    current = status.css('.match-header-vs-note')

    st = []
    for stat in current:
        st.append(stat.text(strip=True).replace('\t', '').replace('\n', '').upper())
    final_score = status.css_first(".js-spoiler ").text(strip=True).replace('\t', '').replace('\n', '')
    end = st[0]
    bo = st[1]

    veto = html.css_first('.match-header-note').text(strip=True).replace('\t', '').replace('\n', '')


    # 個地圖資料擷取
    container = html.css_first(".vm-stats-container")
    for map in container.css('[class = "vm-stats-game "]'):
        player_stats = []
        team1 = map.css_first('.team .team-name').text().strip()
        team2 = map.css_first('.team.mod-right .team-name').text().strip()

        # map fetch
        map_node = map.css_first(".map span")
        map_names = map_node.text().replace('\t', ' ').replace('\n', ' ').split(' ')
        map_names = [item for item in map_names if item != '']
        map_name = map_names[0]

        scores = map.css('.score')
        score1 = scores[0].text().strip()
        score2 = scores[1].text().strip()

        time = map.css_first(".map-duration").text().strip()

        for team in map.css('[class="wf-table-inset mod-overview"]'):
            tbody = team.css_first("tbody")  # 找到 tbody 節點
            # 找出所有 tr
            for row in tbody.css("tr"):
                cells = row.css("td")

                flag_tag = cells[0].css_first('i')
                flag = flag_tag.attributes.get("title", "")

                player_name = player_name = [s for s in cells[0].text().replace('\t', ' ').replace('\n', ' ').split(' ') if s.strip()][0]
                agent_tag = cells[1].css_first('img')
                agent = agent_tag.attributes.get("title", "")

                rating = cells[2].css_first('.mod-both').text()
                acs = cells[3].css_first('.mod-both').text()

                kills = cells[4].css_first('.mod-both').text()
                deaths = cells[5].css_first('.mod-both').text()
                assists = cells[6].css_first('.mod-both').text()

                kd_diff = cells[7].css_first('.mod-both').text()
                kast = cells[8].css_first('.mod-both').text()
                adr = cells[9].css_first('.mod-both').text()
                hs = cells[10].css_first('.mod-both').text()
                fk = cells[11].css_first('.mod-both').text()
                fd = cells[12].css_first('.mod-both').text()

                player_stats.append({
                    'flag': flag,
                    'player' : player_name,
                    'agent' : agent,
                    'rating': rating,
                    'acs': acs,
                    'kills': kills,
                    'deaths': deaths,
                    'assists': assists,
                    'kd_diff': kd_diff,
                    'kast': kast,
                    'adr': adr,
                    'hs': hs,
                    'fk': fk,
                    'fd': fd
                })
        maps.append({
            'team1': team1,
            'team2': team2,
            'map' : map_name,
            'score1': score1,
            'score2': score2,
            'time': time,
            'players': player_stats
        })

    
    def smart_linebreak(text, max_len, splt):
        words = text.split(splt)
        line1 = []
        line2 = []
        current_len = 0

        for word in words:
            # +1 是空格（除第一個字以外）
            word_len = len(word) + (1 if line1 else 0)
            if current_len + word_len <= max_len:
                line1.append(word)
                current_len += word_len
            else:
                line2.append(word)

        # 加上換行（若第二行有內容才換）
        if line2:
            return splt.join(line1) + '\n' + splt.join(line2)
        else:
            return splt.join(line1)


    #---------------------------------------------以下為繪圖 ------------------------------------------------

    # 設定畫布
    if (len(maps) == 3):
        width, height = 800, 600
    elif (len(maps) == 2):
        width, height = 800, 550
    elif (len(maps) == 4):
        width, height = 800, 700
    elif (len(maps) == 5):
        width, height = 800, 750

    img = Image.new("RGB", (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    # 畫背景格線（方便對齊）
    '''grid_color = (230, 230, 230)  # 淺灰色
    for x in range(0, width, 20):  # 每 20px 畫一條直線
        draw.line([(x, 0), (x, height)], fill=grid_color, width=1)
    for y in range(0, height, 30):  # 每 30px 畫一條橫線
        draw.line([(0, y), (width, y)], fill=grid_color, width=1)'''

    # 字型

    font_content = ImageFont.truetype("fonts/NotoSans-Regular.ttf", 25)
    font_bold = ImageFont.truetype("fonts/NotoSans-Bold.ttf", 30)
    font_sub = ImageFont.truetype("fonts/NotoSans-Regular.ttf", 20)
    font_score = ImageFont.truetype("fonts/NotoSans-Regular.ttf", 60)


    # 比賽總資訊
    bbox= draw.textbbox((0, 0), smart_linebreak(team1_name, 13, ' '), font=font_bold)
    team1_w = bbox[2] - bbox[0]
    team1_start = 50
    draw.text((50, 180), f"{smart_linebreak(team1_name, 13, ' ')}", fill="black", font=font_bold)

    bbox= draw.textbbox((0, 0), smart_linebreak(team2_name, 13, ' '), font=font_bold)
    team2_w = bbox[2] - bbox[0]
    team2_start  = width - (50 + team2_w)
    draw.text((team2_start, 180), f"{smart_linebreak(team2_name, 13, ' ')}", fill="black", font=font_bold)


    # 最終比分
    f_score = final_score.split(':')
    f_score = f'{f_score[0]} : {f_score[1]}'
    bbox = draw.textbbox((0, 0), f_score, font=font_score)
    text_w = bbox[2] - bbox[0]
    draw.text(((width - text_w)//2, 90), f"{f_score}", fill="black", font=font_score)

    # 隊伍logo
    try:
        t1_logo = requests.get('https:' + team1_icon)
    except:
        t1_logo = requests.get('https://i.pinimg.com/736x/92/02/46/9202461fb26e12bfc91175439b9dc7e6.jpg')
    t1_img = Image.open(BytesIO(t1_logo.content)).convert("RGBA")
    t1_img = t1_img.resize((120,120))
    t1_logo_pos = team1_start + (team1_w//2) - 60
    img.paste(t1_img, (t1_logo_pos, 50), t1_img)

    try:
        t2_logo = requests.get('https:' + team2_icon)
    except:
        t2_logo = requests.get('https://i.pinimg.com/736x/92/02/46/9202461fb26e12bfc91175439b9dc7e6.jpg')
    t2_img = Image.open(BytesIO(t2_logo.content)).convert("RGBA")
    t2_img = t2_img.resize((120,120))
    t2_logo_pos = team2_start + (team2_w//2) - 60
    img.paste(t2_img, (t2_logo_pos, 50), t2_img)

    # Event
    bbox = bbox = draw.textbbox((0, 0), event_name, font=font_sub)
    event_name_w = bbox[2] - bbox[0]
    draw.text(((width - event_name_w)//2, 15), f"{event_name}", fill="black", font=font_sub)
    bbox = bbox = draw.textbbox((0, 0), event_stage, font=font_sub)
    event_stage_w = bbox[2] - bbox[0]
    draw.text(((width - event_stage_w)//2, 40), f"{event_stage}", fill="black", font=font_sub)

    bbox = bbox = draw.textbbox((0, 0), bo, font=font_sub)
    bo_w = bbox[2] - bbox[0]
    draw.text(((width - bo_w)//2, 185), f"{bo}", fill="gray", font=font_sub)
    #bbox = draw.textbbox((0, 0), team2, font=font_content)

    for i in range(len(maps)):
        cmap = maps[i]
        # 資料匯入
        team1_name = cmap['team1']
        team2_name = cmap['team2']
        score1 = cmap['score1']
        score2 = cmap['score2']
        map_name = cmap['map']
        time = cmap['time']

        # 標題

        #地圖名稱
        bbox = draw.textbbox((0, 0), map_name, font=font_bold)
        text_w = bbox[2] - bbox[0]
        draw.text(((width - text_w)//2, 250 + (80*i)), f"{map_name}", fill="black", font=font_bold)

        # 地圖時間
        bbox = draw.textbbox((0, 0), time, font=font_content)
        text_w = bbox[2] - bbox[0]
        draw.text(((width - text_w)//2, 290 + (80*i)), f"{time}", fill="gray", font=font_content)
            
        # 地圖分數
        bbox = draw.textbbox((0, 0), score1, font=font_score)
        score1_w = bbox[2] - bbox[0]
        bbox = draw.textbbox((0, 0), score2, font=font_score)
        score2_w = bbox[2] - bbox[0]
        if int(score1) > int(score2):
            draw.text((50, 245 + (80*i)), f"{score1}", fill="green", font=font_score)
            draw.text((width - (50+score2_w), 250 + (80*i)), f"{score2}", fill="black", font=font_score)
        else:
            draw.text((50, 245 + (80*i)), f"{score1}", fill="black", font=font_score)
            draw.text((width - (50+score2_w), 250 + (80*i)), f"{score2}", fill="green", font=font_score)
        
        # Veto
        if i == len(maps) - 1:
            bbox = bbox = draw.textbbox((0, 0), smart_linebreak(veto, 50, ';'), font=font_sub)
            veto_w = bbox[2] - bbox[0]
            veto_start = width - veto_w
            if veto_start < 0:
                font = ImageFont.truetype("fonts/NotoSans-Regular.ttf", 16)
                bbox = bbox = draw.textbbox((0, 0), smart_linebreak(veto, 50, ';'), font=font)
                veto_w = bbox[2] - bbox[0]
                draw.text(((width - veto_w)//2, 250 + 80*i + 100), f"{smart_linebreak(veto, 50, ';')}", fill="gray", font=font)
            else:
                draw.text(((width - veto_w)//2, 250 + 80*i + 100), f"{smart_linebreak(veto, 50, ';')}", fill="gray", font=font_sub)

    # 儲存圖片或回傳到 Discord
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer