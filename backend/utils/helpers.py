def estimate_token_count(text: str) -> int:
    """Approximate token count (split on whitespace, multiply by 1.3)."""
    if not text:
        return 0
    return int(len(text.split()) * 1.3)

def format_summary(summary: dict) -> str:
    """Convert summary JSON to a readable string for prompt injection."""
    import json
    # If it's a simple dict, dump it. If we want specific formatting we can add it here.
    # For now, JSON dump is robust.
    return json.dumps(summary, indent=2)

def format_graph(edges: list) -> str:
    """Convert graph edges to a readable string like 'Entity A --[USES]--> Entity B (conf: 0.9)'."""
    lines = []
    for edge in edges:
        # edge is a dict from api_models/db_models or raw dict
        # Assuming dict structure from the models
        source = edge.get("from_entity", "Unknown")
        target = edge.get("to_entity", "Unknown")
        rel = edge.get("relation_type", "RELATED_TO")
        conf = edge.get("confidence", 1.0)
        lines.append(f"{source} --[{rel}]--> {target} (conf: {conf})")
    return "\n".join(lines)

def format_messages(messages: list) -> str:
    """Convert message list to '[user]: ...\n[assistant]: ...\n' format."""
    lines = []
    for msg in messages:
        # msg can be a Message object or dict. Handle both.
        role = getattr(msg, "role", None) or msg.get("role")
        content = getattr(msg, "content", None) or msg.get("content")
        lines.append(f"[{role}]: {content}")
    return "\n".join(lines)

def extract_key_points(summary: dict) -> str:
    """From a summary dict, extract only facts and decisions as a short compressed string."""
    # Assuming standard summary structure with FACTS and DECISIONS keys
    lines = []
    if "FACTS" in summary and isinstance(summary["FACTS"], list):
        for fact in summary["FACTS"]:
            val = fact.get("fact", "") if isinstance(fact, dict) else str(fact)
            lines.append(f"- {val}")
    if "DECISIONS" in summary and isinstance(summary["DECISIONS"], list):
        for dec in summary["DECISIONS"]:
            val = dec.get("decision", "") if isinstance(dec, dict) else str(dec)
            lines.append(f"- [DECISION] {val}")
            
    if not lines:
        import json
        return json.dumps(summary)
        
    return "\n".join(lines)
