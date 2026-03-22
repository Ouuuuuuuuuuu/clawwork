"""
重返大明 - 皇帝模拟器
从朱元璋到朱瞻基，历代大明皇帝任你选择
一个高自由度的 AI 驱动文字冒险游戏
"""

import streamlit as st
import random
from datetime import datetime, timedelta
from openai import OpenAI
import json
import copy

# ============== 游戏配置 ==============
GAME_TITLE = "🏯 重返大明"
GAME_SUBTITLE = "历代皇帝模拟器 · 高自由度 AI 驱动"

# ============== 历代皇帝配置 ==============
EMPERORS = {
    "朱元璋": {
        "年号": "洪武",
        "头像": "👴",
        "简介": "明太祖，出身布衣，驱逐鞑虏，恢复中华。开局一个碗，打下大明江山。",
        "初始属性": {"皇权": 90, "民心": 70, "国库": 40, "兵力": 85, "健康": 70},
        "特色": "铁血手腕，猜忌心重，擅长治国但晚年嗜杀",
        "朝臣": ["刘伯温", "徐达", "李善长", "胡惟庸", "蓝玉"]
    },
    "朱允炆": {
        "年号": "建文",
        "头像": "👶",
        "简介": "明惠帝，太祖之孙，生性仁慈，推行宽政，却在靖难之役中下落不明。",
        "初始属性": {"皇权": 60, "民心": 75, "国库": 60, "兵力": 50, "健康": 80},
        "特色": "仁弱君子，不善权谋，面对叔叔们的威胁力不从心",
        "朝臣": ["方孝孺", "黄子澄", "齐泰", "练子宁", "铁铉"]
    },
    "朱棣": {
        "年号": "永乐",
        "头像": "⚔️",
        "简介": "明成祖，靖难夺位，迁都北京，五征漠北，派郑和下西洋，文治武功皆臻极盛。",
        "初始属性": {"皇权": 85, "民心": 80, "国库": 70, "兵力": 90, "健康": 75},
        "特色": "雄才大略，好大喜功，既会打仗也会治国",
        "朝臣": ["姚广孝", "解缙", "杨士奇", "杨荣", "郑和"]
    },
    "朱高炽": {
        "年号": "洪熙",
        "头像": "🧓",
        "简介": "明仁宗，体胖多病，监国多年，即位后施行仁政，为仁宣之治奠定基础。",
        "初始属性": {"皇权": 70, "民心": 85, "国库": 75, "兵力": 60, "健康": 50},
        "特色": "仁厚长者，善于守成，但龙体欠佳，在位仅十月",
        "朝臣": ["杨士奇", "杨荣", "杨溥", "夏原吉", "蹇义"]
    },
    "朱瞻基": {
        "年号": "宣德",
        "头像": "🎨",
        "简介": "明宣宗，太平天子，促织皇帝，开创仁宣之治，爱好书画，是位艺术家皇帝。",
        "初始属性": {"皇权": 75, "民心": 85, "国库": 80, "兵力": 70, "健康": 85},
        "特色": "文武双全，懂得享乐与治国平衡，宣德炉流传千古",
        "朝臣": ["杨士奇", "杨荣", "杨溥", "于谦", "周忱"]
    }
}

