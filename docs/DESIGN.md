## 2.2 TradeStateMachine — finite‑state specification  

| **State** | **Entry condition** | **Allowed transition(s)** | **Transition trigger** | **Action(s) on entry)** |
|-----------|--------------------|---------------------------|------------------------|------------------------|
| **Idle** | Bot started **or** previous position fully closed | `Scout` | *FactorScore* ≥ Θ₁ (≥ 3 core factors simultaneously true) | No orders – begin factor monitoring |
| **Scout** | Entered with **risk 0.10 R** probe order (size = 10 % of full risk) | `Confirm`, `ExitSL` | • 30 tick timer expired **and** FactorScore ≥ Θ₂<br>• Hard‑stop price hit | Place *OCO* order: hard stop = entry × 0.997 (‑0.3 %), soft limit = entry × 1.005 |
| **Confirm** | Scout still open **and** FactorScore ≥ Θ₂ within 30 ticks | `Hold`, `ExitSL` | • Full‑risk add order filled (another 0.25 R)<br>• Hard‑stop price hit | Add size; refresh OCO (new avg price, same % stop) |
| **Hold** | Full position active **and** FactorScore ≥ Θ₃ (≥ Θ₂‑δ) | `ExitTP`, `ExitSL`, `EndOfDay` | • Adaptive partial‑TP hit *(max(0.5 %, 0.7 × ATR))* → `ExitTP`<br>• Hard‑stop hit → `ExitSL`<br>• 14:30:00 KST → `EndOfDay` | Trail soft stop to *VWAP – 1 tick* every 20 ticks |
| **ExitTP** | Partial take‑profit executed (≈ 50 % size) | `Hold`, `ExitSL`, `EndOfDay` | • FactorScore recovers ≥ Θ₃ → back to `Hold`<br>• Hard‑stop of residual hit → `ExitSL`<br>• 14:30 KST → `EndOfDay` | Adjust risk‑budget & refresh trailing stop |
| **ExitSL** | Hard stop (‑0.4 % from avg) filled **OR** latency‑guard forced market‑out | `Idle` | — | Log loss, freeze same symbol for 5 min (*order cool‑down*) |
| **EndOfDay** | Any open position after 14:30:00 | `Idle` | All positions closed at market | Write EOD PnL row, disable new signals until next session |

**Key symbols**

* `R` : per‑trade risk budget (account × 0.4 %)  
* `FactorScore` = weighted sum of • Tick Imbalance • Net Futures Flow • Cash Flow • F‑S Gap • Quote Imbalance.  
* Θ₁ < Θ₂ < Θ₃ are configurable thresholds (e.g. 60 / 70 / 75 points).
