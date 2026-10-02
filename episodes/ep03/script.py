"""道德经细读 03 · 天地不仁，以万物为刍狗（第五章）"""
from dao.config import QUOTE_SPEED as Q
from dao.engine import S, Shot
from dao.scenes import Hook, Original, Outro, Summary, Title

from .scenes import BuRen, ChuGou, ShouZhong, cover_art

META = {
    "num": "03",
    "slug": "天地不仁",
    "out": "道德经细读03_天地不仁",
}

COVER = {
    "title": "天地不仁",
    "question": ["是说天地", "残忍吗？"],
    "info": "《道德经》第五章 · 不仁、刍狗与守中",
    "seal": "老子",
    "art": cover_art,
}

# 古文读音校正（MiniMax pronunciation_dict）
PRON = [
    "橐籥/(tuo2)(yue4)",
    "数穷/(shuo4)(qiong2)",
    "刍狗/(chu2)(gou3)",
]

SHOTS = [
    Shot(Hook, lead=0.9, segs=[
        S("“天地不仁，以万物为刍狗”，这句话常在感叹世事无常时被引用。"),
        S("许多人把它理解为：天地冷酷无情，视万物如草芥。", cue="common"),
        S("但在老子这里，“不仁”并不是残忍；“刍狗”，也不只是草芥。", cue="but"),
    ], tail=1.2, p=dict(
        quote="天地不仁", seal="老子", common_cue="common", but_cue="but",
        common_label="常见的理解", common_lines=["天地冷酷无情", "视万物如草芥"],
        but_text="“不仁”并非残忍",
    )),

    Shot(Title, lead=1.4, segs=[
        S("道德经细读，第三期。"),
    ], tail=1.4, p=dict(
        series="道德经细读", num="03", title="天地不仁", subtitle="是说天地残忍吗？",
        source="《道德经》第五章", seal="细读",
    )),

    Shot(Original, lead=1.0, segs=[
        S("先看原文。", gap=0.6),
        S("天地不仁，以万物为刍狗；圣人不仁，以百姓为刍狗。", cue="r1", speed=Q, gap=0.7),
        S("天地之间，其犹橐籥乎？虚而不屈，动而愈出。", cue="r2", speed=Q, gap=0.7),
        S("多言数穷，不如守中。", cue="r3", speed=Q, gap=0.9),
        S("全章四十五字，可以从三个词读起：不仁、刍狗、守中。", cue="groups"),
    ], tail=2.4, p=dict(
        book="《道德经》", chapter="第五章", edition="通行本 · 四十五字",
        read=["r1", "r2", "r3"],
        columns=["天地不仁，", "以万物为刍狗；", "圣人不仁，", "以百姓为刍狗。", "天地之间，", "其犹橐籥乎？",
                 "虚而不屈，", "动而愈出。", "多言数穷，", "不如守中。"],
        x_right=1745, colstep=118,
        pinyin=[(1, "刍", "chú"), (5, "橐", "tuó"), (5, "籥", "yuè"), (8, "数", "shuò")],
        group_cue="groups", group_clause=1,
        groups=[("一", [(0, 2, 4), (2, 2, 4)]),
                ("二", [(1, 4, 6), (3, 4, 6)]),
                ("三", [(8, 0, 4), (9, 0, 4)])],
        legend=[("一", "不仁", "天地不仁 · 圣人不仁"), ("二", "刍狗", "以万物为刍狗"), ("三", "守中", "多言数穷，不如守中")],
    )),

    Shot(BuRen, lead=1.0, segs=[
        S("第一层，是“不仁”。", gap=0.6),
        S("王弼注说：“天地任自然，无为无造，万物自相治理，故不仁也。”", cue="wangbi", gap=0.6),
        S("所谓“仁”，在这里是有意施恩、有所偏爱；“不仁”，是不偏不私，任万物自然生长。", cue="def", gap=0.7),
        S("再看下一句：“圣人不仁，以百姓为刍狗。”圣人是老子心中的理想人格，如果“不仁”是残忍，这句话就说不通了。",
          cue="sage", gap=0.7),
        S("就像一场雨落下，不会挑选哪一株草木。", cue="rain", gap=0.7),
        S("放到今天，境遇的起落，未必是冲着自己来的；少一分怨天尤人，多一分平常心。", cue="modern"),
    ], tail=1.6, p=dict(
        section="不仁",
        wangbi=["天地任自然，无为无造，", "万物自相治理，故不仁也。"],
        ren="有意施恩，有所偏爱", buren="不偏不私，任其自然",
        sage="圣人不仁，以百姓为刍狗", sage_note="圣人是老子心中的理想人格",
        caption="天施地化，不以仁恩 —— 河上公注",
        modern="境遇起落，未必冲着自己而来",
    )),

    Shot(ChuGou, lead=1.0, segs=[
        S("第二层，是“刍狗”。", gap=0.6),
        S("《庄子·天运》里写过刍狗，也就是用草扎成的狗：祭祀之前，用竹箱盛放，用绣巾覆盖，主祭的人斋戒之后才捧送上去；",
          cue="zhuang", gap=0.3),
        S("祭祀之后，路人踩它的头和脊背，拾柴的人拿去烧火。", cue="after", gap=0.6),
        S("前后判若两样，却不是先爱后恨，只是用处已经过去。", cue="point", gap=0.7),
        S("王弼则把“刍”和“狗”分开解释：“不为兽生刍，而兽食刍；不为人生狗，而人食狗。”天地并不为谁生出万物，万物却各得其用。",
          cue="wangbi", gap=0.7),
        S("两种解释，指向同一处：天地对万物，既无偏爱，也无恶意。", cue="common", gap=0.7),
        S("放到今天，被重视还是被冷落，往往取决于时势，未必关乎好恶；得意时不必自矜，失意时也不必自伤。", cue="modern"),
    ], tail=1.8, p=dict(
        section="刍狗",
        zhuang_label="《庄子·天运》", before="盛以箧衍，巾以文绣", after="行者践其首脊，苏者取而爨之",
        point="不是先爱后恨，只是用处已过",
        wangbi_label="王弼注", wangbi=["不为兽生刍，而兽食刍；", "不为人生狗，而人食狗。"],
        wangbi_point="天地不为谁而生，万物各得其用",
        common="既无偏爱，也无恶意",
        modern="被重视还是被冷落，往往取决于时势；得意不必自矜，失意不必自伤",
    )),

    Shot(ShouZhong, lead=1.0, segs=[
        S("第三层，是“守中”。", gap=0.6),
        S("老子把天地之间比作橐籥，也就是风箱：中间空虚，却不会穷竭；越是鼓动，风越是源源不断。", cue="bellows", gap=0.7),
        S("紧接着说：“多言数穷，不如守中。”话说得越多，越容易屡屡陷入困境，不如守住内心的虚静。", cue="duo", gap=0.7),
        S("马王堆帛书乙本写作“多闻数穷，不若守于中”：不只是说得多，听得多、求得杂，也会让人困顿。", cue="boshu", gap=0.7),
        S("王弼注说得更直接：“愈为之则愈失之矣。”", cue="wangbi", gap=0.7),
        S("放到今天，少一些不必要的表态与干预，给自己，也给他人，留出一点空间。", cue="modern"),
    ], tail=1.8, p=dict(
        section="守中", bellows_caption="虚而不屈，动而愈出",
        boshu="多闻数穷，不若守于中", wangbi="愈为之则愈失之矣",
        modern=["少一些不必要的表态与干预，", "给自己，也给他人，留出空间。"],
    )),

    Shot(Summary, lead=1.0, segs=[
        S("回到“天地不仁”这几个字。", gap=0.6),
        S("不仁，是不偏不私；刍狗，是无爱无憎；守中，是少言而有度。", cue="rows", gap=0.7),
        S("天地的“不仁”，恰恰是一种更大的公允。", cue="foot"),
    ], tail=2.0, p=dict(
        kicker="第五章 · 小结", heading="天地不仁",
        rows=[("一", "不仁", "不偏不私", "天地任自然"), ("二", "刍狗", "无爱无憎", "《庄子·天运》 · 王弼注"),
              ("三", "守中", "少言有度", "多言数穷，不如守中")],
        rows_cue="rows", row_clauses=[0, 2, 4],
        foot="天地的“不仁”，恰恰是一种更大的公允", foot_cue="foot",
    )),

    Shot(Outro, lead=1.0, segs=[
        S("下一期，我们读“千里之行，始于足下”。", cue="next", gap=0.6),
        S("同一章里，老子更在意的其实是“终”：慎终如始，则无败事。", cue="variant", gap=0.8),
        S("你怎样理解“天地不仁”？欢迎在评论区留言。", cue="cta"),
    ], tail=3.0, p=dict(
        next_label="下一期", next_title="“始于足下”之后，还有一句更要紧", next_quote="始于足下",
        variant=(0, "终", "慎终如始"), variant_cue="variant",
        cta=["你怎样理解“天地不仁”？", "欢迎在评论区留言。"], cta_cue="cta",
        series="道德经细读", seal="细读",
    )),
]
