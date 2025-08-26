"""
Centralized prompt definitions and response schema for economy JSON generation.
"""

from typing import Dict, List, Optional


def gemini_phase1_prompt(game_info: str, game_title: str) -> str:
    return f"""You are an expert video game economist researching "{game_title}".

Based on this information:
{game_info}

Phase 1 — Systems Inventory:
1) Game overview: genre, core mechanics, audience, platforms, business model
2) Currencies: premium, soft, event-specific; how earned/spent
3) Resources: materials, items, consumables; rarity when relevant
4) Progression: XP, levels, ranks, mastery, account-level
5) Time gates: energy, tickets, cooldowns, daily/weekly locks
6) Activities: core play, secondary (crafting, trading), meta (collections, achievements), monetized (passes, subs)

Be specific and comprehensive to inform economy flow mapping."""


def gemini_phase2_prompt(phase1: str, game_title: str) -> str:
    return f"""Phase 2 — Resource Flows for {game_title}

Using Phase 1 findings:
{phase1}

Map input/output for key activities:
- Inputs (costs, tickets, energy)
- Outputs (currencies, rewards, materials)
- Permanent gains (XP, unlocks, reputation)
- Conversion mechanisms (currency exchanges, crafting, upgrades)
- Daily/progression/monetization/social loops
- Resource sinks (temporary/permanent/competitive/social)

Be explicit about flows and conversion points."""


def gemini_phase3_prompt(phase2: str, game_title: str) -> str:
    return f"""Phase 3 — Optimization and Final Goods for {game_title}

Using Phase 2 flows:
{phase2}

Identify:
- Optimization paths (F2P, low-spend, whale; time-rich vs money-rich)
- Bottlenecks (progress, resource, time, social)
- Final goods (ultimate achievements, prestige, completion, social goals)
- Value props (progress feel, monetization drivers, long-term retention)

Synthesize what creates lasting value and drives spending."""


def gemini_synthesis_prompt(phase1: str, phase2: str, phase3: str, game_title: str) -> str:
    return f"""Synthesize research into a structured economy model for {game_title}.

Phase 1 (Systems):\n{phase1[:2000]}...\n\nPhase 2 (Flows):\n{phase2[:2000]}...\n\nPhase 3 (Optimization/Goals):\n{phase3[:2000]}...

Deliver a clear economy model with:
1) Primary inputs (time, money, attention)
2) Core activity nodes (consume → produce → accumulate)
3) Resource classifications (sources, sinks, values)
4) Flow connections between activities
5) Final goods (ultimate goals)
6) Optional groupings (subsections)

Keep it precise and consistent to convert to JSON.
"""


