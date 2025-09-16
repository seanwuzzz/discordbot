import requests
from selectolax.parser import HTMLParser
import pandas as pd
import json
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import re
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib import font_manager


def scrape_major_info(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0",
    }

    url = url
    resp = requests.get(url, headers= headers)
    html = HTMLParser(resp.text)
    status = resp.status_code

    # 定義各式儲存空間
    main_info = {}  # 比賽主資訊
    maps = []  # 各地圖主資訊
    bet_info = []  # 賠率資訊
    data = []  # 總儲存空間

    
    match_status = {
        'match_started' : True,
        'bet_enabled' : False
    }
    
    try:
        # 總結果資料擷取
        box = html.css_first(".match-header-super")
        main_info['event_name'] = box.css_first('div[style*="font-weight"]').text(strip=True)
        main_info['event_stage'] = box.css_first('.match-header-event-series').text(strip=True).replace('\t', '').replace('\n', '')


        vs = html.css_first(".match-header-vs")
        team1_tag = vs.css_first('a.match-header-link.wf-link-hover.mod-1')
        main_info['team1_name'] =team1_tag.css_first('.wf-title-med ').text().replace('\t', '').replace('\n', '').strip()
        main_info['team1_icon'] = team1_tag.css_first('img').attributes.get('src')

        team2_tag = vs.css_first('a.match-header-link.wf-link-hover.mod-2')
        main_info['team2_icon'] = team2_tag.css_first('img').attributes.get('src')
        main_info['team2_name'] = team2_tag.css_first('.wf-title-med ').text().strip()

        status = html.css_first('.match-header-vs-score')
        current = status.css('.match-header-vs-note')

        nodes = []
        match_date = html.css('.match-header-date .moment-tz-convert')
        count = 0
        for info in match_date:
            nodes.append(info.text(strip=True))
            if count == 0:
                match_utc = info.attributes.get('data-utc-ts')
        
        main_info['match_utc'] = match_utc    
        main_info['game_date'] = nodes[0]
        main_info['sch_time'] = nodes[1]
            

        st = []
        for stat in current:
            st.append(stat.text(strip=True).replace('\t', '').replace('\n', '').upper())
        if len(st) == 2:
            main_info['status'] = st[0]  # 比賽是否結束or幾天後開始
            main_info['bo'] = st[1]  # best of ?
        else:
            main_info['status'] = st[0]
            main_info['bo'] = st[-1]
        
        try:
            main_info['final_score'] = status.css_first(".js-spoiler ").text(strip=True).replace('\t', '').replace('\n', '')
            main_info['veto'] = html.css_first('.match-header-note').text(strip=True).replace('\t', '').replace('\n', '')
        except:
            match_status['match_started'] = False
            main_info['final_score'] = '0:0'
            main_info['veto'] = ' '
        data.append(main_info)

    except Exception as e:
        print(f"無法獲取比賽資料: {e}")
        return 0

    # 個別地圖資料擷取
    container = html.css_first(".vm-stats-container")
    if match_status['match_started'] == True:
        if main_info['status'].lower() == 'live':
            search_key = '.vm-stats-game'
        else:
            search_key = '[class = "vm-stats-game "]'
        for map in container.css(search_key):
            game_id = map.attributes.get('data-game-id')
            if game_id != 'all':
                
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
                maps.append({
                    'team1': team1,
                    'team2': team2,
                    'map' : map_name,
                    'score1': score1,
                    'score2': score2,
                    'time': time,
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
            match_status['bet_enabled'] = True

            bet_info.append(team_tags)
            bet_info.append(bet_rate)
            
        except Exception as e:
            print(f'賠率資訊Unavailable: {e}')

    data.append(match_status)
    data.append(maps)
    data.append(bet_info)

    return data

def scrape_map_stats(url):
    headers = {
            "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0",
        }
    rows = []
    url = url
    resp = requests.get(url, headers= headers)
    html = HTMLParser(resp.text)

    container = html.css_first(".vm-stats-container")
    for map in container.css('[class = "vm-stats-game "]'):
        for team in map.css('[class="wf-table-inset mod-overview"]'):
            tbody = team.css_first("tbody")  # 找到 tbody 節點
            # 找出所有 tr
            for row in tbody.css("tr"):
                cells = row.css("td")

                flag_tag = cells[0].css_first('i')
                flag = flag_tag.attributes.get("title", "")

                player_name  = [s for s in cells[0].text().replace('\t', ' ').replace('\n', ' ').split(' ') if s.strip()][0]
                team = [s for s in cells[0].text().replace('\t', ' ').replace('\n', ' ').split(' ') if s.strip()][1]
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

                rows.append({
                    'player' : player_name,
                    'team' : team,
                    'flag': flag,
                    'agent' : agent,
                    'rating': float(rating),
                    'acs': float(acs),
                    'kills': float(kills),
                    'deaths': float(deaths),
                    'assists': float(assists),
                    'kd_diff': float(kd_diff),
                    'kast': float(kast.replace('%','')),
                    'adr': float(adr),
                    'hs': float(hs.replace('%','')),
                    'fk': float(fk),
                    'fd': float(fd)
                })
    df = pd.DataFrame(rows)
    stats = ['acs', 'kills', 'deaths', 'assists', 'kd_diff', 'kast', 'adr', 'hs', 'fk', 'fd']
    player_avg_stats = df.groupby('player')[stats].mean().round(2)
    player_teams = df.groupby('player')['team'].first().reset_index()
    player_avg_stats = pd.merge(player_avg_stats, player_teams, on='player').sort_values(by=['team', 'acs'], ascending=[False, False]).reset_index(drop=True)
    print(player_avg_stats)

def gen_pic(data):

    info = data[0]
    status = data[1]
    maps = data[2]
    
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
    
    def centered_starty(text, center_y, font):
        # 測量文字高度
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_height = text_bbox[3] - text_bbox[1]

        # 計算讓中線對齊 center_y 的起始位置
        start_y = center_y - text_height // 2
        return start_y, text_height

    # 繪製賠率bar chart
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
        font_path = "fonts/NotoSans-Regular.ttf"
        font_prop = font_manager.FontProperties(fname=font_path)
        ax.text(pct1 / 2, 0, f"{teams[0]} {odds[0]}x", ha='center', va='center',
                color='black', fontsize=12)

        ax.text(pct1 + pct2 / 2, 0, f"{teams[1]} {odds[1]}x", ha='center', va='center',
                color='white', fontsize= 12)

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
    if (len(maps) == 3) and status['match_started'] == True:
        width, height = 800, 600
    elif (len(maps) == 2) and status['match_started'] == True:
        width, height = 800, 550
    elif (len(maps) == 4) and status['match_started'] == True:
        width, height = 800, 700
    elif (len(maps) == 5) and status['match_started'] == True:
        width, height = 800, 750
    elif status['match_started'] == False:
        width, height = 800, 400

    img = Image.new("RGB", (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    # 字型

    font_content = ImageFont.truetype("fonts/NotoSans-Regular.ttf", 25)
    font_bold = ImageFont.truetype("fonts/NotoSans-Bold.ttf", 30)
    font_sub = ImageFont.truetype("fonts/NotoSans-Regular.ttf", 20)
    font_sub_bold = ImageFont.truetype("fonts/NotoSans-SemiBold.ttf", 20)
    font_score = ImageFont.truetype("fonts/NotoSans-Regular.ttf", 60)
    font_note = ImageFont.truetype("fonts/NotoSans-Regular.ttf", 14)


    # 比賽總資訊
    team1_starty = 175
    team2_starty = 175
    team1_startx, team1_w = centered_startx(smart_linebreak(info['team1_name'], 13, ' '), 140, font= font_bold)
    draw.text((team1_startx, 175), f"{smart_linebreak(info['team1_name'], 13, ' ')}", fill="black", font=font_bold)

    team2_startx, team2_w = centered_startx(smart_linebreak(info['team2_name'], 13, ' '), 660, font= font_bold)
    draw.text((team2_startx, 175), f"{smart_linebreak(info['team2_name'], 13, ' ')}", fill="black", font=font_bold)

    # 最終比分
    f_score = info['final_score'].split(':')
    fscore1 = int(f_score[0].strip())
    fscore2 = int(f_score[1].strip())

    draw.text((width//2, 117), ':', fill='black', font= font_score, anchor = 'mt')
    if fscore1 > fscore2:
        draw.text(((width//2) - 50, 112), f'{fscore1}', fill='green', font= font_score, anchor= 'mt')
        draw.text(((width//2) + 50, 112), f'{fscore2}', fill='black', font= font_score, anchor= 'mt')
    elif fscore1 < fscore2:
        draw.text(((width//2) - 50, 112), f'{fscore1}', fill='black', font= font_score, anchor= 'mt')
        draw.text(((width//2) + 50, 112),f'{fscore2}', fill='green', font= font_score, anchor= 'mt')
    else:
        draw.text(((width//2) - 50, 112), f'{fscore1}', fill='black', font= font_score, anchor= 'mt')
        draw.text(((width//2) + 50, 112), f'{fscore2}', fill='black', font= font_score, anchor= 'mt')

        
    #fscore_start, fscore_w = centered_startx(f_score, width//2, font= font_score)
    #draw.text((fscore_start, 90), f"{f_score}", fill="black", font=font_score)

    # 隊伍logo
    try:
        t1_logo = requests.get('https:' + info['team1_icon'])
    except:
        t1_logo = requests.get('https://i.pinimg.com/736x/92/02/46/9202461fb26e12bfc91175439b9dc7e6.jpg')
    t1_img = Image.open(BytesIO(t1_logo.content)).convert("RGBA")
    t1_img = t1_img.resize((120,120))
    t1_logo_pos = team1_startx + (team1_w//2) - 60
    img.paste(t1_img, (t1_logo_pos, 50), t1_img)

    try:
        t2_logo = requests.get('https:' + info['team2_icon'])
    except:
        t2_logo = requests.get('https://i.pinimg.com/736x/92/02/46/9202461fb26e12bfc91175439b9dc7e6.jpg')
    t2_img = Image.open(BytesIO(t2_logo.content)).convert("RGBA")
    t2_img = t2_img.resize((120,120))
    t2_logo_pos = team2_startx + (team2_w//2) - 60
    img.paste(t2_img, (t2_logo_pos, 50), t2_img)

    # Event
    event_name_start, event_name_w = centered_startx(info['event_name'] ,width//2, font_sub_bold)
    draw.text((event_name_start, 15), f"{info['event_name']}", fill="blue", font=font_sub_bold)

    event_stage_start, event_stage_w = centered_startx(info['event_stage'], width//2, font_sub)
    draw.text((event_stage_start, 40), f"{info['event_stage']}", fill="black", font=font_sub)

    end_start, end_w = centered_startx(info['status'], width//2, font_sub)
    if info['status'].lower() == 'final':
        draw.text((end_start, 75), f"{info['status']}", fill="gray", font=font_sub)
    elif info['status'].lower() == 'live':
        draw.text(((width//2), 75), f"{info['status']}", fill="red", font=font_sub_bold, anchor='mt')

    bo_start, bo_w = centered_startx(info['bo'], width//2, font_sub)
    draw.text((bo_start, 175), f"{info['bo']}", fill="gray", font=font_sub)


    # 定義區域分隔（地圖資訊起始）
    null1, team1_y = centered_starty(smart_linebreak(info['team1_name'], 13, ' '), 0, font_bold)
    null2, team2_y = centered_starty(smart_linebreak(info['team2_name'], 13, ' '), 0, font_bold)
    map_cont_starty = max((team1_starty + team1_y, team2_starty + team2_y)) + 50


    for i in range(len(maps)):
        cmap = maps[i]
        # 資料匯入
        score1 = cmap.get('score1', 0)
        score2 = cmap.get('score2', 0)
        map_name = cmap.get('map', 'Unknown Map')
        time = cmap.get('time', 'Unknown Time')

        #地圖名稱
        map_startx, map_w = centered_startx(map_name, width//2, font_bold)
        null_map, map_h = centered_startx(map_name, 0, font_bold)
        map_starty = map_cont_starty + (80*i)
        draw.text((map_startx, map_starty), f"{map_name}", fill="black", font=font_bold)

        # 地圖時間
        time_start, time_w = centered_startx(time, width//2, font_content)
        time_starty = map_cont_starty + 40 + (80*i)
        null_time, time_h = centered_starty(time, 0, font_content)
        draw.text((time_start, time_starty), f"{time}", fill="gray", font=font_content)
            
        # 地圖分數
        score1_start, score1_w = centered_startx(score1, 140, font_score)
        score2_start, score2_w = centered_startx(score2, width-140, font_score)
        score_starty, score_h = centered_starty(score1, (map_starty + (time_starty + time_h))//2, font_score )
        y_anchor = ((map_starty + (time_starty + time_h))//2) + 5

        if int(score1) > int(score2) and time != '-':
            draw.text((score1_start, y_anchor), f"{score1}", fill="green", font=font_score, anchor= 'lm')
            draw.text((score2_start, y_anchor), f"{score2}", fill="black", font=font_score, anchor= 'lm')
        elif int(score1) < int(score2) and time != '-':
            draw.text((score1_start, y_anchor), f"{score1}", fill="black", font=font_score, anchor= 'lm')
            draw.text((score2_start, y_anchor), f"{score2}", fill="green", font=font_score, anchor= 'lm')
        else:
            draw.text((score1_start, y_anchor), f"{score1}", fill="black", font=font_score, anchor= 'lm')
            draw.text((score2_start, y_anchor), f"{score2}", fill="black", font=font_score, anchor= 'lm')

        # Veto
        if i == len(maps) - 1:
            veto_start, veto_w = centered_startx(smart_linebreak(info['veto'], 50, ';'), width//2, font_sub)
            null_veto, veto_h = centered_starty(smart_linebreak(info['veto'], 50, ';'), 0, font_sub)
            veto_starty = time_starty + time_h + 50
            veto_endy = veto_starty + veto_h

            if height - veto_endy < 30:
                extend = 30 - (height - veto_endy)
                new_height = height + extend
                new_img = Image.new("RGB", (width, new_height), color=(255, 255, 255))
                new_img.paste(img, (0, 0))  # 將舊圖片貼到新圖上
                img = new_img
                draw = ImageDraw.Draw(img)  # 重新建立繪圖物件
                height = new_height 
                draw.text(((width - veto_w)//2, veto_starty), f"{smart_linebreak(info['veto'], 50, ';')}", fill="gray", font=font_sub)
            else:
                draw.text(((width - veto_w)//2, veto_starty), f"{smart_linebreak(info['veto'], 50, ';')}", fill="gray", font=font_sub)
        
    # 繪製bet.gg賠率
    if status['bet_enabled'] == True:
        bet_info =  data[3]
        bet_bar = generate_odds_chart(bet_info[0], bet_info[1])
        bet_bar = bet_bar.resize((600,75))
        img.paste(bet_bar, (100, map_cont_starty), bet_bar)
        draw.text((110, map_cont_starty -10), text='PRE-GAME BETTING - POWERED BY', fill= 'gray', font= font_note)
        ggbet = requests.get("https://www.vlr.gg/img/pd/ggbet.png")
        ggbet_img = Image.open(BytesIO(ggbet.content)).convert("RGBA")
        ggbet_img = ggbet_img.resize((77, 15))
        img.paste(ggbet_img, (350, map_cont_starty - 8), ggbet_img)
        # 306x60

    # 畫背景格線（方便對齊）
    '''grid_color = (230, 230, 230)  # 淺灰色
    for x in range(0, width, 20):  # 每 20px 畫一條直線
        draw.line([(x, 0), (x, height)], fill=grid_color, width=1, )
    for y in range(0, height, 30):  # 每 30px 畫一條橫線
        draw.line([(0, y), (width, y)], fill=grid_color, width=1)'''


    game_time = info['game_date'] + ', ' + info['sch_time']  # 比賽時間(date and time)

    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer, game_time

#data = scrape_map_stats('https://www.vlr.gg/542196/giantx-vs-sentinels-valorant-champions-2025-opening-a')
#gen_pic(data)
