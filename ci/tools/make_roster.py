#!/usr/bin/env python3
"""Build data/residents.json (the fixed roster of the town's 790 homes) from
data/resident_faces.json.

usage: make_roster.py <game dir>

Every face r0001..r1396 is one resident. Families are formed from age and sex
(children with parents of a fitting age, couples of a similar age, people on
their own), placed in the five residential areas, and given names that fit
their generation, a shared surname per household, a temperament that has
nothing to do with how they look, and a one-line story. The result is fixed:
the same input always gives the same roster.
"""
import json, random, sys, collections

G = sys.argv[1]
rng = random.Random(14935)
faces = json.load(open(f"{G}/data/resident_faces.json", encoding="utf-8"))

AREAS = {"団地": 300, "駅前のマンション": 120, "北の住宅街": 150, "南の住宅街": 120, "住宅街": 100}
HOMES = sum(AREAS.values())

# ---------------------------------------------------------------- names
NAMES = {
 "m": [
  (12, "蓮 陽翔 湊 蒼 樹 大和 悠真 朝陽 碧 律 颯真 陽太 結翔 奏太 蒼空 新 暖 伊織 瑛太 晴 岳 陸 航 悠人 遥斗 壮真 大翔 湊斗 結人 蒼介"),
  (17, "大翔 悠斗 陽向 翔 颯太 拓海 悠 優斗 陸斗 隼 海斗 晴翔 健太 颯 智也 光 優太 琉生 奏 蒼真 一輝 想 春輝 瑛斗"),
  (24, "翔太 拓海 大輝 海斗 優斗 颯太 隼人 翔 涼 駿 直人 航平 雄大 拓真 亮太 龍之介 和真 将吾 晃大 瑞樹 健斗 啓介"),
  (34, "大輔 拓也 健太 達也 雄太 亮 大樹 直樹 和也 洋平 慎也 祐介 貴之 啓太 将太 陽介 智也 圭佑 優 翔平 雅人 純也"),
  (49, "誠 拓也 直樹 健一 和也 剛 隆之 浩之 達也 智之 秀樹 健太郎 聡 崇 雅樹 英樹 康弘 哲也 竜也 学 亮介 淳"),
  (64, "浩 誠 隆 博之 正人 修 健二 和彦 茂樹 浩二 秀樹 稔 弘 徹 克也 正樹 伸一 敏之 雅彦 俊介 孝 晃"),
  (79, "博 茂 実 清 勝 進 武 正 昭 豊 勉 修 明 隆 和夫 幸雄 輝男 敏夫 正義 光男 秀夫 弘"),
  (200, "正雄 清 勇 実 茂 三郎 勝 武雄 義雄 進 一郎 重雄 栄 静雄 昭二 秀雄 健蔵 治 寛 久雄 金次郎 留吉"),
 ],
 "f": [
  (12, "陽葵 凛 結菜 紬 芽依 澪 葵 咲良 結衣 杏 莉子 美月 心春 柚葉 詩 琴音 花 楓 陽菜 一花 美桜 彩葉 結愛 千夏"),
  (17, "陽菜 結衣 結愛 美咲 さくら 凛 美羽 心愛 彩花 莉子 七海 優奈 花音 美優 杏奈 遥 未来 菜々子 愛莉 日向 真央 柚"),
  (24, "美咲 葵 七海 彩 遥 優花 菜摘 千尋 沙耶 萌 栞 舞 愛 夏美 明日香 杏 瑞希 茜 若菜 彩乃 実結 美玖"),
  (34, "美咲 彩 愛 舞 沙織 麻衣 千尋 茜 瞳 恵 理沙 由佳 奈々 早紀 智美 綾 香織 優子 真由 亜美 美穂 愛美"),
  (49, "恵 久美子 由美 智子 真由美 香織 裕子 直美 陽子 美穂 明美 美紀 亜希子 典子 純子 さやか 京子 理恵 千秋 由紀 麻美 志保"),
  (64, "由美子 恵子 久美子 裕子 真理子 洋子 直子 幸子 典子 和子 啓子 美智子 明美 順子 京子 悦子 弘美 薫 敦子 雅子 千代美 文子"),
  (79, "和子 幸子 節子 洋子 恵子 京子 美智子 悦子 弘子 久子 良子 静子 信子 照子 佳子 富美子 敏子 道子 光子 栄子 君子 紀子"),
  (200, "キヨ ハル フミ トシ ヨシ 千代 澄子 静江 春子 美代子 八重子 貞子 久江 初江 光江 ミツ タケ 喜美子 照代 房子 ツル ウメ"),
 ],
}
NAMES = {s: [(lim, n.split()) for lim, n in v] for s, v in NAMES.items()}