def final_json_instructions_prompt(game_title: str) -> str:
    return f"""You must now output ONLY a single valid JSON object for "{game_title}".

Top-level keys (exact): "inputs", "nodes", "edges". Optional: "subsections".

Strict rules:
- No markdown or prose. JSON only.
- No trailing commas.
- Never leave blanks: use [] for empty arrays.
- All ids are snake_case: lowercase letters, digits, underscores only.
- Every edge references an existing id.

Classification rules (very important):
- Sources: Spendable or transferrable resources that are ADDED to inventory and can be used/converted elsewhere (currencies, materials, items, tickets). Examples: "Gold", "Wood", "Seeds", "Cooking Ingredients".
- Sinks: Resources that are SUBTRACTED from inventory or consumed to perform actions (currencies, materials, tickets, energy/time-gated costs). Examples: "Energy", "Gold", "Crafting Materials", "Seeds".
- Values: Non-spendable progression metrics that ONLY ACCUMULATE (store-of-progress). These cannot be spent. Examples: "XP", "Account Level", "Reputation/Renown", "Mastery", "Story Progress", "Relationship Level", "Prestige Rank".
- Final goods: Player-facing experiential end states or design pillars that the player strives for (not raw resources). Examples: "Decorated Home", "Maxed Skills", "Completed Quests", "Strong Relationships", "Legendary Collection", "Prestige/Leaderboard Rank".

Important exclusions:
- Never place value-like metrics (XP, Level, Rank, Reputation/Renown, Mastery, Progression) in "sources" or "sinks". They belong in "values" only.
- Never place spendable/consumable resources (materials, items, currencies, components, tickets, ingredients) in "values". They belong in "sources"/"sinks".
- Do not mark raw resources or crafted items as final goods. Final goods should represent high-level experiential outcomes or design pillars.

Edge constraints:
- Only allow edges of these forms:
  - inputs ("time"/"money") → activity nodes
  - activity nodes → activity nodes or final goods
- Do NOT create edges to resource nouns; represent resource flows only via sources/sinks arrays.

Subsections discipline:
- Build subsections after nodes/inputs are finalized.
- Only include nodeIds that exist; silently drop any that do not. If a subsection becomes empty, omit it.

Id naming:
- id must be snake_case derived from the label (strip any leading "To ", lowercase, replace spaces/specials with underscores).

Input ids and labels:
- Use input ids exactly: "time" and/or "money" when present
- Use input labels exactly: "Time" and/or "Money"

Node labels style:
- Use a verb-first, human-readable label without underscores
- Format as: "To <Verb Phrase>" (e.g., "To Gather", "To Cook", "To Quest & Socialize")
- Do NOT include "Spend Time" or "Spend Money" in node labels (inputs and edges represent this)
- Use proper capitalization for acronyms like "XP"

Resource naming in `sources`, `sinks`, `values`:
- No underscores; replace with spaces and capitalize words (e.g., "raw_materials" → "Raw Materials")
- Capitalize first letter of each word; use "XP" exactly when applicable

Schema summary:
- inputs[]: {{id, label, kind == "initial_sink_node"}}
- nodes[]: {{id, label, sources[], sinks[], values[], kind? == "final_good"}}
- edges[]: [from_id, to_id]
- subsections[]?: {{id, label, nodeIds[], color?}}

Self-check before finalizing:
- Construct the set S of all ids from inputs and nodes
- Verify each edge [a,b] has a in S and b in S; if any mismatch, rename or adjust ids to ensure consistency
- Ensure no duplicate edges
- Ensure every final_good node has at least one incoming edge
 
Final goods policy:
- Final goods are ultimate outcomes (e.g., Decorated Home, Maxed Skills, Completed Quests, Strong Relationships, Community Contribution, Prestige Rank, Story Completion, Legendary Collection)
- Do NOT mark raw resources or intermediate outputs as final goods. Avoid marking as final_good:
  - Materials, Components, Ingredients, Resources, Fish categories, Dishes, Recipes
  - Gold, Utility, Buffs, Energy, Health, Quest Items, Collectibles, Desired Items, Renown
  - Any XP (e.g., Crafting XP, Cooking XP)
"""

def detail_requirements(depth: int = 0, categories: Optional[List[str]] = None) -> str:
    cats = categories or [
        "Gathering/Foraging/Mining", "Farming/Gardening", "Fishing", "Cooking", "Crafting/Refining",
        "Questing/Social", "Trading/Exchange", "Housing/Decoration"
    ]
    if depth and depth > 0:
        lines = [
            f"Add granularity: target at least {max(1, depth)} distinct nodes per applicable category:",
        ]
        for c in cats:
            lines.append(f"- {c}")
        lines.append("Ensure each node clearly states sinks, sources, and values.")
        return "\n" + "\n".join(lines)
    return ""

def repair_prompt(game_title: str, original_json_snippet: str, issues_text: str) -> str:
    return f"""You previously generated economy JSON for "{game_title}", but issues were found:

Problems:
{issues_text}

Original JSON (snippet):
{original_json_snippet}

Produce a corrected JSON that resolves all problems while following these strict rules:
- Keep top-level keys exactly: inputs, nodes, edges (optional: subsections)
- Preserve valid content, but fix ids, edges, and labels as needed
- Node labels: format as "To <Verb Phrase>" for activities; final_goods keep plain labels
- sources/sinks/values terms: no underscores, capitalized words; "XP" exactly uppercase
- Self-check edges: every edge ids must exist; remove duplicates; ensure every final_good has >=1 incoming edge
- Output ONLY the JSON object, no extra text.
"""


