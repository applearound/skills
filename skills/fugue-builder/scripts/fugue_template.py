#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
赋格生成通用模板：手写主题 + 音阶级平移公式 + 约束搜索对位 + 合成渲染。
引擎与具体音乐体系解耦：任何能写成有序音高数组的体系都能生成
（大小调、教会调式、五声、日本音阶、布鲁斯、和声小调、自定义音阶）。

用法：复制本文件，从零推导一个新 profile（推导规程见 SKILL.md 与
references/counterpoint.md），配套重写素材区（主题 / 间插段 / 终止），
引擎区不要动。依赖：numpy、matplotlib、midiutil（uv 临时环境安装）。

内置两个已验证范例 profile：PENTA_PROFILE（C 宫五声，民乐三重奏）、
TONAL_PROFILE（D 小调，管风琴），仅作推导参考，新需求不要套用它们。
"""
from itertools import product
import numpy as np

# ======================= 配置区（每次生成从这里从零构建） =======================
# 本模板是通用引擎：任何能写成有序音高数组的体系都能跑（大小调、教会调式、
# 五声、日本音阶、布鲁斯、和声小调、自定义律制……）。
# 每类新需求应当从零推导一个新 profile，下面两个 profile 只是已验证的范例，
# 不要把新需求硬套进它们。
#
# 推导规则（详见 references/counterpoint.md）：
#   scale        目标体系跨八度连续音高数组，是所有公式的基准
#   step         相邻音阶音的半音差集合，可省略——引擎自动从 scale 推导
#   susp_resolve 挂留下行解决步长，可省略——默认为 -step
#   answer       答题的音阶级平移步数，语义决策：新调式中心在音阶上高几级
#   mode_chords  调式和弦集合（强拍和声奖励），无此概念的体系设 None

PENTA_PROFILE = {                       # 范例一：C 宫五声（民乐三重奏）
    'title': 'Fugue on C gong pentatonic',
    'out_prefix': 'fugue_penta',
    'scale': [43, 45, 48, 50, 52, 55, 57, 60, 62, 64, 67, 69, 72, 74, 76, 79, 81, 84],
    'con': {0, 3, 4, 5, 7, 8, 9},       # 协和音程，多数体系通用，特殊体系可改
    'perfect': {0, 7},                  # 禁平行的完全协和集
    'allow_par5_episode': True,         # 风格开关：间插段是否放行平行五度（民乐支声）
    'mode_chords': {frozenset(c) for c in
                    [(0,4,7), (2,7,9), (4,9,0), (7,0,2), (9,0,4)]},   # 宫商角徵羽
    'domains': {
        'S': [60, 62, 64, 67, 69, 72, 74, 76, 79],
        'A': [52, 55, 57, 60, 62, 64, 67, 69, 72, 74, 76],
        'B': [43, 45, 48, 50, 52, 55, 57, 60],
    },
    'qpm': 76,
    'beam_width': 250,
    'susp_bonus': 2.2,       # 挂留奖励强度：细节类型偏好是风格参数。
                             # 严格对位风格偏低（1.6，挂留为主），流动性风格偏高
    'instruments': {'S': 'dizi', 'A': 'zheng', 'B': 'qin'},
    'gains': {'S': 0.95, 'A': 1.20, 'B': 1.45},
    'reverb': {'seconds': 2.0, 'tau': 0.55, 'predelay': 0.018, 'wet': 0.28},
    'lead': {'S': (0, 64), 'A': (64, 128), 'B': (160, 224)},
    'phrase_ends': {64, 128, 160, 224},
    'midi_prog': {'S': 74, 'A': 106, 'B': 45},
}

TONAL_PROFILE = {                       # 范例二：D 小调（管风琴）
    'title': 'Fugue in D minor',
    'out_prefix': 'fugue_tonal',
    # scale 是全曲音高资源表：所有调性借用音都要入列——主题导音 C#4=61、C#5=73、
    # semitone 答题映射出的还原 B（59=答题产物、47=低音域）与 Bb 系并存、
    # 皮卡迪三度 F#4=66、答题导音 G#3=56。缺列会导致索引崩溃或误报偏音。
    # 含借用音的体系答题用 semitone 模式（degree 的八度级数推导会失真）
    'scale': [38, 40, 41, 43, 45, 46, 47, 48, 50, 52, 53, 55, 56, 57, 58, 59,
              60, 61, 62, 64, 65, 66, 67, 68, 69, 70, 72, 73, 74, 76, 77, 79],
    'con': {0, 3, 4, 5, 7, 8, 9},
    'perfect': {0, 7},
    'allow_par5_episode': False,
    'mode_chords': None,
    'domains': {
        'S': [62, 64, 65, 67, 69, 70, 72, 74],
        'A': [55, 57, 58, 60, 62, 64, 65, 67, 69, 70, 72],
        'B': [45, 47, 48, 50, 52, 53, 55],
    },
    'qpm': 72,
    'beam_width': 250,
    'susp_bonus': 1.6,       # v2 原版实测值：严格对位风格下挂留密度最健康的比例
    'instruments': {'S': 'organ', 'A': 'organ', 'B': 'organ'},
    'gains': {'S': 0.85, 'A': 0.75, 'B': 0.95},
    'reverb': {'seconds': 2.8, 'tau': 0.95, 'predelay': 0.025, 'wet': 0.30},
    'lead': {'S': (0, 64), 'A': (64, 128), 'B': (160, 224)},
    'phrase_ends': {64, 128, 160, 224},
    'midi_prog': {'S': 19, 'A': 19, 'B': 19},
}

CONFIG = dict(PENTA_PROFILE)            # 换 profile 在这里；新需求请写新 profile

# ======================= 音乐素材区（手写部分，与 profile 配套） =======================
# 素材必须全部重写为当前 profile 体系的音高（引擎只查搜索声部，
# 手写段的违例要靠人自查：主题音域、episode 与低音拍点协和、终止声部进行）
# 主题：(MIDI 音高, 八分音符数)，8 小节共 64 个八分位
# 要点：开头给特征动机（可被识别与模进），有高点，有长音收束，音域控制在声部域内
SUBJECT = [
    (67, 2), (64, 2), (62, 2), (60, 2),
    (62, 1), (64, 1), (67, 2), (69, 2), (67, 2),
    (64, 1), (67, 1), (69, 2), (72, 2), (69, 2),
    (67, 2), (64, 2), (62, 4),
    (64, 1), (67, 1), (64, 1), (62, 1), (60, 2), (62, 2),
    (60, 2), (62, 2), (64, 4),
    (67, 1), (69, 1), (72, 2), (69, 1), (67, 1), (64, 2),
    (62, 2), (60, 6),
]

# 答题移调公式，两种模式按体系选择：
#   degree  音阶级平移：音阶自足体系（五声、多数调式音乐），保证答题不出偏音
#   semitone 半音移调：主题含音阶外导音借用时使用（如小调的还原七级），
#           半音移调会把导音正确映射到新调属和弦的导音，音阶级平移做不到
ANSWER = {'mode': 'degree', 'steps': 3, 'octave': -1}
BASS_ENTRY = {'mode': 'degree', 'steps': 0, 'octave': -1}   # 回主调中心，降八度

# 间插段 e128-160（M17-20）：手写模进。笛模进逐级上移，低音换和弦支撑。
# 注意：手写段每个八分位都要与低音拍点协和，写完自查（引擎不检查固定声部间违例）
EPISODE = {
    'S': [72,72,69,69,67,67,64,64,
          74,74,72,72,67,67,64,64,
          76,76,74,74,72,72,69,69,
          79,79,76,76,74,74,72,72],
    'B': [48]*8 + [43]*8 + [45]*8 + [43]*8,
}

# 终止 e240-256（M31-32）：手写。倒数第二小节属方向和弦，末小节主和弦。
CADENCE = {
    'S': [74]*8 + [72]*8,
    'A': [67]*16,
    'B': [43]*8 + [48]*8,
}

# 终止装饰（可选）：筝刮奏替换 A 声部 M31 前半
GLISSANDO = {'voice': 'A', 'start': 240, 'notes': (79, 76, 74, 72, 69, 67, 64, 60)}
# 终止颤音（可选）：西方版用 {'voice': 'S', 'start': 240, 'aux': +1, 'reps': 3}
TRILL = None

# ======================= 引擎区（以下不要动） =======================
N_POS = 256
VOICES = ('S', 'A', 'B')
TL = {v: [None] * N_POS for v in VOICES}

SCALE = CONFIG['scale']
IDX = {p: i for i, p in enumerate(SCALE)}
CON = CONFIG['con']
PERFECT = CONFIG['perfect']
# 级进步长与挂留解决步长：profile 可显式给出，否则从音阶自动推导
_derived_step = {b - a for a, b in zip(SCALE, SCALE[1:]) if 0 < b - a < 12}
STEP = frozenset(CONFIG.get('step') or _derived_step)
SUSP_RESOLVE = tuple(CONFIG.get('susp_resolve')
                     or sorted(-s for s in _derived_step))
DOMAINS = CONFIG['domains']
K = CONFIG['beam_width']
HARD = None
print(f'级进步长集（推导/显式）：{sorted(STEP)}，挂留解决：{SUSP_RESOLVE}')

# 八度对应的音阶级数（五声 5、七声 7），从音阶数组自动推导
OCT_STEPS = next(IDX[p + 12] - IDX[p] for p in SCALE if p + 12 in IDX)

def transpose_answer(seq, spec):
    """答题/低音进入的移调公式。degree = 音阶级平移，semitone = 半音移调。"""
    if spec.get('mode', 'degree') == 'semitone':
        return [p + spec['shift'] for p in seq]
    return [SCALE[IDX[p] + spec['steps'] + OCT_STEPS * spec.get('octave', 0)]
            for p in seq]

def expand(notes):
    out = []
    for p, d in notes:
        out += [p] * d
    assert len(out) == 64, f'主题总时值 {len(out)}，应为 64 个八分位'
    return out

subj = expand(SUBJECT)
TL['S'][0:64] = subj
TL['A'][64:128] = transpose_answer(subj, ANSWER)
TL['B'][160:224] = transpose_answer(subj, BASS_ENTRY)
TL['S'][128:160] = EPISODE['S']
TL['B'][128:160] = EPISODE['B']
for v in VOICES:
    TL[v][240:256] = CADENCE[v]

def interval(a, b):
    return abs(a - b) % 12

def sdist(p, q):
    return IDX[p] - IDX[q]

def pos_class(e):
    r = e % 8
    if r in (0, 4):  return 'strong'
    if e % 2 == 0:   return 'mid'
    return 'off'

def search_voices_at(e):
    if 64 <= e < 128:   return ('S',)
    if 128 <= e < 160:  return ('A',)
    if 160 <= e < 224:  return ('S', 'A')
    if 224 <= e < 240:  return ('S', 'A', 'B')
    return ()

# 终止引导罚的目标音位：从终止式首拍音自动推导（上 1 级到下 2 级的邻域，
# 邻域过窄会把搜索逼向高罚的接驳路径）
CAD_TARGETS = {}
for v in VOICES:
    t0 = CADENCE[v][0]
    if t0 in IDX:
        lo = max(0, IDX[t0] - 2)
        CAD_TARGETS[v] = tuple(dict.fromkeys(
            SCALE[i] for i in (min(IDX[t0] + 1, len(SCALE) - 1), IDX[t0], lo, lo + 1)))
    else:
        CAD_TARGETS[v] = (t0,)

def vertical(cur, prev, flags, pclass, e, sv):
    RELAX = e >= 240          # 终止接驳：硬淘汰放宽为大罚，防 beam 枯竭
    pen = 0.0
    vals = [cur[v] for v in VOICES]
    diss = [False] * 3
    for i in range(3):
        for j in range(3):
            if i == j or vals[i] is None or vals[j] is None:
                continue
            if interval(vals[i], vals[j]) not in CON:
                diss[i] = True
                break
    newflags = [0, 0, 0]
    for i, v in enumerate(VOICES):
        c, p = cur[v], prev[v]
        if c is None or p is None:
            continue
        d = c - p
        if flags[i] == 2 and d not in SUSP_RESOLVE:
            pen += 20.0
        if flags[i] == 1 and abs(d) not in STEP:
            pen += 20.0
        # 不协和责任只归搜索声部；固定声部无选择权，不受 flag 约束
        if not diss[i] or v not in sv:
            continue
        ad = abs(d)
        if pclass == 'strong':
            if d == 0:
                pen -= CONFIG.get('susp_bonus', 2.2); newflags[i] = 2   # 挂留
            elif ad in STEP:
                pen += 10.0; newflags[i] = 1       # 拍上助音
            else:
                return 100.0 if RELAX else HARD
        elif pclass == 'mid':
            if d == 0:
                pen -= CONFIG.get('susp_bonus', 2.2) * 0.45; newflags[i] = 2
            elif ad in STEP:
                pen += 2.0; newflags[i] = 1
            else:
                return 100.0 if RELAX else HARD
        else:
            # 弱位经过音要给奖励，否则搜索永远选择全协和路径，细节机制形同虚设
            if ad in STEP or d == 0:
                pen -= 0.1; newflags[i] = 1
            else:
                return 100.0 if RELAX else HARD
    s, a, b = vals
    if s is not None and a is not None and abs(s - a) > 24: pen += 2
    if a is not None and b is not None and abs(a - b) > 19: pen += 2
    if s is not None and b is not None and abs(s - b) > 31: pen += 1
    return pen, tuple(newflags)

def parallel(prev, prev2, cur, e):
    episode = 128 <= e < 160
    allow5 = CONFIG['allow_par5_episode'] and episode
    pen = 0.0
    for v1, v2 in (('S', 'A'), ('S', 'B'), ('A', 'B')):
        a2, b2 = prev[v1], prev[v2]
        a3, b3 = cur[v1], cur[v2]
        if None in (a2, b2, a3, b3):
            continue
        i2, i3 = interval(a2, b2), interval(a3, b3)
        if i2 in PERFECT and i3 in PERFECT and a2 != a3 and b2 != b3:
            if (a3 - a2) * (b3 - b2) > 0:
                if allow5 and i2 == 7 and i3 == 7:
                    continue
                return 100.0 if e >= 240 else HARD
            pen += 30.0                              # 反向五八
    return pen

def melodic(prev, prev2, cur, same_counts, e, sv):
    """旋律按音阶级距离衡量。只约束搜索声部：固定声部是手写的，
    对它们执行跳进禁令会让合法的手写八度跳进杀死整条 beam。"""
    pen = 0.0
    for i, v in enumerate(VOICES):
        if v not in sv:
            continue
        c, p = cur[v], prev[v]
        if c is None or p is None:
            continue
        sd = sdist(c, p)
        ad = abs(sd)
        if ad >= 5:
            if e >= 240:
                pen += 100.0
                continue
            return HARD
        if ad == 1:      pen -= 0.5     # 级进：流动感的主要来源
        elif ad == 0:    pen += 0.7     # 同音停留：轻罚，防线条死水
        elif ad == 2:    pen += 0.3     # 音阶三度
        elif ad == 3:    pen += 1.6     # 四五度跳
        else:            pen += 3.2     # 六度大跳
        pp = prev2[v]
        if pp is not None:
            spd = sdist(p, pp)
            if abs(spd) >= 2:
                if spd * sd > 0:  pen += 2.2      # 连续同向跳进
                elif ad == 1:     pen -= 0.8      # 跳进后反向级进补偿
        if sd == 0 and same_counts[i] >= 2:
            pen += 0.5 * (same_counts[i] - 1)
    return pen

def harmony_pen(prev, cur, pclass):
    """强拍和声塑形：有调式和弦集时奖励匹配；没有时退化为粘滞罚
    （相邻拍同和弦集合轻罚，维持和声律动——提炼时曾丢失，导致拍点摩擦翻倍）"""
    mode_chords = CONFIG.get('mode_chords')
    if mode_chords is None:
        p1 = frozenset(p % 12 for p in prev.values() if p is not None)
        p2 = frozenset(p % 12 for p in cur.values() if p is not None)
        return 0.25 if (p1 and p1 == p2) else 0.0
    if pclass != 'strong':
        return 0.0
    pcs = frozenset(p % 12 for p in cur.values() if p is not None)
    if not pcs:
        return 0.0
    for ch in mode_chords:
        if pcs <= ch:
            return -0.7 if pcs == ch else -0.3
    return 0.3

def run_search():
    beam = [(0.0,
             tuple(TL[v][63] for v in VOICES),
             tuple(TL[v][62] for v in VOICES),
             (0, 0, 0), (0, 0, 0),
             ())]
    for e in range(64, 256):
        sv = search_voices_at(e)
        pclass = pos_class(e)
        if sv:
            doms = [DOMAINS[v] for v in sv]
            raw = [dict(zip(VOICES,
                            (ch[sv.index(v)] if v in sv else TL[v][e] for v in VOICES)))
                   for ch in product(*doms)]
        else:
            raw = [{v: TL[v][e] for v in VOICES}]
        new_beam = []
        for pen, prev, prev2, flags, samec, path in beam:
            pd = dict(zip(VOICES, prev))
            pd2 = dict(zip(VOICES, prev2))
            for c in raw:
                vp = vertical(c, pd, flags, pclass, e, sv)
                if vp is HARD:
                    continue
                vpen, nflags = vp
                mpen = melodic(pd, pd2, c, samec, e, sv)
                if mpen is HARD:
                    continue
                ppen = parallel(pd, pd2, c, e)
                if ppen is HARD:
                    continue
                hpen = harmony_pen(pd, c, pclass)
                total = pen + vpen + mpen + ppen + hpen
                if e == 64 and c['S'] in IDX and TL['S'][63] in IDX \
                        and abs(sdist(c['S'], TL['S'][63])) >= 2:
                    total -= 1.0          # 对题以跳进进入，与主题形成性格对比
                if 160 <= e < 192 and c['A'] and c['A'] > 64:
                    total += 0.15         # 低音主题陈述期中音声部让路
                if e >= 230:              # 终止接驳引导：提前几拍铺向终止音位
                    w = 2.0 if e >= 236 else 0.6
                    for v, wt in (('S', 0.5), ('A', 0.3), ('B', 0.4)):
                        tgt = CAD_TARGETS[v]
                        if c[v] is not None and c[v] in IDX and tgt[0] in IDX:
                            total += w * min(abs(sdist(c[v], x)) for x in tgt) * wt
                ns = tuple(samec[i] + 1 if c[v] == pd[v] and c[v] is not None else 0
                           for i, v in enumerate(VOICES))
                new_beam.append((total, tuple(c[v] for v in VOICES), prev,
                                 nflags, ns, path + (tuple(c[v] for v in VOICES),)))
        new_beam.sort(key=lambda x: x[0])
        beam = new_beam[:K]
        if not beam:
            raise RuntimeError(f'beam 在位置 {e} 枯竭：检查该处的固定声部 '
                               f'是否与搜索域存在无解组合')
    return beam[0][5], beam[0][0]

print(f"约束搜索（beam = {K}）...")
path, final_pen = run_search()
print(f'搜索完成，总罚分 {final_pen:.2f}')

for i, ct in enumerate(path):
    e = 64 + i
    for v, p in zip(VOICES, ct):
        TL[v][e] = p

def verify():
    rep = {'音阶外偏音': 0, '平行五八(严格段)': 0, '间插段平行五度': 0,
           '未准备拍点不协和': 0, '拍上装饰音': 0, '未级进解决': 0, '旋律大跳': 0,
           '挂留': 0, '弱位不协和(经过/邻音)': 0}
    scale_pcs = {p % 12 for p in SCALE}
    for v in VOICES:
        for p in TL[v]:
            if p is not None and p % 12 not in scale_pcs:
                rep['音阶外偏音'] += 1
    flags = [0, 0, 0]
    for e in range(N_POS):
        cur = {v: TL[v][e] for v in VOICES}
        prev = {v: TL[v][e - 1] for v in VOICES} if e > 0 else cur
        episode = 128 <= e < 160
        for v1, v2 in (('S', 'A'), ('S', 'B'), ('A', 'B')):
            a2, b2 = (prev[v1], prev[v2]) if e > 0 else (None, None)
            a3, b3 = cur[v1], cur[v2]
            if None in (a2, b2, a3, b3):
                continue
            i2, i3 = interval(a2, b2), interval(a3, b3)
            if (i2 == i3 == 7 and a2 != a3 and b2 != b3
                    and (a3 - a2) * (b3 - b2) > 0):
                rep['间插段平行五度' if episode else '平行五八(严格段)'] += 1
            if (e > 0 and i2 in PERFECT and i3 in PERFECT and i2 != 7
                    and a2 != a3 and b2 != b3 and (a3 - a2) * (b3 - b2) > 0):
                rep['平行五八(严格段)'] += 1
        vals = [cur[v] for v in VOICES]
        diss = [False] * 3
        for i in range(3):
            for j in range(3):
                if i == j or vals[i] is None or vals[j] is None:
                    continue
                if interval(vals[i], vals[j]) not in CON:
                    diss[i] = True
                    break
        pclass = pos_class(e)
        sv = search_voices_at(e)
        nf = [0, 0, 0]
        for i, v in enumerate(VOICES):
            c, p = cur[v], prev[v]
            if c is None or p is None:
                continue
            d = c - p
            if flags[i] == 2 and d not in SUSP_RESOLVE:
                rep['未级进解决'] += 1
            if flags[i] == 1 and abs(d) not in STEP:
                rep['未级进解决'] += 1
            if not diss[i] or v not in sv:
                continue
            ad = abs(d)
            if pclass in ('strong', 'mid'):
                if d == 0:
                    rep['挂留'] += 1; nf[i] = 2
                elif ad in STEP:
                    rep['拍上装饰音'] += 1; nf[i] = 1
                else:
                    rep['未准备拍点不协和'] += 1
            else:
                if ad in STEP or d == 0:
                    rep['弱位不协和(经过/邻音)'] += 1; nf[i] = 1
                else:
                    rep['未级进解决'] += 1
            if c in IDX and p in IDX and abs(sdist(c, p)) >= 5:
                rep['旋律大跳'] += 1
        flags = nf
    return rep

rep = verify()
print('规则验证：', rep)

def merge_notes(seq):
    notes, i = [], 0
    while i < len(seq):
        p = seq[i]
        if p is None:
            i += 1
            continue
        j = i
        while j < len(seq) and seq[j] == p:
            j += 1
        notes.append((p, j - i, i))
        i = j
    return notes

NOTES = {v: merge_notes(TL[v]) for v in VOICES}
for v in VOICES:
    print(f'{v}: {len(NOTES[v])} 个音符，音域 '
          f'{min(p for p,_,_ in NOTES[v])}-{max(p for p,_,_ in NOTES[v])}')

# 终止装饰替换
if GLISSANDO:
    g = GLISSANDO
    NOTES[g['voice']] = [n for n in NOTES[g['voice']] if n[2] < g['start']]
    add, pos = [], float(g['start'])
    for gp in g['notes']:
        add.append((gp, 0.5, pos))
        pos += 0.5
    add.append((TL[g['voice']][g['start'] + 4], 12.0, g['start'] + 4))
    NOTES[g['voice']] += add
    NOTES[g['voice']].sort(key=lambda n: n[2])
if TRILL:
    t = TRILL
    NOTES[t['voice']] = [n for n in NOTES[t['voice']]
                         if not (n[2] == t['start'])]
    add, pos = [], t['start']
    for _ in range(t['reps']):
        base = TL[t['voice']][t['start']]
        add += [(base, 1, pos), (base + t['aux'], 1, pos + 1)]
        pos += 2
    add.append((TL[t['voice']][t['start']], 2, pos))
    NOTES[t['voice']] += add
    NOTES[t['voice']].sort(key=lambda n: n[2])

# ======================= 渲染 =======================
SR = 44100
EIGHTH = 60.0 / CONFIG['qpm'] / 2
rng = np.random.default_rng(2026)
total_len = int((N_POS * EIGHTH + 4.5) * SR)
LEAD = CONFIG['lead']
PHRASE_ENDS = CONFIG['phrase_ends']

STOPS = [                                    # organ 四档音栓逐段加亮
    [1.0, 0.45, 0.28, 0.15, 0.07, 0.04],
    [1.0, 0.55, 0.38, 0.25, 0.14, 0.08, 0.05],
    [1.0, 0.62, 0.45, 0.32, 0.20, 0.12, 0.08, 0.05],
    [1.0, 0.68, 0.50, 0.38, 0.26, 0.16, 0.10, 0.07, 0.04],
]

def stops_for_pos(e):
    m = e // 8
    return STOPS[min(3, m // 8)]

def synth_organ(pitch, dur, start, use_sub):
    f0 = 440.0 * 2 ** ((pitch - 69) / 12)
    n = int((dur + 0.16) * SR)
    t = np.arange(n) / SR
    sig = np.zeros(n)
    for cents in (2.5, -2.5):
        f = f0 * 2 ** ((cents + rng.uniform(-0.6, 0.6)) / 1200)
        for k, amp in enumerate(stops_for_pos(int(start)), start=1):
            if f * k > 0.9 * SR / 2:
                break
            sig += amp * np.sin(2 * np.pi * f * k * t + rng.uniform(0, 2 * np.pi))
    if use_sub:
        fs = f0 / 2
        for k, amp in enumerate([0.5, 0.32, 0.2, 0.1, 0.06, 0.03], start=1):
            if fs * k > 0.9 * SR / 2:
                break
            sig += amp * np.sin(2 * np.pi * fs * k * t + rng.uniform(0, 2 * np.pi))
    env = np.ones(n)
    a, r = int(0.015 * SR), int(0.15 * SR)
    env[:a] = np.linspace(0, 1, a)
    k0 = int(dur * SR)
    env[k0:] = np.exp(-np.arange(n - k0) / (0.05 * SR))
    return sig * env

def synth_dizi(pitch, dur, lead):
    f0 = 440.0 * 2 ** ((pitch - 69) / 12)
    n = int((dur + 0.3) * SR)
    t = np.arange(n) / SR
    depth = 0.004 if lead else 0.0025
    vib = 1 + depth * np.sin(2 * np.pi * 5.2 * t) * np.clip((t - 0.18) / 0.5, 0, 1)
    ph = 2 * np.pi * f0 * np.cumsum(vib) / SR
    sig = np.sin(ph) + 0.14 * np.sin(2 * ph + 0.5) + 0.05 * np.sin(3 * ph + 1.1)
    sig += 0.02 * np.diff(rng.standard_normal(n), prepend=0)
    env = np.ones(n)
    a, r = int(0.035 * SR), int(0.14 * SR)
    env[:a] = np.linspace(0, 1, a) ** 1.5
    k0 = int(dur * SR)
    env[k0:] = np.exp(-np.arange(n - k0) / (0.05 * SR))
    return sig * env

def synth_ks(pitch, dur, t60, bright):
    f0 = 440.0 * 2 ** ((pitch - 69) / 12)
    n = int((dur + 1.4) * SR)
    out = np.zeros(n)
    per = int(round(SR / f0))
    decay = 10 ** (-3.0 / (t60 * f0))
    for cents in (4.0, -4.0):
        buf = rng.standard_normal(int(round(SR / (f0 * 2 ** (cents / 1200)))))
        p2 = len(buf)
        idx = 0
        seg = np.zeros(n)
        while idx < n:
            m = min(p2, n - idx)
            seg[idx:idx + m] = buf[:m]
            buf = decay * (bright * buf + (1 - bright) * 0.5 * (buf + np.roll(buf, -1)))
            idx += p2
        out += seg
    out *= np.exp(-np.arange(n) / (1.1 * SR))
    out[:int(0.003 * SR)] += 0.25 * rng.standard_normal(int(0.003 * SR))
    return out

KS_PARAMS = {'zheng': (1.8, 0.15), 'qin': (2.6, 0.05)}

def render(voice, gain):
    kind = CONFIG['instruments'][voice]
    out = np.zeros(total_len, dtype=np.float64)
    notes = NOTES[voice]
    for idx, (p, dur_e, start) in enumerate(notes):
        lo, hi = LEAD[voice]
        g = gain * (1.14 if lo <= start < hi else 1.0)
        dur = dur_e * EIGHTH
        if start + dur_e in PHRASE_ENDS:
            dur *= 0.92                      # 乐句末气口
        if kind == 'organ':
            sig = synth_organ(p, dur, start, voice == 'B')
        elif kind == 'dizi':
            sig = synth_dizi(p, dur, lead=(lo <= start < hi))
        else:
            if idx > 0:
                pp = notes[idx - 1][0]
                if pp == p:
                    dur *= 0.82              # 同音重拨分开
                elif abs(IDX[pp] - IDX[p]) >= 3:
                    dur *= 0.92              # 跳进稍断
            sig = synth_ks(p, dur, *KS_PARAMS[kind])
        i0 = int(start * EIGHTH * SR)
        i1 = min(i0 + len(sig), total_len)
        out[i0:i1] += sig[: i1 - i0] * g
    return out

mono = sum(render(v, CONFIG['gains'][v]) for v in VOICES)
print('合成完成')

def reverb_ir(seed):
    rv = CONFIG['reverb']
    r = np.random.default_rng(seed)
    n = int(rv['seconds'] * SR)
    t = np.arange(n) / SR
    ir = r.standard_normal(n) * np.exp(-t / rv['tau'])
    ir /= np.sqrt(np.sum(ir ** 2))
    return np.concatenate([np.zeros(int(rv['predelay'] * SR)), ir])

def fft_convolve(x, h):
    n = len(x) + len(h) - 1
    nfft = 1 << (n - 1).bit_length()
    return np.fft.irfft(np.fft.rfft(x, nfft) * np.fft.rfft(h, nfft), nfft)[:len(x)]

wet = CONFIG['reverb']['wet']
outL = mono * (1 - wet * 0.9) + fft_convolve(mono, reverb_ir(11)) * wet
outR = mono * (1 - wet * 0.9) + fft_convolve(mono, reverb_ir(29)) * wet

import wave
peak = max(np.max(np.abs(outL)), np.max(np.abs(outR)))
prefix = CONFIG['out_prefix']
with wave.open(prefix + '.wav', 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    inter = np.empty(total_len * 2, dtype=np.int16)
    inter[0::2] = np.clip(outL / peak * 0.85 * 32767, -32768, 32767).astype(np.int16)
    inter[1::2] = np.clip(outR / peak * 0.85 * 32767, -32768, 32767).astype(np.int16)
    w.writeframes(inter.tobytes())
print(f'WAV 完成：{total_len/SR:.1f}s')

from midiutil import MIDIFile
mf = MIDIFile(3)
for ti, v in enumerate(VOICES):
    mf.addTempo(ti, 0, CONFIG['qpm'])
    mf.addProgramChange(ti, ti, 0, CONFIG['midi_prog'][v])
    for p, dur_e, start in NOTES[v]:
        mf.addNote(ti, ti, p, start * 0.5, dur_e * 0.5, 90)
with open(prefix + '.mid', 'wb') as f:
    mf.writeFile(f)
print('MIDI 完成')

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

fig, ax = plt.subplots(figsize=(17, 6), dpi=130)
colors = {'S': '#c0392b', 'A': '#27ae60', 'B': '#2980b9'}
for v in VOICES:
    for p, dur_e, start in NOTES[v]:
        ax.plot([start, start + dur_e], [p, p], color=colors[v], lw=6,
                solid_capstyle='butt', alpha=0.9)
for m in range(0, 33):
    ax.axvline(m * 8, color='gray', lw=0.35, alpha=0.5)
for e in range(N_POS):
    act = [(TL[v][e], v) for v in VOICES if TL[v][e] is not None]
    for x, v in act:
        if any(v != w and interval(x, y) not in CON for y, w in act):
            col = '#f39c12' if pos_class(e) in ('strong', 'mid') else '#95a5a6'
            ax.plot([e + 0.5], [x], marker='o', ms=3, color=col, zorder=5)
for x, label in [(0, 'Subject'), (64, 'Answer + countersubject'),
                 (128, 'Episode'), (160, 'Subject (bass)'),
                 (224, 'To cadence'), (240, 'Cadence')]:
    ax.text(x + 0.4, 82.5, label, fontsize=9, color='#555')
ax.set_xlim(0, 256)
ax.set_ylim(min(SCALE) - 3, max(SCALE) + 4)
ax.set_xlabel('eighth note')
ax.set_title(CONFIG['title'])
ax.legend(handles=[Line2D([0], [0], color=colors[v], lw=6, label=v) for v in VOICES])
fig.tight_layout()
fig.savefig(prefix + '.png')
print('谱面完成')