# ============== 朝臣配置（按皇帝定制） ==============
OFFICIALS_POOL = {
    # 洪武朝
    "刘伯温": {"职位": "诚意伯", "性格": "神机妙算，深谙帝王心术", "忠诚": 80, "能力": 95, "头像": "🔮", "简介": "开国元勋，神机妙算，通晓天文地理"},
    "徐达": {"职位": "魏国公", "性格": "谨慎稳重，不居功自傲", "忠诚": 95, "能力": 92, "头像": "🎖️", "简介": "开国第一功臣，北伐统帅，军中威望极高"},
    "李善长": {"职位": "韩国公", "性格": "老谋深算，善权谋", "忠诚": 60, "能力": 88, "头像": "🦊", "简介": "开国丞相，淮西集团首领，后与胡惟庸案牵连"},
    "胡惟庸": {"职位": "左丞相", "性格": "专权跋扈，结党营私", "忠诚": 30, "能力": 75, "头像": "🐍", "简介": "独揽相权七年，引发胡惟庸案，导致丞相制度废除"},
    "蓝玉": {"职位": "凉国公", "性格": "勇猛骄横，居功自傲", "忠诚": 50, "能力": 90, "头像": "⚔️", "简介": "捕鱼儿海大捷，封狼居胥，因跋扈被诛"},
    
    # 建文朝
    "方孝孺": {"职位": "翰林学士", "性格": "忠贞不屈，书生意气", "忠诚": 100, "能力": 85, "头像": "📜", "简介": "读书种子，宁死不降燕王，被诛十族"},
    "黄子澄": {"职位": "太常寺卿", "性格": "刚直不阿，缺乏谋略", "忠诚": 95, "能力": 65, "头像": "🎋", "简介": "削藩主谋，忠心可鉴但策略失当"},
    "齐泰": {"职位": "兵部尚书", "性格": "忠诚但急躁", "忠诚": 90, "能力": 70, "头像": "📋", "简介": "参与削藩，城破被俘不屈而死"},
    "练子宁": {"职位": "御史大夫", "性格": "刚正不阿", "忠诚": 95, "能力": 75, "头像": "✍️", "简介": "靖难后不屈，被朱棣处死"},
    "铁铉": {"职位": "山东参政", "性格": "忠烈刚毅", "忠诚": 98, "能力": 85, "头像": "🛡️", "简介": "死守济南，城破后宁死不屈"},
    
    # 永乐朝
    "姚广孝": {"职位": "太子少师", "性格": "深谋远虑，亦僧亦道", "忠诚": 85, "能力": 98, "头像": "🧙", "简介": "黑衣宰相，靖难首功，精通儒释道"},
    "解缙": {"职位": "内阁首辅", "性格": "才华横溢，恃才傲物", "忠诚": 75, "能力": 90, "头像": "📚", "简介": "主编《永乐大典》，因直言被贬"},
    "杨士奇": {"职位": "内阁大学士", "性格": "老成持重，善于调和", "忠诚": 90, "能力": 92, "头像": "🧓", "简介": "三杨之首，历经五朝，四朝元老"},
    "杨荣": {"职位": "内阁大学士", "性格": "敏锐果决，善断", "忠诚": 88, "能力": 90, "头像": "🎯", "简介": "三杨之一，善谋略，多谋善断"},
    "郑和": {"职位": "水师提督", "性格": "胆识过人，见多识广", "忠诚": 95, "能力": 90, "头像": "⚓", "简介": "七下西洋，通使海外，扬我国威"},
    
    # 洪熙/宣德朝
    "杨溥": {"职位": "内阁大学士", "性格": "谨慎持重，廉洁奉公", "忠诚": 92, "能力": 88, "头像": "🕯️", "简介": "三杨之一，历经磨难，忠心不改"},
    "夏原吉": {"职位": "户部尚书", "性格": "清廉持重，善理财", "忠诚": 90, "能力": 92, "头像": "💰", "简介": "理财能手，永乐朝的钱袋子"},
    "蹇义": {"职位": "吏部尚书", "性格": "持重老成", "忠诚": 88, "能力": 85, "头像": "📋", "简介": "主管吏部三十余年，善于用人"},
    "于谦": {"职位": "兵部侍郎", "性格": "刚正不阿，忠烈无双", "忠诚": 98, "能力": 95, "头像": "🛡️", "简介": "社稷之臣，北京保卫战功臣"},
    "周忱": {"职位": "工部侍郎", "性格": "务实能干", "忠诚": 85, "能力": 88, "头像": "🔧", "简介": "治理江南，改革赋税，政绩卓著"},
    
    # 通用名臣（所有朝代可选）
    "海瑞": {"职位": "都察院御史", "性格": "刚正不阿，清廉耿直", "忠诚": 95, "能力": 80, "头像": "👴", "简介": "海青天，敢于直谏，两袖清风"},
    "戚继光": {"职位": "蓟辽总督", "性格": "勇猛善战，忠心耿耿", "忠诚": 90, "能力": 92, "头像": "🎖️", "简介": "抗倭名将，练兵有方，保家卫国"},
    "张居正": {"职位": "内阁首辅", "性格": "精明强干，改革派", "忠诚": 85, "能力": 95, "头像": "🧠", "简介": "一代名相，一条鞭法，富国强兵"},
    "严嵩": {"职位": "礼部尚书", "性格": "阿谀奉承，城府极深", "忠诚": 40, "能力": 75, "头像": "🦊", "简介": "老谋深算，结党营私，需小心提防"},
    "李时珍": {"职位": "太医院院判", "性格": "悬壶济世，淡泊名利", "忠诚": 88, "能力": 90, "头像": "🧑‍⚕️", "简介": "药圣，本草纲目，调理龙体"},
}

# ============== 皇帝属性 ==============
ATTRIBUTES = {
    "皇权": {"icon": "👑", "desc": "朝廷掌控力"},
    "民心": {"icon": "❤️", "desc": "百姓拥护度"},
    "国库": {"icon": "💰", "desc": "银两储备"},
    "兵力": {"icon": "⚔️", "desc": "军队战力"},
    "健康": {"icon": "💪", "desc": "龙体安康"},
}

# ============== 初始化 ==============
def init_game():
    """初始化游戏状态"""
    if "game_state" not in st.session_state:
        st.session_state.game_state = {
            "started": False,
            "emperor_selected": False,
            "emperor": None,
            "year": 1,
            "month": 1,
            "day": 1,
            "attributes": {},
            "officials": {},
            "history": [],
            "current_event": None,
            "messages": [],
            "game_over": False,
            "game_over_reason": None,
            "achievements": [],
        }
    
    if "client" not in st.session_state:
        # 使用 KimiCode API
        api_key = st.secrets.get("kimicode", {}).get("api_key", "")
        st.session_state.client = OpenAI(
            api_key=api_key,
            base_url="https://api.kimicode.com/v1"
        )