SURNAMES = """佐藤 鈴木 高橋 田中 伊藤 渡辺 山本 中村 小林 加藤 吉田 山田 佐々木 山口 松本 井上 木村 林 斎藤 清水
山崎 森 池田 橋本 阿部 石川 山下 中島 石井 小川 前田 岡田 長谷川 藤田 後藤 近藤 村上 遠藤 青木 坂本
斉藤 福田 太田 西村 藤井 金子 岡本 藤原 中野 三浦 原田 中川 松田 竹内 小野 田村 中山 和田 石田 森田
上田 原 内田 柴田 酒井 宮崎 横山 高木 安藤 宮本 大野 小島 工藤 谷口 今井 高田 丸山 増田 杉山 村田
大塚 小山 平野 藤本 河野 上野 野口 武田 松井 千葉 岩崎 菅原 木下 久保 佐野 野村 松尾 市川 菊地 杉本
古川 大西 島田 水野 桜井 高野 渡部 吉川 山内 西田 飯田 菊池 西川 小松 北村 安田 五十嵐 川口 平田 関
中田 久保田 服部 東 岩田 土屋 川崎 福島 本田 辻 樋口 秋山 田口 永井 山中 中西 吉村 川上 石原 大橋
松岡 馬場 浅野 荒木 大久保 野田 小沢 田辺 川村 星野 黒田 堀 尾崎 望月 永田 熊谷 内藤 松村 西山 大谷
平井 大島 岩本 片山 本間 早川 横田 岡崎 荒井 大石 鎌田 成田 宮田 小田 石橋 篠原 須藤 河合 高山 吉岡
佐伯 森下 大川 戸田""".split()
# a little more weight on the very common names, none used more than 8 times
SUR_W = [3 if k < 20 else 2 if k < 60 else 1 for k in range(len(SURNAMES))]
sur_used = collections.Counter()

def surname():
    while True:
        s = rng.choices(SURNAMES, SUR_W)[0]
        if sur_used[s] < 8:
            sur_used[s] += 1
            return s

used_full = set()
def given(sex, age, sur, taken):
    for lim, pool in NAMES[sex]:
        if age <= lim:
            break
    for _ in range(50):
        n = rng.choice(pool)
        if n not in taken and (sur, n) not in used_full:
            used_full.add((sur, n))
            return n
    return rng.choice(pool)

# ---------------------------------------------------------------- traits and stories
TRAITS_ADULT = """几帳面 心配性 世話好き 頑固 人見知り 陽気 口数が少ない 短気 おおらか 慎重 好奇心が強い 面倒見がいい
意地っ張り 涙もろい 楽観的 神経質 律儀 気が強い のんびり屋 正義感が強い 皮肉屋 臆病 手先が器用 物知り 噂好き
負けず嫌い 照れ屋 落ち着いている せっかち 頼りになる 疑り深い 人当たりがいい 無愛想 しっかり者 お人好し""".split()
TRAITS_CHILD = """元気 人見知り 甘えん坊 しっかり者 泣き虫 おしゃべり 恥ずかしがり 負けず嫌い 好奇心が強い
おっとり いたずら好き 優しい 怖がり 物静か 生意気 素直 マイペース 頑張り屋""".split()

