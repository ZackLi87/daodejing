"""道德经细读 04 · 千里之行，始于足下（第六十四章）"""
from dao.config import QUOTE_SPEED as Q
from dao.engine import S, Shot
from dao.scenes import Hook, Original, Outro, Summary, Title

from .scenes import ShenZhong, WeiZhao, ZuXia, cover_art

META = {
    "num": "04",
    "slug": "千里之行",
    "out": "道德经细读04_千里之行",
}

COVER = {
    "title": "千里之行",
    "question": ["始于足下，", "更要慎终"],
    "info": "《道德经》第六十四章 · 未兆、足下与慎终",
    "seal": "老子",
    "art": cover_art,
}

# 古文读音校正（MiniMax pronunciation_dict）
PRON = [
    "易泮/(yi4)(pan4)",
    "几成/(ji1)(cheng2)",
    "累土/(lei3)(tu3)",
    "为之于未有/(wei2)(zhi1)(yu2)(wei4)(you3)",
    "合抱/(he2)(bao4)",
    "百仞/(bai3)(ren4)",
    "为而不争/(wei2)(er2)(bu4)(zheng1)",
]

SHOTS = [
    Shot(Hook, lead=0.9, segs=[
        S("“千里之行，始于足下”，常被用来鼓励人迈出第一步。"),
        S("许多人对它的理解是：再远的路，只要开始走，总能走到。", cue="common"),
        S("但在第六十四章里，老子同样看重另外两个时刻：开始之前，与将成之时。", cue="but"),
    ], tail=1.2, p=dict(
        quote="千里之行", seal="老子", common_cue="common", but_cue="but",
        common_label="常见的理解", common_lines=["再远的路", "从第一步开始"],
        but_text="开始之前，与将成之时",
    )),

    Shot(Title, lead=1.4, segs=[
        S("道德经细读，第四期。"),
    ], tail=1.4, p=dict(
        series="道德经细读", num="04", title="千里之行", subtitle="只是在说“开始”吗？",
        source="《道德经》第六十四章", seal="细读",
    )),

    Shot(Original, lead=1.0, segs=[
        S("先看原文，这里节选第六十四章的几句。", gap=0.6),
        S("其安易持，其未兆易谋；其脆易泮，其微易散。为之于未有，治之于未乱。", cue="r1", speed=Q, gap=0.7),
        S("合抱之木，生于毫末；九层之台，起于累土；千里之行，始于足下。", cue="r2", speed=Q, gap=0.7),
        S("民之从事，常于几成而败之。慎终如始，则无败事。", cue="r3", speed=Q, gap=0.9),
        S("名句夹在中间：前面讲开始之前，后面讲将成之时。", cue="groups"),
    ], tail=2.4, p=dict(
        book="《道德经》", chapter="第六十四章", edition="通行本 · 节录",
        read=["r1", "r2", "r3"],
        columns=["其安易持，其未兆易谋；", "其脆易泮，其微易散。", "为之于未有，", "治之于未乱。",
                 "合抱之木，生于毫末；", "九层之台，起于累土；", "千里之行，始于足下。",
                 "民之从事，", "常于几成而败之。", "慎终如始，则无败事。"],
        x_right=1745, colstep=118,
        pinyin=[(1, "泮", "pàn"), (5, "累", "lěi"), (8, "几", "jī")],
        group_cue="groups", group_clause=1,
        groups=[("一", [(2, 0, 5), (3, 0, 5), (0, 5, 10)]),
                ("二", [(6, 5, 9), (4, 7, 9), (5, 7, 9)]),
                ("三", [(8, 0, 7), (9, 0, 9)])],
        legend=[("一", "未兆", "为之于未有"), ("二", "足下", "毫末·累土·足下"), ("三", "慎终", "慎终如始")],
    )),

    Shot(WeiZhao, lead=1.0, segs=[
        S("第一层，是“未兆”。", gap=0.6),
        S("局面安定时，容易维持；事情尚无征兆时，容易谋划；脆弱的东西，容易化解；细微的东西，容易消散。", cue="an", gap=0.7),
        S("所以要“为之于未有，治之于未乱”：在问题出现之前着手，在秩序混乱之前治理。", cue="core", gap=0.7),
        S("合抱的大树，生于毫末；九层的高台，起于累土。这两句常被读作“积少成多”，在这里更是提醒：事情还小的时候，最容易处理。",
          cue="tree", gap=0.7),
        S("放到今天，健康、人际与工作中的许多问题，在萌芽时处理，代价最小。", cue="modern"),
    ], tail=1.8, p=dict(
        section="未兆",
        easy=["其安易持", "其未兆易谋", "其脆易泮", "其微易散"],
        core=["为之于未有，", "治之于未乱。"],
        tree_note="大事起于细微，处理也宜在细微之时",
        modern=["许多问题在萌芽时处理，", "代价最小。"],
        label_small="毫末", label_big="合抱之木",
    )),

    Shot(ZuXia, lead=1.0, segs=[
        S("第二层，是“足下”。", gap=0.6),
        S("我们熟悉的“千里之行，始于足下”，在马王堆帛书中，甲本作“百仁之高”，乙本作“百千之高”，学者多读为“百仞之高”。",
          cue="v1", gap=0.7),
        S("仞是古代的长度单位，百仞之高，是说极高之处。", cue="ren", gap=0.7),
        S("这样读来，“毫末”“累土”“足下”三者并列，说的都是：再高、再大的东西，也从最低、最小的地方起步。", cue="parallel", gap=0.7),
        S("放到今天，起点不在远方的理想条件里，就在此刻脚下的位置。", cue="modern"),
    ], tail=1.8, p=dict(
        section="足下",
        boshu=[("甲本", "百仁之高，台于足下"), ("乙本", "百千之高，始于足下")],
        ren="仁、千读为“仞”，百仞极言其高",
        parallel=[("合抱之木", "生于毫末"), ("九层之台", "起于累土"), ("百仞之高", "始于足下")],
        modern="起点不在远方的理想条件里，就在此刻脚下的位置",
    )),

    Shot(ShenZhong, lead=1.0, segs=[
        S("第三层，是“慎终”。", gap=0.6),
        S("老子说：“民之从事，常于几成而败之。”人们做事，常常在快要成功的时候失败。", cue="fail", gap=0.7),
        S("王弼对这一句的注释只有四个字：“不慎终也。”", cue="wangbi", gap=0.7),
        S("所以紧接着说：“慎终如始，则无败事。”对待结尾，要像对待开头一样谨慎。", cue="shen", gap=0.7),
        S("放到今天，越接近完成，越需要保持起初的审慎；最后一次检查与核对，往往决定成败。", cue="modern"),
    ], tail=1.8, p=dict(
        section="慎终", shen="慎终如始，则无败事",
        modern=["越接近完成，", "越需要起初的审慎。"],
        path_caption="常于几成而败之",
    )),

    Shot(Summary, lead=1.0, segs=[
        S("回到“千里之行，始于足下”。", gap=0.6),
        S("未兆，是在开始之前着手；足下，是从此刻所在之处起步；慎终，是在将成之时依然审慎。", cue="rows", gap=0.7),
        S("一件事的成败，既在第一步，也在最后一步。", cue="foot"),
    ], tail=2.0, p=dict(
        kicker="第六十四章 · 小结", heading="千里之行",
        rows=[("一", "未兆", "治于未乱", "为之于未有"), ("二", "足下", "起于脚下", "毫末 · 累土 · 足下"),
              ("三", "慎终", "终如其始", "慎终如始，则无败事")],
        rows_cue="rows", row_clauses=[0, 2, 4],
        foot="一件事的成败，既在第一步，也在最后一步", foot_cue="foot",
    )),

    Shot(Outro, lead=1.0, segs=[
        S("下一期，我们读“信言不美，美言不信”。", cue="next", gap=0.6),
        S("它所在的第八十一章，是通行本的最后一章；全书最后四个字，是“为而不争”。老子并不主张无所作为。", cue="variant", gap=0.8),
        S("你是否有过“几成而败”的经历？欢迎在评论区分享。", cue="cta"),
    ], tail=3.0, p=dict(
        next_label="下一期", next_title="通行本的最后一句，是什么？", next_quote="为而不争",
        variant=(0, "并非无为", "通行本末句"), variant_cue="variant",
        cta=["你是否有过“几成而败”的经历？", "欢迎在评论区分享。"], cta_cue="cta",
        series="道德经细读", seal="细读",
    )),
]
