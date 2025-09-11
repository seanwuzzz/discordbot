import requests
from selectolax.parser import HTMLParser
import pandas as pd
import json
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import re
import matplotlib.pyplot as plt
import matplotlib.patches as patches

def gen_pic(url):

    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0",
    }

    url = url
    resp = requests.get(url, headers= headers)
    html = HTMLParser(resp.text)
    status = resp.status_code

    match_started = True
    bet_enabled = False
    maps = []

    try:
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
        if len(st) == 2:
            end = st[0]  # 比賽是否結束or幾天後開始
            bo = st[1]  # best of ?
        else:
            end = st[0]
            bo = st[-1]
        
        try:
            final_score = status.css_first(".js-spoiler ").text(strip=True).replace('\t', '').replace('\n', '')
            veto = html.css_first('.match-header-note').text(strip=True).replace('\t', '').replace('\n', '')
        except:
            match_started = False
            final_score = '0:0'
            veto = ' '
    except:
        print("無法獲取比賽資料")
        return 0

    # 個地圖資料擷取
    container = html.css_first(".vm-stats-container")
    if match_started == True:
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
    else:
        try:
            team_tags = []
            bet_rate = []
            bet_tree = html.css_first('a.wf-card.mod-dark.match-bet-item')
            team_tags_f = bet_tree.css('.match-bet-item-team-tag')
            for tag in team_tags_f:
                team_tags.append(tag.text(strip=True))

            betting = bet_tree.css('.match-bet-item-odds.mod-')
            for bet in betting:
                bet_rate.append(float(bet.text(strip=True)))
            bet_enabled = True

        except:
            print('123')
    
    # 定義文字處理函式
    def smart_linebreak(text, max_len, splt):
        text = extract_parentheses_content(text)
        words = text.split(splt)
        lines = [[]]  # 用來儲存多行內容
        current_len = 0

        for word in words:
            word_len = len(word) + (1 if lines[-1] else 0)  # +1 是 split 字元
            if current_len + word_len <= max_len:
                lines[-1].append(word)
                current_len += word_len
            else:
                # 換新的一行
                lines.append([word])
                current_len = len(word)

        # 把每一行合併成字串，再用換行符號組合
        return '\n'.join(splt.join(line) for line in lines)

    def extract_parentheses_content(text):
        match = re.search(r'\((.*?)\)', text)
        return match.group(1) if match else text

    
    def centered_startx(text, center_x, font):
        # 測量文字寬度
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]

        # 計算讓中線對齊 center_x 的起始位置
        start_x = center_x - text_width // 2
        return start_x, text_width

    def generate_odds_chart(teams, odds):
        colors= ['white', 'black']

        inv1 = 1 / odds[0]
        inv2 = 1 / odds[1]
        total = inv1 + inv2
        pct1 = inv1 / total * 100
        pct2 = inv2 / total * 100

        # 用堆疊橫條畫出來
        fig, ax = plt.subplots(figsize=(6.0, 0.75), dpi=100)

        # 畫單一列（y=0）長度為 100 的 bar
        ax.barh(0, pct1, color=colors[0], edgecolor='black')
        ax.barh(0, pct2, left=pct1, color=colors[1], edgecolor='black')

        # 加上隊伍名稱與百分比
        ax.text(pct1 / 2, 0, f"{teams[0]} {odds[0]}x", ha='center', va='center',
                color='black', fontsize=12, fontweight = 'bold')

        ax.text(pct1 + pct2 / 2, 0, f"{teams[1]} {odds[1]}x", ha='center', va='center',
                color='white', fontsize= 12, fontweight = 'bold')

        # 美化與去除多餘的元素
        ax.set_xlim(0, 100)
        ax.set_ylim(-0.5, 0.5)
        ax.axis('off')  # 隱藏軸線
        
        plt.tight_layout()
 
        buf = BytesIO()
        plt.savefig(buf, format='PNG', bbox_inches='tight', transparent=True)
        plt.close(fig)
        buf.seek(0)
        return Image.open(buf)
    #---------------------------------------------以下為繪圖 ------------------------------------------------

    # 設定畫布
    if (len(maps) == 3) and match_started == True:
        width, height = 800, 600
    elif (len(maps) == 2) and match_started == True:
        width, height = 800, 550
    elif (len(maps) == 4) and match_started == True:
        width, height = 800, 700
    elif (len(maps) == 5) and match_started == True:
        width, height = 800, 750
    elif match_started == False:
        width, height = 800, 400

    img = Image.new("RGB", (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    # 畫背景格線（方便對齊）
    grid_color = (230, 230, 230)  # 淺灰色
    for x in range(0, width, 20):  # 每 20px 畫一條直線
        draw.line([(x, 0), (x, height)], fill=grid_color, width=1)
    for y in range(0, height, 30):  # 每 30px 畫一條橫線
        draw.line([(0, y), (width, y)], fill=grid_color, width=1)

    # 字型

    font_content = ImageFont.truetype("fonts/NotoSans-Regular.ttf", 25)
    font_bold = ImageFont.truetype("fonts/NotoSans-Bold.ttf", 30)
    font_sub = ImageFont.truetype("fonts/NotoSans-Regular.ttf", 20)
    font_sub_bold = ImageFont.truetype("fonts/NotoSans-SemiBold.ttf", 20)
    font_score = ImageFont.truetype("fonts/NotoSans-Regular.ttf", 60)


    # 比賽總資訊
    team1_start, team1_w = centered_startx(smart_linebreak(team1_name, 13, ' '), 140, font= font_bold)
    draw.text((team1_start, 175), f"{smart_linebreak(team1_name, 13, ' ')}", fill="black", font=font_bold)

    team2_start, team2_w = centered_startx(smart_linebreak(team2_name, 13, ' '), 660, font= font_bold)
    draw.text((team2_start, 175), f"{smart_linebreak(team2_name, 13, ' ')}", fill="black", font=font_bold)

    # 最終比分
    f_score = final_score.split(':')
    f_score = f'{f_score[0]} : {f_score[1]}'
    fscore_start, fscore_w = centered_startx(f_score, width//2, font= font_score)
    draw.text((fscore_start, 90), f"{f_score}", fill="black", font=font_score)

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
    event_name_start, event_name_w = centered_startx(event_name, width//2, font_sub_bold)
    draw.text((event_name_start, 15), f"{event_name}", fill="blue", font=font_sub_bold)

    event_stage_start, event_stage_w = centered_startx(event_stage, width//2, font_sub)
    draw.text((event_stage_start, 40), f"{event_stage}", fill="black", font=font_sub)

    end_start, end_w = centered_startx(end, width//2, font_sub)
    if end.lower() == 'final':
        draw.text((end_start, 70), f"{end}", fill="gray", font=font_sub)
    else:
        draw.text((end_start, 70), f"{end}", fill="green", font=font_sub)

    bo_start, bo_w = centered_startx(bo, width//2, font_sub)
    draw.text((bo_start, 185), f"{bo}", fill="gray", font=font_sub)

    for i in range(len(maps)):
        cmap = maps[i]
        # 資料匯入
        team1_name = cmap.get('team1', 'Unknown Team 1')
        team2_name = cmap.get('team2', 'Unknown Team 2')
        score1 = cmap.get('score1', 0)
        score2 = cmap.get('score2', 0)
        map_name = cmap.get('map', 'Unknown Map')
        time = cmap.get('time', 'Unknown Time')

        #地圖名稱
        map_start, map_w = centered_startx(map_name, width//2, font_bold)
        draw.text((map_start, 250 + (80*i)), f"{map_name}", fill="black", font=font_bold)

        # 地圖時間
        time_start, time_w = centered_startx(time, width//2, font_content)
        draw.text((time_start, 290 + (80*i)), f"{time}", fill="gray", font=font_content)
            
        # 地圖分數
        score1_start, score1_w = centered_startx(score1, 140, font_score)
        score2_start, score2_w = centered_startx(score2, width-140, font_score)
        
        if int(score1) > int(score2):
            draw.text((score1_start, 245 + (80*i)), f"{score1}", fill="green", font=font_score)
            draw.text((score2_start, 250 + (80*i)), f"{score2}", fill="black", font=font_score)
        else:
            draw.text((score1_start, 245 + (80*i)), f"{score1}", fill="black", font=font_score)
            draw.text((score2_start, 250 + (80*i)), f"{score2}", fill="green", font=font_score)
        
        # Veto
        if i == len(maps) - 1:
            veto_start, veto_w = centered_startx(smart_linebreak(veto, 50, ';'), width//2, font_sub)
            if veto_start < 0:
                font = ImageFont.truetype("fonts/NotoSans-Regular.ttf", 16)
                bbox = bbox = draw.textbbox((0, 0), smart_linebreak(veto, 50, ';'), font=font)
                veto_w = bbox[2] - bbox[0]
                draw.text(((width - veto_w)//2, 250 + 80*i + 100), f"{smart_linebreak(veto, 50, ';')}", fill="gray", font=font)
            else:
                draw.text(((width - veto_w)//2, 250 + 80*i + 100), f"{smart_linebreak(veto, 50, ';')}", fill="gray", font=font_sub)
        
    # 儲存圖片或回傳到 Discord
    if bet_enabled == True:
        bet_bar = generate_odds_chart(team_tags, bet_rate)
        bet_bar = bet_bar.resize((600,75))
        img.paste(bet_bar, (100, 250), bet_bar)


    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer
