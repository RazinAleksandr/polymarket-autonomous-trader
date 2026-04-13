# TradingAgents Integration Plan

How to integrate the best parts of TradingAgents into polymarket-trader.

Date: 2026-04-12  
Source: `/home/trader/TradingAgents/`  
Target: `/home/trader/polymarket-trader/`

---

## What to Integrate (3 components)

### 1. Bull/Bear Structured Debate — HIGH PRIORITY

**Problem it solves:** Phase C currently runs a single Claude session that researches bull evidence, then bear evidence, then synthesizes. This has confirmation bias risk — once the agent forms a view during bull research, the bear research is half-hearted. The $301 Iran ceasefire loss is a textbook example: the agent was committed to "status quo wins" and barely considered the Hormuz deadline pressure.

**What TradingAgents does:** Two separate LLM agents debate. Bull researcher advocates for YES with evidence. Bear researcher explicitly counters bull's specific claims. They alternate for configurable rounds. A synthesis agent reads the full debate and commits to a probability.

**Source files:**
- `TradingAgents/tradingagents/agents/researchers/bull_researcher.py` — bull advocate prompt
- `TradingAgents/tradingagents/agents/researchers/bear_researcher.py` — bear advocate prompt
- `TradingAgents/tradingagents/agents/researchers/research_manager.py` — synthesis agent
- `TradingAgents/tradingagents/graph/conditional_logic.py` — debate round control (`count >= 2 * max_debate_rounds`)

**Implementation:**
- Create `lib/debate.py` with `run_bull_case()`, `run_bear_case()`, `synthesize_debate()` functions
- Adapt prompts for prediction markets: replace stock language ("company growth," "competitive moat") with market language ("resolution criteria," "base rates," "event probability")
- Refactor Phase C in `.claude/CLAUDE.md`:
  - Current: "search bull evidence → search bear evidence → estimate probability"
  - New: "bull agent argues YES with web search → bear agent reads bull's argument and counters with web search → synthesizer reads full debate and outputs probability"
- Default 1 round (2 turns) — same as TradingAgents default
- Save full debate text to `state/cycles/{cycle_id}/debate_{market_id}.md` for audit
- Synthesizer outputs existing schema: `{ estimated_prob, confidence, edge, reasoning }`

**Key prompt adaptations needed:**
- Bull: "You are arguing that this market should resolve YES. Research evidence supporting YES. Be specific about resolution criteria. Cite sources."
- Bear: "You have read the bull case above. Counter each specific claim with evidence. Research what could go wrong. Check base rates for similar events."
- Synthesizer: "Read the full debate. Estimate the true probability. Do not split the difference — commit to a number. Apply calibration corrections if available. Output structured JSON."

**Code reusability from TradingAgents:** ~70%. Copy prompt structure, replace domain-specific language.

---

### 2. BM25 Memory System — HIGH PRIORITY

**Problem it solves:** The agent starts every cycle reading the last 3 reports and `strategy.md` — but when analyzing a new geopolitics market, it has no way to recall what went wrong on a similar geopolitics market 20 cycles ago. Golden rules are general ("cap at 90%") but don't surface situation-specific lessons like "last time we saw a Pakistan-mediated negotiation, ceasefire happened within 48 hours."

**What TradingAgents does:** BM25 (Best Matching 25) lexical retrieval — no API calls, no vector database, no embeddings. Fast keyword-based similarity matching. When analyzing a situation, it retrieves 2 past analyses of similar situations.

**Source files:**
- `TradingAgents/tradingagents/agents/utils/memory.py` — `FinancialSituationMemory` class (standalone, zero dependencies beyond `rank-bm25`)