def get_llm_response(system_prompt, user_prompt, temperature=0.8):
    """调用 KimiCode API 获取回复"""
    try:
        client = st.session_state.client
        response = client.chat.completions.create(
            model="kimi-k2.5",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=temperature,
            max_tokens=800
        )
        return response.choices[0].message.content
    except Exception as e:
        # 如果 API 调用失败，返回备用回复
        return f"【陛下恕罪，通信有碍】{str(e)[:50]}..."

# ============== 游戏机制 ==============
def setup_emperor(emperor_name):
    """设置皇帝初始状态"""
    emperor = EMPERORS[emperor_name]
    state = st.session_state.game_state
    
    state["emperor"] = emperor_name
    state["attributes"] = {
        "皇权": {"value": emperor["初始属性"]["皇权"], "max": 100},
        "民心": {"value": emperor["初始属性"]["民心"], "max": 100},
        "国库": {"value": emperor["初始属性"]["国库"], "max": 100},
        "兵力": {"value": emperor["初始属性"]["兵力"], "max": 100},
        "健康": {"value": emperor["初始属性"]["健康"], "max": 100},
    }
    
    # 根据皇帝设置朝臣
    state["officials"] = {}
    for official_name in emperor["朝臣"]:
        if official_name in OFFICIALS_POOL:
            state["officials"][official_name] = copy.deepcopy(OFFICIALS_POOL[official_name])
    
    state["emperor_selected"] = True

def advance_time(days=1):
    """推进时间"""
    state = st.session_state.game_state
    state["day"] += days
    
    while state["day"] > 30:
        state["day"] -= 30
        state["month"] += 1
    
    while state["month"] > 12:
        state["month"] -= 12
        state["year"] += 1
        # 每年随机事件
        generate_yearly_event()
    
    # 随机健康衰减
    if random.random() < 0.3:
        decay = random.randint(1, 3)
        state["attributes"]["健康"]["value"] = max(0, state["attributes"]["健康"]["value"] - decay)
    
    check_game_over()

def generate_yearly_event():
    """生成年度事件"""
    emperor = st.session_state.game_state["emperor"]
    
    # 根据不同皇帝有不同的特色事件
    base_events = [
        ("黄河泛滥", "灾情", -10, -15, -5, 0),
        ("边境告急", "战事", 0, -5, -10, -10),
        ("丰收之年", "祥瑞", 5, 10, 5, 0),
        ("科举大考", "朝政", 0, 0, -5, 0),
        ("藩王异动", "危机", -15, 0, -10, -5),
        ("倭寇侵扰", "战事", 0, -8, -5, -8),
        ("天降祥瑞", "祥瑞", 10, 5, 0, 0),
        ("瘟疫流行", "灾情", -5, -20, -10, -15),
    ]
    
    # 皇帝特色事件
    special_events = {
        "朱元璋": [
            ("蓝玉案爆发", "政治", -5, -10, 0, -5),
            ("胡惟庸案", "政治", -10, -5, 0, 0),
            ("空印案", "政治", -5, -10, 0, 0),
        ],
        "朱允炆": [
            ("削藩令下", "危机", -20, 0, -10, -15),
            ("燕王起兵", "战事", -30, -10, -20, -25),
            ("李景隆大败", "战事", -15, -5, -15, -20),
        ],
        "朱棣": [
            ("迁都北京", "朝政", 5, -5, -20, 5),
            ("郑和返航", "祥瑞", 10, 5, 5, 0),
            ("北征大漠", "战事", 5, -5, -30, -10),
            ("编纂大典", "朝政", 5, 5, -15, 0),
        ],
        "朱高炽": [
            ("赦免建文旧臣", "朝政", -5, 10, 0, 0),
            ("停止下西洋", "朝政", 0, 0, 10, 0),
            ("体疾加重", "健康", 0, 0, 0, -20),
        ],
        "朱瞻基": [
            ("促织之戏", "朝政", -5, -5, -5, -5),
            ("平定汉王", "战事", 10, 5, -10, -5),
            ("仁宣之治", "祥瑞", 5, 15, 10, 5),
        ],
    }
    
    if emperor in special_events:
        events = base_events + special_events[emperor]
    else:
        events = base_events
    
    event = random.choice(events)
    state = st.session_state.game_state
    state["current_event"] = {
        "name": event[0],
        "type": event[1],
        "effects": {
            "皇权": event[2],
            "民心": event[3],
            "国库": event[4],
            "兵力": event[5],
        }
    }
    
    # 应用效果
    for attr, change in state["current_event"]["effects"].items():
        if change != 0:
            state["attributes"][attr]["value"] = max(0, min(100, state["attributes"][attr]["value"] + change))
    
    state["history"].append(f"{state['year']}年：{event[0]} ({event[1]})")