def economy_json_response_schema() -> Dict:
    """JSON Schema-like dict for Gemini structured output.

    Enforces the shape and basic constraints. Gemini will try to conform.
    """
    return {
        "type": "object",
        "properties": {
            "inputs": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "label": {"type": "string"},
                        "kind": {"type": "string", "enum": ["initial_sink_node"]},
                    },
                    "required": ["id", "label", "kind"],
                }
            },
            "nodes": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "label": {"type": "string"},
                        "sources": {"type": "array", "items": {"type": "string"}},
                        "sinks": {"type": "array", "items": {"type": "string"}},
                        "values": {"type": "array", "items": {"type": "string"}},
                        "kind": {"type": "string", "enum": ["final_good"]},
                    },
                    "required": ["id", "label", "sources", "sinks", "values"],
                }
            },
            "edges": {
                "type": "array",
                "items": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            },
            "subsections": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "label": {"type": "string"},
                        "nodeIds": {"type": "array", "items": {"type": "string"}},
                        "color": {"type": "string"}
                    },
                    "required": ["id", "label", "nodeIds"],
                }
            }
        },
        "required": ["inputs", "nodes", "edges"],
    }


def system_instruction_text() -> str:
    return (
        "You are an expert game economy analyst. Follow strict classification: "
        "Sources=spendable resources added; Sinks=consumed resources; Values=non-spendable progression (XP, levels, rank, renown, mastery, story progress); "
        "Final goods=player-facing experiential outcomes (design pillars). Never put XP/levels/etc. in sources/sinks; never put resources in values; never mark resources or crafted items as final goods. "
        "Edges only: inputs→activities, activities→activities or final_goods. No edges to resource nouns; use sources/sinks arrays instead. "
        "Node labels: 'To <Verb Phrase>' for activities; final_goods keep plain labels. id must be snake_case from label (strip leading 'To '). "
        "Subsections must reference existing ids only; drop unknowns or omit subsections if empty."
    )

def good_bad_examples() -> str:
    good = {
        "inputs": [{"id":"time","label":"Time","kind":"initial_sink_node"}],
        "nodes": [
            {"id":"to_quest","label":"To Quest","sources":["Gold","Quest Items"],"sinks":["Time"],"values":["XP"]},
            {"id":"completed_quests","label":"Completed Quests","sources":[],"sinks":[],"values":[],"kind":"final_good"}
        ],
        "edges": [["time","to_quest"],["to_quest","completed_quests"]]
    }
    bad = {
        "inputs": [{"id":"time","label":"Time","kind":"initial_sink_node"}],
        "nodes": [
            {"id":"quest","label":"To Quest","sources":["XP","Gold"],"sinks":["Time"],"values":[]},
            {"id":"gold","label":"Gold","sources":[],"sinks":[],"values":[],"kind":"final_good"}
        ],
        "edges": [["time","quest"],["quest","gold"]]
    }
    return (
        "Good example (correct classification and edges):\n" + str(good) +
        "\nBad example (wrong: XP in sources; resource as final_good):\n" + str(bad) +
        "\nAlways correct the bad patterns to match the good patterns."
    )

def classification_stage_prompt(synthesis: str) -> str:
    return (
        "Create a concise classification table of candidate nodes with columns: id, label, sinks[], sources[], values[], kind(optional=final_good).\n"
        "Rules: Do NOT create nodes for resource nouns (materials/items/currency/etc.); those belong only in sources/sinks/values only. "
        "Ensure values only contain progression metrics (XP, levels, rank, renown, mastery, story progress). "
        "Return the table as plain text, then proceed to JSON in the next step.\n\n"
        f"Synthesis notes:\n{synthesis[:1500]}...\n"
    )