**Implementation:**
- Copy `memory.py` directly — class is generic, no modifications needed
- Add `rank-bm25` to `requirements.txt`
- Create `lib/memory_manager.py`:
  - One BM25 memory instance per category: `politics_memory`, `sports_memory`, `crypto_memory`, etc.
  - `load_memories()` — read pickled indices from `state/memories/{category}.pkl` on startup
  - `save_memories()` — pickle indices after updates
  - `retrieve(category, market_question, n=2)` — get top 2 similar past situations
  - `store(category, situation_text, lesson_text)` — add new lesson after resolution
- Hook into Phase C: before debate starts, call `retrieve()` and inject past lessons into both bull and bear agent prompts
- Hook into Phase E: after resolution, call `store()` with the market situation + lesson learned
- Fallback: if no pickled memory exists (first run), start empty — BM25 handles zero-doc gracefully

**Storage layout:**
```
state/memories/
  politics.pkl
  sports.pkl
  crypto.pkl
  commodities.pkl
  entertainment.pkl
  finance.pkl
```

**Code reusability from TradingAgents:** 100%. Class is copy-paste ready.

---

### 3. Structured Reflection — MEDIUM PRIORITY

**Problem it solves:** Phase E learns from losses, but unstructured — Claude writes a report and maybe updates strategy.md. There's no systematic "what specifically went wrong in the bull/bear analysis?" step that produces a condensed lesson for future retrieval.

**What TradingAgents does:** After each trade, a reflector agent analyzes the decision: "Was the bull argument correct? Why or why not? What's the one-sentence lesson?" The condensed lesson is stored in BM25 memory for future retrieval.

**Source files:**
- `TradingAgents/tradingagents/graph/reflection.py` — `Reflector` class

**Implementation:**
- Add reflection step to Phase E after each resolution:
  1. Load the original debate text from `state/cycles/{cycle_id}/debate_{market_id}.md`
  2. Run reflection prompt: "The bull estimated X%, bear estimated Y%, synthesis was Z%. Actual outcome was WIN/LOSS. What specifically went wrong or right in the analysis? Extract one condensed lesson."
  3. Store (market_situation, lesson) in category BM25 memory
  4. Also append to `knowledge/market-types/{category}.md` (maintains current audit trail)
- This makes the memory system self-populating — every trade resolution teaches the next analysis

**Code reusability from TradingAgents:** ~60%. Copy reflection structure, rewrite prompts for prediction markets.

---

## What NOT to Integrate

**Risk Debate (aggressive/conservative/neutral agents):**
- Kelly criterion + hard position limits already handle risk quantitatively
- LLM debate over "be aggressive vs conservative" adds cost without value when you have 5% caps and quarter-Kelly
- Skip entirely

**LangGraph orchestration:**
- Overkill for single-agent architecture
- Current bash+cron+CLAUDE.md flow is simpler and works
- Only relevant if the project moves to multiple parallel Claude sessions
- Skip for now

**Data tools (yfinance, fundamentals, technicals):**
- These are for stocks. Prediction markets don't have balance sheets, P/E ratios, or MACD indicators
- Gamma API + CLOB + web search already covers Polymarket's data needs
- Skip entirely

**Signal extraction:**
- polymarket-trader already outputs structured JSON (estimated_prob, confidence, edge)
- TradingAgents' "extract BUY/SELL from text" is less precise than what we already have
- Skip entirely

**Multi-provider LLM support:**
- Interesting but low priority — Claude Code CLI is the runtime, not LangChain
- Would require rewriting the entire agent layer
- Skip for v2 scope

---

## Implementation Phases

### Phase 1: Bull/Bear Debate (highest impact)

**Files to create:**
- `lib/debate.py` — bull/bear/synthesizer functions
- `.claude/skills/debate-market.md` — skill doc for running structured debate

**Files to modify:**
- `.claude/CLAUDE.md` — Phase C instructions to use debate instead of sequential research
- `requirements.txt` — no new deps for debate itself

**Testing:**
- Run 5-10 markets through debate pipeline
- Compare probability estimates vs current single-agent approach
- Measure: does debate produce different (better-calibrated) estimates?