def check_game_over():
    """检查游戏结束条件"""
    state = st.session_state.game_state
    attrs = state["attributes"]
    emperor = EMPERORS[state["emperor"]]
    
    # 根据皇帝有不同的结局
    if attrs["健康"]["value"] <= 0:
        if state["emperor"] == "朱高炽":
            state["game_over_reason"] = "龙体欠安，驾崩于钦安殿（在位仅十月，与史实相符）"
        else:
            state["game_over_reason"] = "龙体欠安，驾崩于乾清宫"
        state["game_over"] = True
    elif attrs["皇权"]["value"] <= 0:
        if state["emperor"] == "朱允炆":
            state["game_over_reason"] = "燕王攻入南京，宫中火起，陛下下落不明..."
        else:
            state["game_over_reason"] = "权臣篡位，陛下被软禁于南宫"
        state["game_over"] = True
    elif attrs["民心"]["value"] <= 0:
        state["game_over_reason"] = "民怨沸腾，流寇攻入北京"
        state["game_over"] = True
    elif state["year"] >= 30:
        state["game_over"] = True
        state["game_over_reason"] = f"在位三十载，开创{emperor['年号']}盛世，功德圆满"
    elif state["year"] >= 10 and state["emperor"] == "朱高炽":
        # 朱高炽历史上在位仅10个月，能撑过10年是奇迹
        state["game_over"] = True
        state["game_over_reason"] = f"在位十年，远超预期，创造了洪熙奇迹！"

def get_official_response(official_name, context):
    """获取朝臣的 AI 回复"""
    official = st.session_state.game_state["officials"][official_name]
    state = st.session_state.game_state
    emperor = EMPERORS[state["emperor"]]
    
    system_prompt = f"""你是{emperor['年号']}朝的{official['职位']}{official_name}，{official['简介']}。
你的性格：{official['性格']}。
忠诚值：{official['忠诚']}/100，能力值：{official['能力']}/100。

当前是{emperor['年号']}{state['year']}年{state['month']}月，{state['emperor']}陛下咨询朝政。
请用古雅文言或半文言回复，保持角色一致性，体现你的性格特点。
如果忠诚低，可能阳奉阴违；如果能力强，建议切中肯綮。
注意：你是{emperor['年号']}朝的人，不要提及其他朝代的人或事。"""
    
    return get_llm_response(system_prompt, context)

def get_emperor_decision_context():
    """获取皇帝决策上下文"""
    state = st.session_state.game_state
    emperor = EMPERORS[state["emperor"]]
    
    context = f"""当前局势：
- 皇帝：{state['emperor']}（{emperor['特色']}）
- 年号：{emperor['年号']}{state['year']}年{state['month']}月{state['day']}日
- 皇权：{state['attributes']['皇权']['value']}/100
- 民心：{state['attributes']['民心']['value']}/100
- 国库：{state['attributes']['国库']['value']}/100
- 兵力：{state['attributes']['兵力']['value']}/100
- 健康：{state['attributes']['健康']['value']}/100
"""
    
    if state["current_event"]:
        context += f"\n【紧急事件】{state['current_event']['name']} ({state['current_event']['type']})"
    
    return context

# ============== UI 组件 ==============
def render_header():
    """渲染标题"""
    st.title(GAME_TITLE)
    st.caption(GAME_SUBTITLE)
    
    state = st.session_state.game_state
    if state["started"] and state["emperor"]:
        emperor = EMPERORS[state["emperor"]]
        
        # 显示皇帝信息
        cols = st.columns([1, 4])
        with cols[0]:
            st.markdown(f"### {emperor['头像']} {state['emperor']}")
            st.caption(f"{emperor['年号']}{state['year']}年")
        with cols[1]:
            # 属性条
            attr_cols = st.columns(5)
            for i, (attr_name, attr_data) in enumerate(state["attributes"].items()):
                with attr_cols[i]:
                    icon = ATTRIBUTES[attr_name]["icon"]
                    value = attr_data["value"]
                    # 根据数值显示颜色
                    if value >= 70:
                        color = "🟢"
                    elif value >= 40:
                        color = "🟡"
                    else:
                        color = "🔴"
                    st.metric(f"{icon} {attr_name}", f"{color} {value}")
        
        st.divider()

