# -*- coding: utf-8 -*-
"""用与谱面完全相同的数据合成《致爱丽丝》音频（钢琴音色近似），输出 WAV"""
import os
import sys
import math
import wave
import struct

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import jianpu_renderer as B  # 复用谱面数据，保证音频与谱面一致；改模板文件名时同步改这里

SR = 44100
SIXTEENTH = None

# 3/8，♩. = 52  =>  每小节 = 60/52 秒
MEASURE = 60.0 / 52.0
BEAT = MEASURE / 3.0          # 一个八分音符

SEMI = {'1': 0, '2': 2, '3': 4, '4': 5, '5': 7, '6': 9, '7': 11}


def midi(n):
    m = 60 + SEMI[n['d']] + 12 * n['oct']
    if n['acc'] == '#':
        m += 1
    if n['acc'] == 'b':
        m -= 1
    return m


def freq(m):
    return 440.0 * (2 ** ((m - 69) / 12.0))


ORDER = [(0, B.PICK), (1, B.M1), (2, B.M2), (3, B.M3), (4, B.M4), (5, B.M5),
         (6, B.M6), (7, B.M7), (8, B.M8), (9, B.M9), (10, B.M10), (11, B.M11),
         (12, B.M12), (13, B.M13), (14, B.M14), (15, B.M15), (16, B.M16),
         (17, B.M17), (18, B.M18), (19, B.M19), (20, B.M20), (21, B.M21),
         (22, B.M22), (23, B.M23), (24, B.M24)]


def build_events():
    ev = []          # (start, dur, midi, vel)
    last = None
    for idx, (mid_num, notes) in enumerate(ORDER):
        t0 = idx * MEASURE
        # 左手：每小节第一个拍一个根音
        lh = B.LH.get(mid_num, '')
        if lh:
            digit = lh[0]
            low = 1 if '̣' in lh else 0
            m = 60 + SEMI[digit] - 12 * (1 + low)
            ev.append((t0, MEASURE * 0.96, m, 0.34))
        for j, slot in enumerate(notes):
            sb = t0 + j * BEAT
            if len(slot) == 1 and slot[0]['d'] in ('0', '-'):
                if slot[0]['d'] == '-' and last is not None:
                    s, d, m, v = ev[last]
                    ev[last] = (s, d + BEAT, m, v)
                continue
            if len(slot) == 2:                       # 两个十六分
                for k, n in enumerate(slot):
                    ev.append((sb + k * BEAT / 2, BEAT / 2 * 0.94, midi(n), 0.8))
                    last = len(ev) - 1
            else:
                n = slot[0]
                ev.append((sb, BEAT * 0.94, midi(n), 0.8))
                last = len(ev) - 1
    return ev


def render(events, total):
    n = int(total * SR) + SR // 2
    buf = [0.0] * n
    for start, dur, m, vel in events:
        f = freq(m)
        s0 = int(start * SR)
        length = int((dur + 0.18) * SR)
        # 每个泛音单独衰减，高次泛音衰减更快，接近钢琴
        partials = [(1, 1.00, 2.2), (2, 0.42, 3.4), (3, 0.20, 4.8),
                    (4, 0.10, 6.2), (5, 0.05, 7.6), (6, 0.028, 9.0)]
        amp = vel * 0.24
        for i in range(length):
            t = i / SR
            if s0 + i >= n:
                break
            # 起音 5ms，缓起避免爆音
            atk = min(1.0, t / 0.005)
            v = 0.0
            for k, a, dcy in partials:
                if f * k > SR / 2.2:
                    continue
                v += a * math.exp(-t * dcy) * math.sin(2 * math.pi * f * k * t)
            # 击弦噪声：最初 30ms
            if t < 0.03:
                v += (0.06 * (1 - t / 0.03)) * math.sin(2 * math.pi * f * 7.3 * t)
            buf[s0 + i] += v * amp * atk
    # 轻混响：三次衰减延迟
    rev = [0.0] * n
    for delay, gain in ((0.031, 0.30), (0.067, 0.18), (0.113, 0.10)):
        d = int(delay * SR)
        for i in range(n - d):
            rev[i + d] += buf[i] * gain
    out = [buf[i] + rev[i] * 0.55 for i in range(n)]
    peak = max(max(out), -min(out)) or 1.0
    g = 0.89 / peak
    return out, g


def write_wav(path, data, gain):
    with wave.open(path, 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        frames = bytearray()
        for x in data:
            v = int(max(-1.0, min(1.0, x * gain)) * 32767)
            frames += struct.pack('<h', v)
        w.writeframes(bytes(frames))


if __name__ == '__main__':
    events = build_events()
    total = len(ORDER) * MEASURE + 1.6
    print('notes', len(events), 'dur', round(total, 2), 's')
    data, g = render(events, total)
    out = os.environ.get('AUDIO_OUT', os.path.join(HERE, 'demo.wav'))
    write_wav(out, data, g)
    print(out, round(os.path.getsize(out) / 1024 / 1024, 2), 'MB')