JOBS = """営業の会社員 経理の会社員 総務の会社員 介護士 看護師 配送ドライバー 工場勤務 市役所の職員 小学校の先生
スーパーのパート 美容師 大工 電気工事士 保育士 歯科衛生士 八百屋の店主 居酒屋の店員 タクシー運転手 在宅のプログラマー
郵便局員 銀行員 薬局の事務 警備員 塾講師 清掃員 調理師 自動車整備士 家事を切り盛りしている 求職中 農協の職員
フリーのデザイナー 運送会社の配車係 病院の事務 クリーニング屋の店員 ホームセンターの店員 不動産屋の営業""".split()
RETIRED = """元は町工場の職人 元は国鉄の駅員 元は小学校の先生 元は商店街で魚屋をしていた 元は看護師 元は役場の職員
元は大工 元は会社の経理 元は自転車屋 元はバスの運転手 元は保険の外交員 元は郵便配達 元は和裁の仕立て
元は食堂を営んでいた 元は銀行員 元は田んぼをやっていた 専業で家を守ってきた 元は電器屋""".split()
HOBBY = "盆栽 囲碁 家庭菜園 俳句 朝の散歩 川釣り 書道 カラオケ 編み物 将棋 ラジオ体操 庭いじり 写経 詩吟 園芸".split()
STUDY = """大学で経済を学んでいる 大学で看護を学んでいる 専門学校で調理を学んでいる 美容の専門学校に通っている
大学で建築を学んでいる 浪人中で予備校に通っている 大学の工学部に通っている 専門学校で介護を学んでいる
大学で文学を学んでいる コンビニで夜勤のアルバイトをしている 大学の教育学部に通っている 専門学校で情報処理を学んでいる""".split()
CLUB = "野球部 サッカー部 吹奏楽部 陸上部 バスケ部 美術部 剣道部 卓球部 帰宅部 バレー部 写真部 将棋部".split()
LIKES = "虫取り 絵を描くこと 電車 恐竜の図鑑 サッカー 折り紙 ゲーム 料理のお手伝い 一輪車 読書 縄跳び 工作".split()

ADULT_TAIL = """朝早く家を出て、夜遅く帰る。 近所づきあいは挨拶程度。 休みの日は釣りに出かける。 町内会の役員を引き受けている。
最近、体力の衰えを気にしている。 車が好きで、休日は洗車をしている。 料理が得意で、近所におすそ分けをする。
地元の消防団に入っている。 夜勤明けは昼まで寝ている。 ベランダで野菜を育てている。 前の職場を辞めて、この町に戻ってきた。
親の介護で実家と行き来している。 犬の散歩が日課。 口には出さないが、貯金をこつこつ続けている。
ジョギングが日課。 手先が器用で、近所の修理を頼まれる。""".split()
SENIOR_TAIL = """連れ合いを数年前に亡くした。 遠くに住む子どもから毎週電話がある。 膝が悪く、階段がつらい。
朝は誰よりも早く起きる。 近所の子どもに飴を配るのが楽しみ。 若い頃の話になると止まらない。
薬を何種類も飲んでいる。 町のことなら何でも知っている。 戦後の食べ物のない時代を覚えている。 物を捨てられない。""".split()

def trait(age):
    return rng.choice(TRAITS_CHILD if age < 13 else TRAITS_ADULT)

def story(p, role, h):
    a = p["age"]
    if a < 13:
        return f"小学{max(1, min(6, a - 6))}年生。{rng.choice(LIKES)}が好き。"
    if a < 18:
        school = f"中学{a - 12}年生" if a <= 15 else f"高校{a - 15}年生"
        return f"{school}。{rng.choice(CLUB)}。"
    if role == "child":
        return rng.choice(["大学に通いながら実家で暮らしている。", "高校を出て、地元で働きはじめた。", "就職先を探しながら実家にいる。", "専門学校に通っている。"])
    if role == "student":
        return f"{rng.choice(STUDY)}。" + rng.choice(["一人暮らしは二年目。", "実家は遠い。", "仕送りは少ない。", "", ""])
    if a >= 65:
        return f"{rng.choice(RETIRED)}。{rng.choice(HOBBY)}が趣味。" + rng.choice(SENIOR_TAIL if role != "couple" else SENIOR_TAIL[1:])
    if role == "grand":
        return f"{rng.choice(RETIRED)}。孫の世話をしている。"
    job = rng.choice(JOBS + (["定年後も再雇用で働いている", "早めに仕事を辞めた"] * 4 if a >= 60 else []))
    tails = [t for t in ADULT_TAIL if a >= 45 or "衰え" not in t]
    if h in ("子どものいる家族", "共働きの夫婦"):
        tails = [t for t in tails if "ベランダ" not in t] if rng.random() < 0.5 else tails
    return f"{job}。{rng.choice(tails)}"