**Success criteria:**
- Debate produces structured output matching existing analyst schema
- Bull and bear agents cite real web sources
- Synthesizer doesn't just split the difference — commits to a number
- Debate text saved for audit

---

### Phase 2: BM25 Memory

**Files to create:**
- `lib/memory_manager.py` — category memory instances, load/save/retrieve/store
- Copy of `FinancialSituationMemory` class (from TradingAgents `memory.py`)

**Files to modify:**
- `requirements.txt` — add `rank-bm25>=0.2.2`
- `.claude/CLAUDE.md` — Phase C: retrieve memories before debate; Phase E: store lessons after resolution
- `.gitignore` — add `state/memories/*.pkl`

**Storage:**
- `state/memories/` directory with pickled BM25 indices per category

**Testing:**
- Seed 5-10 synthetic past lessons per category
- Verify retrieval returns relevant matches
- Verify persistence (pickle/unpickle cycle)

**Success criteria:**
- When analyzing a geopolitics market, agent retrieves relevant past geopolitics lessons
- Lessons from Phase E resolutions are automatically stored
- Memory survives across cycles (pickle persistence)

---

### Phase 3: Structured Reflection

**Files to create:**
- `lib/reflection.py` — reflection prompt runner

**Files to modify:**
- `.claude/CLAUDE.md` — Phase E: add reflection step after each resolution

**Dependencies:**
- Requires Phase 1 (debate text to reflect on)
- Requires Phase 2 (BM25 memory to store lessons in)

**Testing:**
- Manually resolve a test position
- Verify reflection produces a condensed lesson
- Verify lesson is stored in BM25 memory AND in market-types markdown

**Success criteria:**
- Each resolution produces exactly one condensed lesson
- Lesson is retrievable by BM25 for future similar markets

---

## Effort Estimates

| Phase | Scope | Depends On |
|-------|-------|------------|
| 1. Bull/Bear Debate | `lib/debate.py`, skill doc, CLAUDE.md refactor | Nothing |
| 2. BM25 Memory | `lib/memory_manager.py`, memory.py copy, CLAUDE.md hooks | Phase 1 (for debate text) |
| 3. Structured Reflection | `lib/reflection.py`, CLAUDE.md Phase E update | Phase 1 + Phase 2 |

Phases 1 and 2 can be developed in parallel (memory works without debate, debate works without memory). Phase 3 requires both.

---

## Measuring Success

**Before integration (baseline):**
- Current Brier score: 0.270 (4 trades)
- Current calibration error: +6.75pp overall
- Edge detection: mostly <4pp, rarely tradeable

**After integration (target):**
- Brier score improvement (lower is better)
- Fewer confirmation-bias errors (like Iran ceasefire)
- Past lessons surfaced during analysis (measurable: are retrieved memories relevant?)
- More nuanced probability estimates (not just "95% NO" — debate should produce more moderate estimates)

**How to measure:**
- Compare debate-produced estimates vs single-agent estimates on same markets
- Track Brier score before/after debate integration
- Count how many times retrieved memories influenced the final estimate
- Review debate quality in audit trail (`state/cycles/{cycle_id}/debate_*.md`)

---

## Risk Assessment

**Biggest risk:** Debate adds LLM cost (2-3x more tokens per market analyzed). Currently ~4 markets analyzed per cycle × 2h cycle = manageable. If debate doubles token usage per market, cost increases but stays within budget since most cycles analyze <10 markets.

**Mitigation:** Only run debate on markets that pass initial filters (Phase B). Don't debate all 50 scanned markets — only the 4-8 candidates that pass volume/resolution/price filters. This is already the current behavior.

**Second risk:** BM25 retrieval may return irrelevant matches early on (few stored lessons). Mitigation: start with empty memory, let it build naturally. After 10+ resolutions per category, retrieval quality improves. In the meantime, debate still works without memory.
