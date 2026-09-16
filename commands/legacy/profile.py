def get_target_profile(args, ctx):
    cl = ctx["client"]

    try:
        # Reply করা user থাকলে তার ID নাও
        target_id = ctx.get("target_user_id")

        # Reply না থাকলে command sender-এর ID
        if not target_id:
            target_id = ctx.get("user_id")

        user = cl.user_info(target_id)

        username = getattr(user, "username", "Unknown")
        full_name = getattr(user, "full_name", "Unknown")
        user_id = getattr(user, "pk", target_id)
        followers = getattr(user, "follower_count", 0)
        following = getattr(user, "following_count", 0)
        posts = getattr(user, "media_count", 0)
        bio = getattr(user, "biography", "") or "No bio"
        private = getattr(user, "is_private", False)
        verified = getattr(user, "is_verified", False)

        return (
            "👤 INSTAGRAM PROFILE\n"
            "━━━━━━━━━━━━━━━━━━\n"
            f"👤 Name: {full_name}\n"
            f"📛 Username: @{username}\n"
            f"🆔 User ID: {user_id}\n"
            f"👥 Followers: {followers}\n"
            f"➡️ Following: {following}\n"
            f"📸 Posts: {posts}\n"
            f"🔒 Private: {'Yes' if private else 'No'}\n"
            f"✅ Verified: {'Yes' if verified else 'No'}\n"
            f"📝 Bio: {bio}\n"
            "━━━━━━━━━━━━━━━━━━"
        )

    except Exception as e:
        print(f"PROFILE ERROR: {e}", flush=True)
        return "❌ Profile information পাওয়া যায়নি."


# এই ভ্যারিয়েবলটা মিসিং থাকার কারণেই Render-এ ImportError আসছিল
PROFILE_COMMANDS = {
    "info": get_target_profile,
    "profile": get_target_profile,
    "uid": get_target_profile,
    "whois": get_target_profile,
}
