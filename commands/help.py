"""Help/menu command — Hinatav2-style module, lists every loaded command by
category (modern + legacy alike, since they all end up in the registry)."""

CONFIG = {
    "name": "help",
    "aliases": ["menu", "commands"],
    "category": "info",
    "cooldown": 3,
    "role": 0,
    "no_prefix": True,
    "no_prefix_role": 0,
    "description": {"en": "Show all available commands or details for one"},
    "usage": {"en": "{p}help [command]"},
}


def on_start(ctx):
    prefix = ctx["config"].get("prefix", ".")
    args = ctx.get("args", [])
    registry = ctx["registry"]

    if args:
        command = registry.resolve(args[0])
        if not command:
            return f'❌ Command "{args[0]}" not found.'
        c = command.config
        desc = (c.get("description") or {}).get("en", "—")
        usage = ((c.get("usage") or {}).get("en", f"{prefix}{c['name']}")).replace("{p}", prefix)
        return (
            "☠️ COMMAND INFO ☠️\n\n"
            f"➥ Name: {c['name']}\n"
            f"➥ Category: {c.get('category', 'Uncategorized')}\n"
            f"➥ Description: {desc}\n"
            f"➥ Aliases: {', '.join(c.get('aliases', [])) or 'None'}\n"
            f"➥ Usage: {usage}\n"
            f"➥ Permission: {c.get('role', 0)}"
        )

    by_category = {}
    for command in registry.commands.values():
        category = (command.config.get("category") or "others").lower()
        by_category.setdefault(category, []).append(command.config["name"])

    bot_name = str(ctx["config"].get("botName", "InstaBOT")).upper()
    lines = [f"━━━☠️ {bot_name} ☠️━━━"]
    for category in sorted(by_category):
        lines.append(f"\n╭──『 {category.upper()} 』")
        names = sorted(by_category[category])
        lines.append("  ".join(f"{prefix}{n}" for n in names))
        lines.append("╰────────────◊")
    lines.append(f"\n➥ Use: {prefix}help <command> for details")
    return "\n".join(lines)