def band(age, role):
    if age < 18:
        return "child"
    if age < 25:
        return "young"
    if age >= 65 or role == "grand":
        return "senior"
    return "adult"

# ---------------------------------------------------------------- families
pool = {f["id"]: f for f in faces}
free = set(pool)
def take(i):
    free.remove(i)
    return dict(pool[i])

def pick(sex, lo, hi, prefer=None):
    c = [i for i in free if pool[i]["sex"] == sex and lo <= pool[i]["age"] <= hi]
    if not c:
        return None
    if prefer is not None:
        c.sort(key=lambda i: abs(pool[i]["age"] - prefer) + rng.random() * 6)
        return c[0]
    return rng.choice(c)

homes = []
# children under 18, and some 18-21s who still live with their parents
kids = sorted([i for i in free if pool[i]["age"] < 18], key=lambda i: pool[i]["age"])
older = [i for i in free if 18 <= pool[i]["age"] <= 21]
rng.shuffle(older)
kids += older[:30]
rng.shuffle(kids)
groups = []
while kids:
    n = rng.choices([1, 2, 3], [40, 47, 13])[0]
    g = [kids.pop()]
    for _ in range(n - 1):
        near = [k for k in kids if abs(pool[k]["age"] - pool[g[0]]["age"]) <= 7]
        if not near:
            break
        k = rng.choice(near)
        kids.remove(k)
        g.append(k)
    groups.append(g)

for g in groups:
    for k in g:
        free.discard(k)
    ages = [pool[k]["age"] for k in g]
    hi_, lo_ = max(ages), min(ages)
    people = []
    single = rng.random() < 0.12
    mom = pick("f", max(25, hi_ + 21), min(64, lo_ + 44), prefer=hi_ + 30)
    dad = pick("m", max(25, hi_ + 21), min(64, lo_ + 48), prefer=hi_ + 32)
    if single:
        if rng.random() < 0.8 and mom:
            dad = None
        elif dad:
            mom = None
    for parent in (dad, mom):
        if parent:
            people.append((take(parent), "parent"))
    if not people:  # nobody of the right age is left: an older relative raises them
        gp = pick("f", hi_ + 40, 200, prefer=hi_ + 55) or pick("m", hi_ + 40, 200, prefer=hi_ + 55)
        people.append((take(gp), "grand"))
    elif rng.random() < 0.10:
        base = max(p["age"] for p, _ in people)
        gp = pick(rng.choice("mf"), base + 20, 200, prefer=base + 27)
        if gp:
            people.append((take(gp), "grand"))
    for k in sorted(g, key=lambda k: -pool[k]["age"]):
        people.append((dict(pool[k]), "child"))
    homes.append(["子どものいる家族", people])

def couples(lo, hi, target, label, gap):
    made = 0
    men = sorted([i for i in free if pool[i]["sex"] == "m" and lo <= pool[i]["age"] <= hi], key=lambda i: rng.random())
    for m in men:
        if made >= target:
            break
        f = pick("f", max(lo - 5, pool[m]["age"] - gap), pool[m]["age"] + 3, prefer=pool[m]["age"] - 2)
        if f and m in free:
            a, b = take(m), take(f)
            lab = label if callable(label) is False else label(a, b)
            homes.append([lab, [(a, "couple"), (b, "couple")]])
            made += 1

couples(65, 200, 88, "老夫婦", 8)
couples(25, 64, 80, "共働きの夫婦", 7)
for i in sorted(free, key=lambda i: pool[i]["age"]):
    p = take(i)
    a = p["age"]
    if a >= 65:
        homes.append(["一人暮らしの高齢者", [(p, "alone")]])
    elif a <= 22:
        homes.append(["学生の一人暮らし", [(p, "student")]])
    else:
        homes.append(["単身の会社員", [(p, "alone")]])

