# LASAGNA2354 (ラザニア2354) 最小ブレッドボード実験（XIAO RP2350 + 74系のみ、カートリッジ無し・ロジアナ無し）

目的: Rev.B の要件決め — ALE最小パルス幅、ラッチ伝搬遅延、デコーダーグリッチ、外付けプル抵抗でのバスターンアラウンド。
測定は XIAO 自身が行う（PIO が全GPIOを sys clk 毎にスナップショット、1 clk = 5.81 ns @172 MHz）。

## 部品（秋月電子、2026-10-13 にページ取得・税込価格確認）
必須（すべて DIP、変換基板不要）
- [8回路Dラッチ TC74HC573AP(F)](https://akizukidenshi.com/catalog/g/g131763/) 160円 — DIP。'573/'574/LCX574 はピン配置同一（D=2-9, Q=19-12, /OE=1, LE/CLK=11）なので差し替え可。秋月に DIP の 74HC574/74AC574/74HC374 は検索で見つからず
- [3to8デコーダー TC74HC138AP](https://akizukidenshi.com/catalog/g/g110013/) 40円 — 3.3V 動作は HC の規格内（ACT138 は 4.5–5.5V 規格なので今回は HC を推奨）
- [集合抵抗 8素子 10kΩ](https://akizukidenshi.com/catalog/g/g111910/) 40円 — D0-3 の外付けプル（共通ピンを GND→プルダウン / 3V3→プルアップ）
- [積層セラミック 0.1µF (10個入)](https://akizukidenshi.com/catalog/g/g113582/) 100円 — 各IC VCC-GND
小計 340円

推奨オプション（本番相当の高速 3.3V ラッチを測る場合）
- [74LCX574FT](https://akizukidenshi.com/catalog/g/g114114/) 100円 — TSSOP20、エッジトリガ
- [SSOP20/SOP20 DIP変換基板](https://akizukidenshi.com/catalog/g/g110497/) 80円 — 0.65mm 面で LCX574FT を実装
- [ピンヘッダー 1×40](https://akizukidenshi.com/catalog/g/g100167/) 35円 — 変換基板用
小計 215円 → 合計 555円

未所有なら
- [ブレッドボード EIC-801](https://akizukidenshi.com/catalog/g/g100315/) 450円
- [ジャンパーワイヤ 14種×10本](https://akizukidenshi.com/catalog/g/g100288/) 930円
全部入り 1,935円

不要: 74HC165/595（今回の要件測定には不使用）。

## XIAO RP2350 ピン（Seeed 公式ピン配置 / Pico SDK seeed_xiao_rp2350.h と整合）
端面 11 本のみ使用（裏面パッド D11–D18 は使わない）。GP0–GP7 が連続で全部端面に出ているので PIO の out/in に好都合。

| 信号 | GPIO | XIAO | 接続先 |
|---|---|---|---|
| D0 (out) | GP0 | D6 | 573 pin2 (D0), 138 pin1 (A), RA 素子1 |
| D1 (out) | GP1 | D7 | 573 pin3 (D1), 138 pin2 (B), RA 素子2 |
| D2 (out) | GP2 | D8 | 573 pin4 (D2), 138 pin3 (C), RA 素子3 |
| D3 (out) | GP3 | D10 | 573 pin5 (D3), RA 素子4 |
| Q0 (in) | GP4 | D9 | 573 pin19 (Q0) |
| Q1 (in) | GP5 | D3 | 573 pin18 (Q1) |
| Q2 (in) | GP6 | D4 | 573 pin17 (Q2) |
| Q3 (in) | GP7 | D5 | 573 pin16 (Q3) |
| ALE (out) | GP26 | D0 | 573 pin11 (LE) / 574 pin11 (CLK) |
| /Y0 (in) | GP27 | D1 | 138 pin15 |
| /Y3 (in) | GP28 | D2 | 138 pin12 |
| 3V3 | — | 3V3 | 573 pin20, 138 pin16, 138 pin6 (G1) |
| GND | — | GND | 573 pin10, 573 pin1 (/OE), 573 未使用D (6-9), 138 pin8, 4 (/G2A), 5 (/G2B) |

集合抵抗: 共通ピン（ドット）を GND（プルダウン）。T5 の逆方向は共通ピンを 3V3 に差し替えて再実行。0.1µF を各 IC の 20-10 / 16-8 間に。
5V は使わない（GP26-28 は ADC ピンで 5V トレラントではない）。

```
 XIAO RP2350                74HC573 (or LCX574)          74HC138
 D6 GP0 ──┬──────────────── 2 D0      Q0 19 ─── D9 GP4
 D7 GP1 ──┼─┬────────────── 3 D1      Q1 18 ─── D3 GP5
 D8 GP2 ──┼─┼─┬──────────── 4 D2      Q2 17 ─── D4 GP6
 D10 GP3 ─┼─┼─┼─┬────────── 5 D3      Q3 16 ─── D5 GP7
 D0 GP26 ─┼─┼─┼─┼────────── 11 LE/CLK  1 /OE ── GND
          │ │ │ │                      
          │ │ │ └ RA10k ─┐   GP0→A(1) GP1→B(2) GP2→C(3)
          └─┴─┴── RA10k ─┴─ COM(GND)   /Y0(15) ─ D1 GP27
                                        /Y3(12) ─ D2 GP28
                                        G1(6)=3V3 /G2A(4) /G2B(5)=GND
```

## ファームウェア
`firmware/latch_bench_xiao/`（ビルド済: `/workspace/latch_bench_xiao.uf2`、172 MHz）。USB CDC に結果を出し `DONE` で終了、'r' で再実行。
- T0: D ピン自己リードバックでループ遅延 L（出力パッド→2段同期）を測り以降から差し引く
- T1: 配線検出（未配線なら Q はプルアップで 1111 → ラッチ試験スキップ）、573 透過型 / 574 エッジ型の自動判別
- T2: ALE↑→Q、D→Q（LE high）の伝搬遅延 min/avg/max [clk, ns]
- T3: ALE 幅 w=1..12 clk × ホールド 1..4 clk のスイープ、16パターン×200回の誤捕捉数と最小エラー無し幅
- T4: 138 全 56 遷移×100 回で非選択 /Y0,/Y3 の Low グリッチを検出 + A→/Y0 遅延
- T5: D0-3 を駆動→Hi-Z、外付けプルで反転するまでの clk（〜255 clk まで）。内部プルは不使用（E9）
- 未配線でも安全: 出力 2mA、全待ちにタイムアウト、必ず DONE

限界: 分解能 1 clk（5.8 ns）。1 clk 未満のグリッチは見逃し得る（多数回反復で確率的に検出）。sys clk を変えると分解能も変わる。