def render_emperor_selection():
    """渲染皇帝选择界面"""
    st.markdown("""
    ## 👑 选择你的帝王身份
    
    从洪武到宣德，五位大明皇帝任你选择。每位皇帝都有独特的初始属性和历史背景。
    """)
    
    cols = st.columns(len(EMPERORS))
    
    for i, (name, info) in enumerate(EMPERORS.items()):
        with cols[i]:
            with st.container(border=True):
                st.markdown(f"### {info['头像']} {name}")
                st.caption(f"**{info['年号']}**")
                st.write(info['简介'][:50] + "...")
                st.write(f"🎭 **特色**：{info['特色']}")
                
                # 显示初始属性
                st.write("📊 **初始属性**：")
                for attr, val in info['初始属性'].items():
                    bar = "█" * (val // 10) + "░" * (10 - val // 10)
                    st.caption(f"{ATTRIBUTES[attr]['icon']} {bar} {val}")
                
                if st.button(f"选择 {name}", key=f"select_{name}", use_container_width=True):
                    setup_emperor(name)
                    st.session_state.game_state["started"] = True
                    
                    # 开场白
                    welcome_msg = {
                        "role": "assistant",
                        "content": f"""
🏯 **{info['年号']}登基大典**

奉天承运，皇帝诏曰：

朕**{name}**，今日登基，改元**{info['年号']}**，大赦天下。

{info['简介']}

朕当谨记：**{info['特色']}**

钦此。

---

💡 **提示**：您可以：
1. 点击左侧朝臣名字，召见询问政事
2. 处理突发的事件
3. 批阅奏折处理国政
4. 微服私访体察民情
5. 在下方输入框自由发号施令

请陛下吩咐！
                        """
                    }
                    st.session_state.game_state["messages"].append(welcome_msg)
                    st.rerun()

def render_welcome():
    """渲染欢迎页面"""
    st.markdown("""
    ## 📜 游戏背景
    
    你本是现代一名普通程序员，某日加班至深夜，突然眼前一黑...
    
    醒来时，你发现自己身着龙袍，坐在大明皇宫的龙椅上！
    
    太监总管跪禀："陛下，您终于醒了！今日有大朝会，文武百官已在午门外等候。"
    
    你竟然穿越成了大明皇帝！
    
    ## 🎮 游戏特色
    
    - **多皇帝选择**：从朱元璋到朱瞻基，体验不同皇帝的治国之路
    - **朝代专属**：每位皇帝有独特的朝臣班子和特色事件
    - **AI 驱动**：每位臣子都有独特性格，由 AI 实时生成对话
    - **历史还原**：靖难之役、郑和下西洋、仁宣之治...亲历历史大事件
    - **多结局**：明君、昏君、亡国之君...你的选择决定历史
    
    ## ⚠️ 生存法则
    
    - **皇权**不能太低，否则会被权臣架空或被篡位
    - **民心**不能太低，否则会被农民起义推翻
    - **国库**不能空虚，否则发不出军饷
    - **兵力**要足够，否则外敌入侵无力抵抗
    - **健康**最重要，龙体欠安则万事皆休（某些皇帝体质较差，需特别注意）
    """)
    
    if st.button("🐉 开始游戏", type="primary", use_container_width=True):
        st.session_state.game_state["selecting_emperor"] = True
        st.rerun()

def render_game_over():
    """渲染游戏结束"""
    state = st.session_state.game_state
    emperor = EMPERORS[state["emperor"]]
    
    st.error("## 🏴 游戏结束")
    st.markdown(f"""
    ### {state['game_over_reason']}
    
    **皇帝**：{emperor['头像']} {state['emperor']}
    **在位时间**：{emperor['年号']}{state['year']}年{state['month']}月
    **历史评价**：
    """)
    
    # 根据属性评价
    attrs = state["attributes"]
    avg_score = sum(a["value"] for a in attrs.values()) / len(attrs)
    
    # 根据皇帝不同有不同的评价标准
    if state["emperor"] == "朱允炆":
        # 朱允炆历史上失败，能坚持越久越厉害
        if state["year"] >= 4:
            st.success("🏆 奇迹！您成功避免了靖难之役，改写了历史！")
        elif avg_score >= 50:
            st.info("📜 虽败犹荣，至少比历史上的建文帝多撑了一段时间...")
        else:
            st.error("💀 与史实一样，被叔叔赶下了台...")
    elif state["emperor"] == "朱高炽":
        # 朱高炽在位短，能长寿就是胜利
        if state["year"] >= 5:
            st.success("🏆 医学奇迹！您活过了预期，创造了新的历史！")
        elif avg_score >= 60:
            st.info("📜 守成之君，为仁宣之治奠定基础")
        else:
            st.error("💀 与史实一样，在位不到一年就驾崩了...")
    else:
        if avg_score >= 70:
            st.success("🏆 千古一帝！您开创了盛世，万民景仰，流芳百世！")
        elif avg_score >= 50:
            st.info("📜 守成之君。您维持了社稷稳定，无功无过，平平无奇。")
        else:
            st.error("💀 亡国之君。您的昏庸导致天下大乱，历史将铭记您的教训。")
    
    st.markdown("### 📚 在位大事记")
    for event in state["history"][-15:]:
        st.write(f"- {event}")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 重新开始", type="primary", use_container_width=True):
            del st.session_state.game_state
            if "client" in st.session_state:
                del st.session_state.client
            st.rerun()
    with col2:
        if st.button("👑 换一位皇帝", use_container_width=True):
            st.session_state.game_state["game_over"] = False
            st.session_state.game_state["started"] = False
            st.session_state.game_state["emperor_selected"] = False
            st.session_state.game_state["selecting_emperor"] = True
            st.session_state.game_state["messages"] = []
            st.session_state.game_state["history"] = []
            st.rerun()

def render_sidebar():
    """渲染侧边栏"""
    with st.sidebar:
        state = st.session_state.game_state
        emperor = EMPERORS[state["emperor"]]
        
        st.header(f"{emperor['头像']} {state['emperor']}朝廷")
        
        st.subheader("📅 时间")
        st.write(f"{emperor['年号']}{state['year']}年 {state['month']}月 {state['day']}日")
        
        st.divider()
        
        st.subheader("👥 召见大臣")
        for name, info in state["officials"].items():
            btn_text = f"{info['头像']} {name}"
            if st.button(btn_text, key=f"official_{name}", help=f"{info['职位']} | 忠诚:{info['忠诚']} 能力:{info['能力']}"):
                st.session_state.selected_official = name
                st.session_state.show_official_chat = True
                st.rerun()
        
        st.divider()
        
        st.subheader("⚡ 快捷操作")
        if st.button("📝 批阅奏折"):
            st.session_state.show_memorial = True
            st.rerun()
        if st.button("🎲 微服私访"):
            st.session_state.show_travel = True
            st.rerun()
        if st.button("🏰 回宫休息"):
            rest()
        
        st.divider()
        
        st.subheader("📜 历史")
        for event in state["history"][-5:]:
            st.caption(event)

def rest():
    """休息恢复"""
    state = st.session_state.game_state
    emperor = EMPERORS[state["emperor"]]
    
    # 不同皇帝休息效果不同
    if state["emperor"] == "朱高炽":
        heal = 15  # 体弱的仁宗更需要休息
    elif state["emperor"] == "朱棣":
        heal = 8   # 永乐大帝精力旺盛，休息恢复慢
    else:
        heal = 10
    
    state["attributes"]["健康"]["value"] = min(100, state["attributes"]["健康"]["value"] + heal)
    advance_time(1)
    
    msg = {
        "role": "assistant",
        "content": f"🌙 陛下回宫歇息，龙体有所恢复。健康 +{heal}"
    }
    state["messages"].append(msg)
    st.rerun()

def render_official_chat():
    """渲染与大臣对话"""
    if not st.session_state.get("show_official_chat"):
        return
    
    official_name = st.session_state.get("selected_official")
    if not official_name:
        return
    
    official = st.session_state.game_state["officials"][official_name]
    emperor = EMPERORS[st.session_state.game_state["emperor"]]
    
    with st.container(border=True):
        st.markdown(f"### {official['头像']} 召见 {official_name}")
        st.caption(f"**{official['职位']}** | {official['简介']}")
        st.write(f"🎯 忠诚:{official['忠诚']} | 能力:{official['能力']} | 性格:{official['性格']}")
        
        # 对话选项
        cols = st.columns(3)
        with cols[0]:
            if st.button("📊 询问国事", key=f"ask_state_{official_name}"):
                with st.spinner("大臣思考中..."):
                    context = get_emperor_decision_context()
                    response = get_official_response(official_name, f"陛下问：{official_name}，如今国事如何？请详细禀报。\n\n{context}")
                    add_message("assistant", f"**{official['头像']} {official_name}**：\n\n{response}")
                st.rerun()
        with cols[1]:
            if st.button("💡 求取建议", key=f"ask_advice_{official_name}"):
                with st.spinner("大臣思考中..."):
                    context = get_emperor_decision_context()
                    response = get_official_response(official_name, f"陛下问：如今面临此局势，卿有何良策？\n\n{context}")
                    add_message("assistant", f"**{official['头像']} {official_name}**：\n\n{response}")
                st.rerun()
        with cols[2]:
            if st.button("🎁 赏赐/问责", key=f"reward_{official_name}"):
                with st.spinner("大臣思考中..."):
                    response = get_official_response(official_name, "陛下表示要赏赐/问责你，请根据你的忠诚度和性格做出回应。")
                    add_message("assistant", f"**{official['头像']} {official_name}**：\n\n{response}")
                st.rerun()
        
        if st.button("❌ 结束召见", key=f"close_official_{official_name}"):
            st.session_state.show_official_chat = False
            st.rerun()

def render_memorial():
    """渲染批阅奏折"""
    if not st.session_state.get("show_memorial"):
        return
    
    state = st.session_state.game_state
    emperor = EMPERORS[state["emperor"]]
    
    # 根据皇帝生成不同特色的奏折
    memorial_pool = {
        "朱元璋": [
            ("蓝玉跋扈", "凉国公蓝玉居功自傲，在军中擅权，请陛下圣裁。"),
            ("科举南北榜", "北方士子抗议科举不公，要求分南北榜取士。"),
            ("藩王请兵", "各地藩王请求增兵护卫，恐有不臣之心。"),
        ],
        "朱允炆": [
            ("燕王异动", "燕王朱棣在北平操练兵马，似有反意。"),
            ("削藩之策", "齐泰、黄子澄上书请求削藩，以固皇权。"),
            ("李景隆请战", "曹国公李景隆请率大军北伐燕王。"),
        ],
        "朱棣": [
            ("迁都事宜", "姚广孝建议正式迁都北京，以天子守国门。"),
            ("郑和返航", "郑和第七次下西洋归来，带回各国贡品。"),
            ("北征蒙古", "鞑靼部犯边，请旨是否亲征漠北。"),
            ("大典编纂", "《永乐大典》编纂完成，请陛下御览。"),
        ],
        "朱高炽": [
            ("赦免建文旧臣", "有大臣建议赦免建文帝旧臣，以宽仁示天下。"),
            ("停止下西洋", "有大臣建议停止郑和下西洋，以节省国库。"),
            ("迁都回南京", "有大臣建议迁回南京，以免北京苦寒。"),
        ],
        "朱瞻基": [
            ("汉王异动", "汉王朱高煦在乐安州有不臣之举。"),
            ("促织之戏", "宫中太监进贡蟋蟀，请陛下消遣。"),
            ("仁宣之治", "各地奏报民殷国富，请陛下继续仁政。"),
        ],
    }
    
    # 通用奏折
    common_memorials = [
        ("边疆军情", "辽东急报，女真部族蠢蠢欲动，请陛下决断。"),
        ("财政奏销", "户部奏请清查全国田亩，推行一条鞭法。"),
        ("官员任免", "吏部呈递本年度京察名单，请圣裁。"),
        ("灾荒赈济", "河南大旱，流民四起，恳请开仓放粮。"),
        ("外交事务", "海外使团抵达，请求通商贸易。"),
    ]
    
    if state["emperor"] in memorial_pool:
        all_memorials = memorial_pool[state["emperor"]] + common_memorials
    else:
        all_memorials = common_memorials
    
    topic, content = random.choice(all_memorials)
    
    with st.container(border=True):
        st.markdown(f"### 📝 奏折：{topic}")
        st.info(content)
        
        cols = st.columns(2)
        with cols[0]:
            if st.button("✅ 准奏", key="approve_memorial"):
                result = handle_memorial_decision(topic, True)
                add_message("assistant", result)
                st.session_state.show_memorial = False
                advance_time(1)
                st.rerun()
        with cols[1]:
            if st.button("❌ 驳回", key="reject_memorial"):
                result = handle_memorial_decision(topic, False)
                add_message("assistant", result)
                st.session_state.show_memorial = False
                advance_time(1)
                st.rerun()

def handle_memorial_decision(topic, approved):
    """处理奏折决策"""
    state = st.session_state.game_state
    emperor = EMPERORS[state["emperor"]]
    
    # 根据皇帝有不同的决策效果
    effects_map = {
        "朱元璋": {
            "蓝玉跋扈": {"皇权": 10, "兵力": -15} if approved else {"皇权": -10, "兵力": 5},
            "科举南北榜": {"民心": 10, "皇权": 5} if approved else {"民心": -15},
        },
        "朱允炆": {
            "燕王异动": {"皇权": -20, "兵力": -20} if approved else {"皇权": -30, "兵力": -10},
            "削藩之策": {"皇权": 15, "兵力": -20} if approved else {"皇权": -10},
        },
        "朱棣": {
            "迁都事宜": {"皇权": 10, "民心": -5, "国库": -15} if approved else {"皇权": -5},
            "北征蒙古": {"皇权": 5, "兵力": -20, "国库": -20} if approved else {"皇权": -5, "兵力": 5},
        },
    }
    
    # 默认效果
    default_effects = {
        "边疆军情": {"皇权": 5, "兵力": -10, "国库": -10} if approved else {"皇权": -5, "兵力": -5},
        "财政奏销": {"皇权": 5, "国库": 10, "民心": -5} if approved else {"皇权": -3},
        "官员任免": {"皇权": 3} if approved else {"皇权": -2},
        "灾荒赈济": {"民心": 10, "国库": -10} if approved else {"民心": -10},
        "外交事务": {"国库": 5, "皇权": 2} if approved else {"皇权": -2},
    }
    
    # 查找效果
    effect = {}
    if state["emperor"] in effects_map and topic in effects_map[state["emperor"]]:
        effect = effects_map[state["emperor"]][topic]
    elif topic in default_effects:
        effect = default_effects[topic]
    
    result_text = f"**批阅结果**：{'准奏' if approved else '驳回'}\n\n"
    
    for attr, change in effect.items():
        state["attributes"][attr]["value"] = max(0, min(100, state["attributes"][attr]["value"] + change))
        if change > 0:
            result_text += f"- {attr} +{change}\n"
        else:
            result_text += f"- {attr} {change}\n"
    
    state["history"].append(f"{state['year']}年{state['month']}月：批阅{topic}奏折")
    
    return result_text

def render_travel():
    """渲染微服私访"""
    if not st.session_state.get("show_travel"):
        return
    
    state = st.session_state.game_state
    emperor = EMPERORS[state["emperor"]]
    
    # 根据皇帝有不同的微服私访事件
    travel_events = {
        "朱元璋": [
            ("微服访贫", "在凤阳老家见到昔日贫农，感慨万千。", {"民心": 10, "健康": 5}),
            ("杀贪官", "当场抓获贪官污吏，下令剥皮实草。", {"民心": 15, "皇权": 5, "健康": -5}),
        ],
        "朱允炆": [
            ("书院论道", "在应天书院与读书人论政，颇受好评。", {"民心": 10, "皇权": -5}),
            ("偶遇藩王", "在街头偶遇化装的藩王叔父，尴尬相对。", {"皇权": -10, "健康": -5}),
        ],
        "朱棣": [
            ("校场阅兵", "在郊区校场观看禁军操练，龙颜大悦。", {"兵力": 10, "健康": 5}),
            ("寻访建文", "暗中寻访建文帝下落，无果而终。", {"皇权": -5, "健康": -5}),
        ],
        "朱高炽": [
            ("体察民情", "在街头见到百姓安居乐业，甚感欣慰。", {"民心": 10, "健康": -5}),
            ("接见读书人", "在翰林院与文臣论政，共商国是。", {"皇权": 5, "健康": -5}),
        ],
        "朱瞻基": [
            ("斗蟋蟀", "在市井见到上好蟋蟀，龙颜大悦。", {"健康": 10, "民心": -5, "皇权": -5}),
            ("书画鉴赏", "在古玩店鉴赏书画，流连忘返。", {"健康": 5, "民心": -3}),
        ],
    }
    
    # 通用事件
    common_events = [
        ("偶遇清官", "在乡间遇到一位为民做主的好官，百姓交口称赞。", {"民心": 5, "皇权": 3}),
        ("贪官污吏", "发现地方官员横征暴敛，民不聊生。", {"民心": -5, "皇权": 5}),
        ("才子佳人", "偶遇才女吟诗作对，传为佳话。", {"健康": 5}),
        ("江湖骗子", "被江湖术士骗去银两。", {"国库": -5, "健康": -3}),
        ("民间疾苦", "亲眼见到百姓生活艰辛，深受触动。", {"民心": 10, "健康": -5}),
    ]
    
    if state["emperor"] in travel_events:
        all_events = travel_events[state["emperor"]] + common_events
    else:
        all_events = common_events
    
    event = random.choice(all_events)
    
    with st.container(border=True):
        st.markdown(f"### 🎲 微服私访：{event[0]}")
        st.info(event[1])
        
        if st.button("🏰 返回宫中", key="return_from_travel"):
            for attr, change in event[2].items():
                state["attributes"][attr]["value"] = max(0, min(100, state["attributes"][attr]["value"] + change))
            
            result_text = "**游历结果**：\n\n"
            for attr, change in event[2].items():
                if change > 0:
                    result_text += f"- {attr} +{change}\n"
                else:
                    result_text += f"- {attr} {change}\n"
            
            state["history"].append(f"{state['year']}年{state['month']}月：微服私访，{event[0]}")
            add_message("assistant", result_text)
            st.session_state.show_travel = False
            advance_time(5)
            st.rerun()

def add_message(role, content):
    """添加消息到历史"""
    st.session_state.game_state["messages"].append({
        "role": role,
        "content": content
    })

def render_chat():
    """渲染聊天界面"""
    state = st.session_state.game_state
    emperor = EMPERORS[state["emperor"]]
    
    # 显示消息历史
    for msg in state["messages"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    
    # 输入框
    if prompt := st.chat_input("陛下有何吩咐..."):
        add_message("user", prompt)
        
        # AI 生成回复
        system_prompt = f"""你是{emperor['年号']}朝的宫廷太监总管，负责协助{state['emperor']}陛下处理日常事务。
当前局势：{get_emperor_decision_context()}
请以恭敬但略带幽默的语气回复，可以引用历史典故，但保持轻松有趣。
回复要简短（100字以内），不要长篇大论。
注意：不要提及其他朝代或未来的事。"""
        
        with st.spinner("总管思考中..."):
            response = get_llm_response(system_prompt, prompt)
        
        add_message("assistant", response)
        
        advance_time(1)
        st.rerun()

# ============== 主程序 ==============
def main():
    init_game()
    
    render_header()
    
    state = st.session_state.game_state
    
    if not state["started"]:
        if state.get("selecting_emperor"):
            render_emperor_selection()
        else:
            render_welcome()
    elif state["game_over"]:
        render_game_over()
    else:
        render_sidebar()
        
        # 显示当前事件
        if state["current_event"]:
            st.warning(f"🚨 **紧急事件**：{state['current_event']['name']} ({state['current_event']['type']})")
            cols = st.columns(2)
            with cols[0]:
                if st.button("✅ 立即处理"):
                    state["current_event"] = None
                    add_message("assistant", "陛下英明，此事已妥善处理。")
                    advance_time(1)
                    st.rerun()
            with cols[1]:
                if st.button("⏳ 稍后再议"):
                    pass
        
        render_official_chat()
        render_memorial()
        render_travel()
        
        st.divider()
        render_chat()

if __name__ == "__main__":
    main()