# exactly 790 homes: merge people on their own into couples, or split couples
def merge_one():
    for lab_from, lab_to, lo in (("単身の会社員", "共働きの夫婦", 25), ("一人暮らしの高齢者", "老夫婦", 65)):
        singles = [h for h in homes if h[0] == lab_from]
        rng.shuffle(singles)
        for h in singles:
            p = h[1][0][0]
            for h2 in singles:
                q = h2[1][0][0]
                if h2 is not h and q["sex"] != p["sex"] and abs(q["age"] - p["age"]) <= 8:
                    homes.remove(h2)
                    h[0] = lab_to
                    h[1] = [(p, "couple"), (q, "couple")]
                    return True
    return False

def split_one():
    for lab, single in (("共働きの夫婦", "単身の会社員"), ("老夫婦", "一人暮らしの高齢者")):
        for h in homes:
            if h[0] == lab:
                (a, _), (b, _) = h[1]
                h[0], h[1] = single, [(a, "alone")]
                homes.append([single, [(b, "alone")]])
                return True
    return False

while len(homes) > HOMES and merge_one():
    pass
while len(homes) < HOMES and split_one():
    pass
assert len(homes) == HOMES, len(homes)
# couples where both are past sixty read as an old couple
for h in homes:
    if h[0] == "共働きの夫婦" and min(p["age"] for p, _ in h[1]) >= 62:
        h[0] = "老夫婦"

# ---------------------------------------------------------------- where they live
WEIGHT = {  # how likely each kind of household is to live in each area
    "団地":           {"一人暮らしの高齢者": 5, "老夫婦": 4, "子どものいる家族": 4, "共働きの夫婦": 2, "学生の一人暮らし": 3, "単身の会社員": 3},
    "駅前のマンション": {"一人暮らしの高齢者": 1, "老夫婦": 1, "子どものいる家族": 3, "共働きの夫婦": 6, "学生の一人暮らし": 2, "単身の会社員": 5},
    "北の住宅街":       {"一人暮らしの高齢者": 4, "老夫婦": 5, "子どものいる家族": 5, "共働きの夫婦": 2, "学生の一人暮らし": 1, "単身の会社員": 1},
    "南の住宅街":       {"一人暮らしの高齢者": 3, "老夫婦": 3, "子どものいる家族": 3, "共働きの夫婦": 2, "学生の一人暮らし": 4, "単身の会社員": 4},
    "住宅街":          {"一人暮らしの高齢者": 4, "老夫婦": 4, "子どものいる家族": 4, "共働きの夫婦": 2, "学生の一人暮らし": 2, "単身の会社員": 2},
}
left = dict(AREAS)
placed = {a: [] for a in AREAS}
rng.shuffle(homes)
for h in homes:
    areas = [a for a in AREAS if left[a] > 0]
    a = rng.choices(areas, [WEIGHT[a][h[0]] * left[a] for a in areas])[0]
    left[a] -= 1
    placed[a].append(h)

out = {"version": 1, "note": "v149.35 住人の名簿。make_roster.py で作成。", "homes": {}}
for a in AREAS:
    rng.shuffle(placed[a])
    rows = []
    for label, people in placed[a]:
        sur = surname()
        taken = set()
        plist = []
        for p, role in people:
            name = given(p["sex"], p["age"], sur, taken)
            taken.add(name)
            plist.append({"id": p["id"], "name": name, "sex": p["sex"], "age": p["age"],
                          "band": band(p["age"], role), "trait": trait(p["age"]), "story": story(p, role, label)})
        rows.append({"family": label, "surname": sur, "people": plist,
                     "caution": rng.randint(0, 100), "kindness": rng.randint(0, 100),
                     "courage": rng.randint(0, 100), "prepared": rng.randint(0, 100)})
    out["homes"][a] = rows

ids = [p["id"] for rows in out["homes"].values() for h in rows for p in h["people"]]
assert len(ids) == len(set(ids)) == len(faces), (len(ids), len(set(ids)))
json.dump(out, open(f"{G}/data/residents.json", "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
c = collections.Counter(h["family"] for rows in out["homes"].values() for h in rows)
print("homes", sum(len(r) for r in out["homes"].values()), "people", len(ids))
for k, v in c.most_common():
    print(" ", k, v)
for a in AREAS:
    cc = collections.Counter(h["family"] for h in out["homes"][a])
    print(a, len(out["homes"][a]), dict(cc))
print("surnames", len(sur_used), "max", sur_used.most_common(3))
